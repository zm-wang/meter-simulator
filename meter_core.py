#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IEC 62056-21 电表模拟器核心（不依赖 GUI）

- MeterEngine：协议状态机，支持 Mode A/B/C/D/E，并对主站报文做诊断（指出问题 + 给出正确写法）
- SerialLink / TcpServerLink / TcpClientLink / UdpLink：传输层
- 也可单独以命令行方式运行（无界面）：
    python3 meter_core.py --tcp-server 0.0.0.0:7000 --mode C
    python3 meter_core.py --serial /dev/ttyUSB0 --baud 300 --mode C --log 会话.txt

兼容 Python 3.7+，Windows / macOS / Linux。串口需要 pyserial。
"""

import argparse
import csv
import socket
import threading
import time
from dataclasses import dataclass, field, replace
from typing import List, Tuple

try:
    import serial
    from serial.tools import list_ports
except ImportError:  # 只用网络模式时可以不装 pyserial
    serial = None
    list_ports = None

from app_info import VERSION as __version__
from i18n import _, N_

SOH, STX, ETX, EOT, ACK, NAK = 0x01, 0x02, 0x03, 0x04, 0x06, 0x15
CR, LF = 0x0D, 0x0A
CRLF = b'\r\n'
ENC = 'latin-1'

BAUD_C = {'0': 300, '1': 600, '2': 1200, '3': 2400, '4': 4800, '5': 9600, '6': 19200}
BAUD_B = {'A': 600, 'B': 1200, 'C': 2400, 'D': 4800, 'E': 9600, 'F': 19200}

# 以下常量中的中文用 N_() 标记，显示时再用 _() 翻译成当前语言
MODE_INFO = {
    'A': N_('双向，不切换波特率：请求 → 标识 → 数据（全程同一波特率）'),
    'B': N_('请求 → 标识 → 按波特率字符(A~F)切速 → 数据，无 ACK'),
    'C': N_('最常用：请求 → 标识 → ACK 选项确认 → 切速 → 数据读取 / 编程模式'),
    'D': N_('单向推送：电表以 2400 bps 主动发送标识和数据，不响应请求'),
    'E': N_('同 Mode C 握手，标识带 \\2；ACK 选 2 后进入 HDLC（DLMS）二进制模式'),
}
# 每种模式的默认（初始波特率, 波特率字符）
MODE_DEFAULTS = {'A': (300, 'J'), 'B': (300, 'E'), 'C': (300, '5'), 'D': (2400, '3'), 'E': (300, '5')}
MODE_BAUD_CHARS = {
    'A': ['J', 'K', 'L', 'Z'],          # Mode A：任意可打印字符，但不能是 0~9、A~I、/、!
    'B': list('ABCDEF'),
    'C': list('0123456'),
    'D': ['3'],
    'E': list('0123456'),
}
STAGES = {
    'A': [('request', N_('请求')), ('ident', N_('标识')), ('data', N_('数据')), ('end', N_('结束'))],
    'B': [('request', N_('请求')), ('ident', N_('标识')), ('switch', N_('切速')), ('data', N_('数据')),
          ('end', N_('结束'))],
    'C': [('request', N_('请求')), ('ident', N_('标识')), ('ack', N_('ACK确认')), ('switch', N_('切速')),
          ('data', N_('数据/编程')), ('end', N_('结束'))],
    'D': [('ident', N_('标识')), ('data', N_('数据')), ('end', N_('结束'))],
    'E': [('request', N_('请求')), ('ident', N_('标识')), ('ack', N_('ACK确认')), ('switch', N_('切速')),
          ('data', N_('数据/HDLC')), ('end', N_('结束'))],
}
MODE_Y = {'0': N_('数据读取'), '1': N_('编程模式'), '2': N_('二进制 HDLC'),
          '6': N_('厂商自定义'), '7': N_('厂商自定义'), '8': N_('厂商自定义'), '9': N_('厂商自定义')}
FAULTS = {'': N_('无'), 'no_ident': N_('不回复标识'), 'no_data': N_('收到 ACK 后不发数据'),
          'bad_bcc': N_('数据 BCC 故意出错')}

DEFAULT_ITEMS = [
    ('0.0.0', '12345678', ''),
    ('1.8.0', '012345.678', 'kWh'),
    ('1.8.1', '006000.000', 'kWh'),
    ('1.8.2', '006345.678', 'kWh'),
    ('2.8.0', '000000.000', 'kWh'),
    ('32.7.0', '230.5', 'V'),
    ('31.7.0', '001.234', 'A'),
    ('F.F', '00000000', ''),
]


# ---------------------------------------------------------------- 报文工具
def calc_bcc(data: bytes) -> int:
    """BCC：逐字节异或（按 7 位计）。范围为 SOH/STX 之后到 ETX/EOT（含）。"""
    bcc = 0
    for b in data:
        bcc ^= b & 0x7F
    return bcc


def frame_with_bcc(start: int, body: bytes) -> bytes:
    """start(SOH/STX) + body（须以 ETX/EOT 结尾）+ BCC"""
    return bytes([start]) + body + bytes([calc_bcc(body)])


def data_set(addr, value, unit=''):
    return '%s(%s*%s)' % (addr, value, unit) if unit else '%s(%s)' % (addr, value)


def build_identification(mode, manufacturer, baud_char, identification) -> bytes:
    enhanced = '\\2' if mode == 'E' else ''
    return ('/' + manufacturer[:3] + baud_char + enhanced + identification).encode(ENC) + CRLF


def build_readout(items, bad_bcc=False) -> bytes:
    body = ''.join(data_set(a, v, u) + '\r\n' for a, v, u in items) + '!\r\n'
    msg = frame_with_bcc(STX, body.encode(ENC) + bytes([ETX]))
    if bad_bcc:
        msg = msg[:-1] + bytes([(msg[-1] ^ 0x2A) & 0x7F])
    return msg


def error_message(text='ERROR') -> bytes:
    return frame_with_bcc(STX, ('(%s)' % text).encode(ENC) + bytes([ETX]))


CTRL_NAMES = {SOH: '<SOH>', STX: '<STX>', ETX: '<ETX>', EOT: '<EOT>', ACK: '<ACK>',
              NAK: '<NAK>', CR: '<CR>', LF: '<LF>'}


def readable(data: bytes) -> str:
    out = []
    for b in data:
        if b in CTRL_NAMES:
            out.append(CTRL_NAMES[b])
        elif 0x20 <= b < 0x7F:
            out.append(chr(b))
        else:
            out.append('<%02X>' % b)
    return ''.join(out)


def to_hex(data: bytes) -> str:
    return ' '.join('%02X' % b for b in data)


def obis_core(addr: str) -> str:
    """去掉 OBIS 的 A-B: 前缀和 *F 后缀，用于提示“相近地址”。"""
    if ':' in addr:
        addr = addr.split(':', 1)[1]
    return addr.split('*', 1)[0]


# ---------------------------------------------------------------- 事件 / 日志
KIND_LABEL = {'rx': N_('收'), 'tx': N_('发'), 'info': N_('信息'), 'stage': N_('阶段'), 'warn': N_('警告'),
              'error': N_('问题'), 'hint': N_('建议'), 'link': N_('连接'), 'session': N_('会话'),
              'items': N_('数据')}
STATUS_LABEL = {'active': N_('进行中'), 'ok': N_('完成'), 'fail': N_('失败'), 'skip': N_('跳过')}


def kind_label(kind):
    return _(KIND_LABEL[kind]) if kind in KIND_LABEL else kind


def status_label(status):
    return _(STATUS_LABEL[status]) if status in STATUS_LABEL else ''


def make_event(kind, text='', data=None, **extra):
    ev = {'ts': time.time(), 'kind': kind, 'text': text, 'data': data}
    ev.update(extra)
    return ev


def fmt_ts(ts):
    return time.strftime('%H:%M:%S', time.localtime(ts)) + '.%03d' % int((ts % 1) * 1000)


def stage_text(ev) -> str:
    label = _(ev['label']) if ev.get('label') else ev.get('stage', '')
    s = _('%s：%s') % (label, status_label(ev.get('status')))
    return s + (_('（%s）') % ev['text'] if ev['text'] else '')


def format_event(ev, show_hex=True) -> str:
    head = '[%s] %s ' % (fmt_ts(ev['ts']), kind_label(ev['kind']))
    data = ev.get('data')
    if ev['kind'] in ('rx', 'tx') and data is not None:
        line = head + readable(data) + ('   // ' + ev['text'] if ev['text'] else '')
        if show_hex:
            line += '\n' + ' ' * 18 + 'HEX ' + to_hex(data)
        return line
    if ev['kind'] == 'stage':
        return head + stage_text(ev)
    if ev['kind'] == 'hint':
        return head + '→ ' + ev['text']
    return head + ev['text']


def save_events(path, events):
    """按扩展名导出：.csv 为表格，其它为文本。"""
    if path.lower().endswith('.csv'):
        with open(path, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.writer(f)
            w.writerow([_('时间'), _('类型'), _('说明'), _('报文(可读)'), _('报文(HEX)')])
            for ev in events:
                data = ev.get('data')
                text = stage_text(ev) if ev['kind'] == 'stage' else ev['text']
                w.writerow([time.strftime('%Y-%m-%d ', time.localtime(ev['ts'])) + fmt_ts(ev['ts']),
                            kind_label(ev['kind']), text,
                            readable(data) if data else '', to_hex(data) if data else ''])
    else:
        with open(path, 'w', encoding='utf-8') as f:
            for ev in events:
                f.write(format_event(ev) + '\n')


# ---------------------------------------------------------------- 配置
@dataclass
class MeterConfig:
    mode: str = 'C'
    manufacturer: str = 'INH'
    baud_char: str = '5'
    identification: str = 'MG301-SIM'
    address: str = ''               # 空 = 接受任意地址
    password: str = '00000000'      # 空 = 编程模式不校验口令
    reply_delay_ms: int = 200       # 响应延时（标准：20/200 ~ 1500 ms）
    ack_timeout_s: float = 3.0      # 发出标识后等待 ACK 的时间
    session_timeout_s: float = 60.0  # 编程 / HDLC 模式无通信超时
    strip_high_bit: bool = False    # 网络模式：接收时去掉最高位（主站按 7E1 透传时）
    push_interval_s: float = 0.0    # Mode D 自动推送间隔，0 = 只手动推送
    fault: str = ''                 # 见 FAULTS
    items: List[Tuple[str, str, str]] = field(default_factory=lambda: list(DEFAULT_ITEMS))


# ---------------------------------------------------------------- 协议引擎
class MeterEngine:
    """
    电表侧状态机。feed()/tick() 只在传输线程中调用；
    GUI 线程只调用 update_config()/push()，事件通过 emit 回调送出。
    """

    def __init__(self, config: MeterConfig, emit):
        self.cfg = config
        self._emit_cb = emit
        self.link = None
        self.session = 0
        self._push_now = False
        self._last_push = 0.0
        self._reset()

    # ---- 外部接口
    def attach(self, link):
        self.link = link

    def update_config(self, cfg: MeterConfig):
        self.cfg = cfg

    def push(self):
        self._push_now = True

    def on_link_up(self):
        self._reset()
        self._last_push = 0.0

    def on_link_down(self):
        if self.state != 'IDLE':
            self.warn(_('连接断开，当前会话中止'))
        self._reset()

    def feed(self, data: bytes):
        if self.cfg.strip_high_bit:
            data = bytes(b & 0x7F for b in data)
        data = self._split_echo(data)
        if not data:
            return
        self.emit('rx', '', data)
        self.last_rx = time.time()
        self.buf.extend(data)
        self._process()

    def tick(self):
        now = time.time()
        c = self.cfg
        if self.pending_since is not None:
            self._process()
        if self.junk and now - self.last_rx > 0.3:
            self._report_junk()

        if self.state == 'WAIT_ACK' and now - self.state_since > c.ack_timeout_s:
            self._ack_timeout()
        elif self.state in ('PROG', 'BINARY') and \
                now - max(self.state_since, self.last_rx) > c.session_timeout_s:
            self.warn(_('%.0f 秒无通信，会话超时结束') % c.session_timeout_s)
            self._end_session(False)

        if c.mode == 'D' and self.state == 'IDLE':
            due = c.push_interval_s > 0 and now - self._last_push >= c.push_interval_s
            if self._push_now or due:
                self._push_now = False
                self._last_push = now
                self._push_mode_d()
        elif self._push_now:
            self._push_now = False
            self.warn(_('只有 Mode D 支持主动推送'))

    # ---- 事件
    def emit(self, kind, text='', data=None, **extra):
        self._emit_cb(make_event(kind, text, data, **extra))

    def info(self, text):
        self.emit('info', text)

    def warn(self, text):
        self.emit('warn', text)

    def problem(self, text, hint=''):
        self.emit('error', text)
        if hint:
            self.emit('hint', hint)

    def stage(self, key, status, text=''):
        label = dict(STAGES.get(self.cfg.mode, [])).get(key, key)
        self.emit('stage', text, stage=key, status=status, label=label)

    # ---- 内部状态
    def _reset(self):
        self.state = 'IDLE'
        self.buf = bytearray()
        self.junk = bytearray()
        self.state_since = time.time()
        self.last_rx = 0.0
        self.pending_since = None
        self.logged_in = False
        self.last_tx = b''
        self.echo_expect = b''
        self.echo_deadline = 0.0
        self.echo_warned = False

    def _new_session(self):
        self.session += 1
        self.logged_in = False
        self.emit('session', _('会话 #%d 开始（Mode %s）') % (self.session, self.cfg.mode),
                  session=self.session, mode=self.cfg.mode)

    def _set_state(self, st):
        self.state = st
        self.state_since = time.time()

    def _send(self, data: bytes, note=''):
        if not self.link:
            return
        self.link.send(data)
        self.last_tx = data
        self.echo_expect = data
        self.echo_deadline = time.time() + 1.0 + len(data) * 11.0 / (self.link.baud or 9600)
        self.emit('tx', note, data)

    def _sleep_reply(self):
        time.sleep(max(0, self.cfg.reply_delay_ms) / 1000.0)

    def _switch_baud(self, baud):
        link = self.link
        if link is None or link.baud is None:
            self.stage('switch', 'skip', _('网络连接，无需切换波特率'))
            return
        if baud == link.baud:
            self.stage('switch', 'skip', _('波特率不变 %d') % baud)
            return
        old = link.baud
        link.drain()
        link.set_baud(baud)
        self.stage('switch', 'ok', '%d → %d bps' % (old, baud))

    def _end_session(self, ok=True):
        link = self.link
        if link is not None and link.baud is not None and link.baud != link.init_baud:
            link.drain()
            time.sleep(0.05)
            link.set_baud(link.init_baud)
            self.info(_('已恢复初始波特率 %d bps，等待下一次请求') % link.init_baud)
        self._set_state('IDLE')
        self.stage('end', 'ok' if ok else 'fail')

    def _split_echo(self, data: bytes) -> bytes:
        """把收到的、与刚发出报文相同的前缀视为回显（RS-485 / 光口回环常见）。"""
        if not self.echo_expect or time.time() > self.echo_deadline:
            self.echo_expect = b''
            return data
        n = 0
        while n < len(data) and n < len(self.echo_expect) and data[n] == self.echo_expect[n]:
            n += 1
        # 只把完整回显或 ≥4 字节的匹配当作回显，避免把主站重发的 "/" 误判
        if n < len(self.echo_expect) and n < 4:
            self.echo_expect = b''
            return data
        self.echo_expect = self.echo_expect[n:]
        self.emit('rx', _('回显（模拟器自己发出的数据被送回），不参与解析'), data[:n])
        if not self.echo_warned:
            self.echo_warned = True
            self.problem(_('检测到回显：收到了模拟器刚发出的报文'),
                         _('常见于 RS-485 半双工或光口回环。DTU 同样会收到自己发出的请求，'
                           '需在 DTU 侧丢弃回显，或改用收发自动切换的 485 模块'))
        return data[n:]

    def _junk(self, data: bytes):
        self.junk.extend(data)
        if len(self.junk) > 256:
            self._report_junk()

    def _expect_text(self):
        c = self.cfg
        return {
            'IDLE': _('请求报文 /?设备地址!<CR><LF>（广播为 /?!<CR><LF>）'),
            'WAIT_ACK': _('ACK 选项报文 <ACK>0%s0<CR><LF>（HEX 06 30 %02X 30 0D 0A）')
                        % (c.baud_char, ord(c.baud_char[:1] or '5')),
            'PROG': _('编程命令 <SOH>命令<STX>数据<ETX><BCC>，例如 <SOH>R1<STX>1.8.0()<ETX><BCC>'),
            'BINARY': _('HDLC 帧'),
        }.get(self.state, '')

    def _report_junk(self):
        data = bytes(self.junk)
        self.junk = bytearray()
        if not data:
            return
        masked = bytes(b & 0x7F for b in data)
        has_high = any(b & 0x80 for b in data)
        printable = all(0x20 <= b < 0x7F or b in (CR, LF, ACK, SOH, STX, ETX) for b in masked)
        even_parity = all(bin(b).count('1') % 2 == 0 for b in data)

        if has_high and printable and even_parity:
            self.problem(_('收到的字节最高位被置位，去掉最高位后为：%s') % readable(masked),
                         _('主站按 7 数据位 + 偶校验（7E1）发送，而模拟器按 8 数据位接收。'
                           '串口：把模拟器改为 7 位 / 偶校验 E；网络：勾选「接收时去掉最高位」。'
                           '反过来也说明：DTU 应使用 7E1，IEC 62056-21 规定的就是 7E1'))
            return
        if data[0] == ACK and self.state == 'IDLE':
            self.problem(_('收到 ACK 选项报文，但当前没有进行中的会话：%s') % readable(data),
                         _('必须先发请求 /?!<CR><LF> 并收到电表标识后，才能发 ACK 选项。'
                           '也可能会话已超时（ACK 超时 %.1f 秒），或主站的请求没被电表收到')
                         % self.cfg.ack_timeout_s)
            return
        if data[0] == SOH and self.state == 'IDLE':
            self.problem(_('收到编程命令，但电表当前不在编程模式：%s') % readable(data),
                         _('进入编程模式的顺序：/?!<CR><LF> → 收标识 → <ACK>0Z1<CR><LF> → 收 P0 → 发 P1 口令'))
            return
        if has_high or 0x00 in data or not printable:
            self.problem(_('收到无法识别的字节：%s') % to_hex(data[:48]),
                         _('常见原因是双方波特率或数据位/校验位不一致，例如主站 9600、电表 300；'
                           '或波特率切换时机不对（主站在发 ACK 之前就切了速，或电表切速后主站还没切）。'
                           'Mode C 应在 ACK 之后才切换到协商波特率'))
            return
        self.problem(_('收到不符合协议的数据：%s') % readable(data),
                     _('当前应收到 %s') % self._expect_text())

    # ---- 主处理循环
    def _process(self):
        handlers = {'IDLE': self._proc_idle, 'WAIT_ACK': self._proc_wait_ack,
                    'PROG': self._proc_prog, 'BINARY': self._proc_binary}
        while True:
            before = (self.state, len(self.buf), self.pending_since)
            handlers[self.state]()
            if (self.state, len(self.buf), self.pending_since) == before:
                break

    def _wait_crlf(self, tail: bytes) -> bool:
        """报文末尾的 CRLF 还没到齐时等待最多 0.3 s。返回 True 表示继续等待。"""
        if len(tail) >= 2 or tail != CRLF[:len(tail)]:
            self.pending_since = None
            return False
        if self.pending_since is None:
            self.pending_since = time.time()
        if time.time() - self.pending_since < 0.3:
            return True
        self.pending_since = None
        return False

    # ---- IDLE：等待请求
    def _proc_idle(self):
        buf = self.buf
        if not buf:
            return
        i = buf.find(b'/')
        if i == -1:
            self._junk(bytes(buf))
            buf.clear()
            return
        if i > 0:
            self._junk(bytes(buf[:i]))
            del buf[:i]
        j = buf.find(b'!')
        if j == -1:
            if len(buf) > 64:
                self.problem(_('收到以 / 开头的数据但一直没有结束符 !：%s') % readable(bytes(buf[:64])),
                             _('请求报文格式为 /?设备地址!<CR><LF>，! 不能省略'))
                buf.clear()
            return
        tail = bytes(buf[j + 1:j + 3])
        if self._wait_crlf(tail):
            return
        crlf_ok = tail == CRLF
        req = bytes(buf[:j + 1])
        consumed = j + 1 + (2 if crlf_ok else len(tail) if tail == CRLF[:len(tail)] else 0)
        del buf[:consumed]
        if self.junk:
            self._report_junk()
        self._on_request(req, crlf_ok)

    def _on_request(self, req: bytes, crlf_ok: bool):
        c = self.cfg
        text = req.decode(ENC)
        self._new_session()
        self.stage('request', 'active')
        if c.mode == 'D':
            self.problem(_('收到请求 %s，但 Mode D 电表只单向推送、不响应请求') % readable(req),
                         _('若 DTU 需要主动抄表，请把模拟器切到 Mode A/B/C；'
                           '若电表确实是 Mode D，DTU 应以 2400 bps 7E1 被动接收'))
            self.stage('request', 'fail')
            return
        if len(text) < 3 or text[1] != '?':
            self.problem(_('请求报文格式错误：%s') % readable(req),
                         _('正确格式为 /?设备地址!<CR><LF>：第 2 个字符必须是 ?。'
                           '例如 /?!<CR><LF>（HEX 2F 3F 21 0D 0A）'))
            self.stage('request', 'fail')
            return
        addr = text[2:-1]
        if not crlf_ok:
            self.problem(_('请求报文缺少结尾的 <CR><LF>'),
                         _('应发送 %s<CR><LF>（HEX 末尾 0D 0A）。模拟器仍会应答，但很多真实电表会直接不应答')
                         % text)
        if len(addr) > 32:
            self.problem(_('设备地址长度 %d 超过标准规定的 32 个字符') % len(addr), _('检查 DTU 中的电表地址配置'))
        if any(not (ch.isalnum() or ch == ' ') for ch in addr):
            self.warn(_('设备地址含非字母数字字符："%s"，部分电表不接受') % addr)
        if addr and c.address and addr.lstrip('0') != c.address.lstrip('0'):
            self.problem(_('请求地址 "%s" 与电表地址 "%s" 不一致，电表不应答') % (addr, c.address),
                         _('DTU 中把电表地址设为 %s，或在总线上只有一块表时使用广播请求 /?!<CR><LF>')
                         % c.address)
            self.stage('request', 'fail')
            return
        self.info(_('收到请求：设备地址 = %s') % (addr or _('（空，广播）')))
        self.stage('request', 'ok')

        if c.fault == 'no_ident':
            self.warn(_('故障注入：不回复标识报文'))
            self.stage('ident', 'fail', _('故障注入'))
            return
        self._sleep_reply()
        self.stage('ident', 'active')
        self._send(build_identification(c.mode, c.manufacturer, c.baud_char, c.identification),
                   _('标识报文：厂商 %s，波特率字符 %s') % (c.manufacturer[:3], c.baud_char))
        self.stage('ident', 'ok')

        if c.mode == 'A':
            self._sleep_reply()
            self._end_session(self._send_readout())
        elif c.mode == 'B':
            baud = BAUD_B.get(c.baud_char)
            if baud is None:
                self.problem(_('Mode B 的波特率字符应为 A~F，当前为 "%s"') % c.baud_char,
                             _('在电表设置中修改波特率字符'))
            self._sleep_reply()
            if baud:
                self._switch_baud(baud)
            self._end_session(self._send_readout())
        else:
            self._set_state('WAIT_ACK')
            self.stage('ack', 'active', _('等待主站 ACK 选项（%.1f 秒）') % c.ack_timeout_s)

    def _send_readout(self) -> bool:
        c = self.cfg
        self.stage('data', 'active')
        if c.fault == 'no_data':
            self.warn(_('故障注入：不发送数据报文'))
            self.stage('data', 'fail', _('故障注入'))
            return False
        bad = c.fault == 'bad_bcc'
        msg = build_readout(c.items, bad_bcc=bad)
        self._send(msg, _('数据报文：%d 项，BCC=0x%02X%s') % (len(c.items), msg[-1], _('（故意出错）') if bad else ''))
        self.stage('data', 'ok')
        return True

    # ---- WAIT_ACK：等待选项确认
    def _proc_wait_ack(self):
        buf = self.buf
        if not buf:
            return
        k_req = buf.find(b'/')
        k_ack = buf.find(bytes([ACK]))
        if k_req != -1 and (k_ack == -1 or k_req < k_ack):
            if k_req > 0:
                self._junk(bytes(buf[:k_req]))
                del buf[:k_req]
            self.problem(_('主站没有发送 ACK 选项，而是重新发送了请求'),
                         _('说明主站没能接收或解析电表的标识报文。请检查：① DTU 串口是否为 7E1（不是 8N1）；'
                           '② DTU 是否支持标识中的波特率字符 "%s"；③ DTU 等待标识的超时是否太短'
                           '（模拟器当前响应延时 %d ms）。若 DTU 按 Mode A/B 工作（不发 ACK），'
                           '请把模拟器切到对应模式验证') % (self.cfg.baud_char, self.cfg.reply_delay_ms))
            self.stage('ack', 'fail')
            self._set_state('IDLE')
            return
        if k_ack == -1:
            if buf.find(bytes([SOH])) != -1:
                self.problem(_('在 ACK 选项确认之前收到了编程命令（SOH 开头）'),
                             _('应先发 <ACK>0%s1<CR><LF> 进入编程模式，收到电表 P0 后再发 P1 口令')
                             % self.cfg.baud_char)
                buf.clear()
                return
            self._junk(bytes(buf))
            buf.clear()
            return
        if k_ack > 0:
            self._junk(bytes(buf[:k_ack]))
            del buf[:k_ack]
        if len(buf) < 4:
            return  # 等待 V Z Y；不到齐由 ACK 超时处理
        tail = bytes(buf[4:6])
        if self._wait_crlf(tail):
            return
        crlf_ok = tail == CRLF
        frame = bytes(buf[:4])
        del buf[:4 + (2 if crlf_ok else len(tail) if tail == CRLF[:len(tail)] else 0)]
        if self.junk:
            self._report_junk()
        self._on_ack(frame, crlf_ok)

    def _ack_timeout(self):
        c = self.cfg
        if self.buf[:1] == bytes([ACK]):
            self.problem(_('只收到 %s，ACK 选项报文不完整') % readable(bytes(self.buf)),
                         _('Mode C 的 ACK 选项报文共 6 字节：<ACK> V Z Y <CR><LF>，'
                           '读数应为 <ACK>0%s0<CR><LF>（HEX 06 30 %02X 30 0D 0A）')
                         % (c.baud_char, ord(c.baud_char[:1] or '5')))
        else:
            self.problem(_('发出标识后 %.1f 秒内没有收到主站的 ACK 选项报文') % c.ack_timeout_s,
                         _('Mode C 要求主站收到标识后发送 <ACK>0%s0<CR><LF>（HEX 06 30 %02X 30 0D 0A）。'
                           '可能原因：① DTU 按 Mode A/B 工作，不发 ACK 而直接等数据——可把模拟器切到 Mode A 或 B 验证；'
                           '② DTU 没收到/没解析出标识报文（检查 7E1、波特率、接线）；'
                           '③ DTU 先切了波特率再发 ACK，导致电表收到乱码')
                         % (c.baud_char, ord(c.baud_char[:1] or '5')))
        self.buf.clear()
        self.stage('ack', 'fail', _('超时'))
        self._end_session(False)

    def _on_ack(self, frame: bytes, crlf_ok: bool):
        c = self.cfg
        v, z, y = chr(frame[1]), chr(frame[2]), chr(frame[3])
        good = _('<ACK>0%s0<CR><LF>（读数）或 <ACK>0%s1<CR><LF>（编程）') % (c.baud_char, c.baud_char)
        self.info(_('收到 ACK 选项：协议 V=%s，波特率 Z=%s，模式 Y=%s（%s）')
                  % (v, z, y, _(MODE_Y.get(y, N_('未知')))))

        def fail(text, hint):
            self.problem(text, hint)
            self.stage('ack', 'fail')
            self._end_session(False)

        if not crlf_ok:
            self.problem(_('ACK 选项报文缺少结尾的 <CR><LF>'), _('完整格式为 %s') % good)
        if v not in '012':
            return fail(_('协议控制字符 V="%s" 无效') % v,
                        _('正常协议应为 0（Mode E 进入 HDLC 时为 2）。正确报文：%s') % good)
        if z not in BAUD_C:
            return fail(_('波特率字符 Z="%s" 无效（Mode C/E 只用 0~6）') % z,
                        _('主站应回送电表标识中的波特率字符 "%s"。正确报文：%s') % (c.baud_char, good))
        offered = BAUD_C.get(c.baud_char)
        want = BAUD_C[z]
        if offered and want > offered:
            return fail(_('主站要求 %d bps，高于电表在标识中提议的 %d bps') % (want, offered),
                        _('Z 只能等于或低于标识中的 "%s"。正确报文：%s') % (c.baud_char, good))
        if offered and want < offered:
            self.info(_('主站选择了较低的波特率 %d bps（标准允许）') % want)
        if y in '6789':
            return fail(_('主站请求厂商自定义模式 Y=%s，模拟器未实现') % y, _('标准读数用 Y=0，编程用 Y=1'))
        if y == '2' or v == '2':
            if c.mode != 'E':
                return fail(_('主站请求 HDLC 二进制模式（属于 Mode E），而电表当前为 Mode %s') % c.mode,
                            _('若 DTU 走 DLMS/COSEM，请把模拟器切到 Mode E；若只需读数，ACK 应为 %s') % good)
            if not (v == '2' and y == '2'):
                self.warn(_('进入 HDLC 时 V 和 Y 通常都为 2，即 <ACK>2%s2<CR><LF>') % c.baud_char)
        elif y not in '01':
            return fail(_('模式控制字符 Y="%s" 无效') % y, _('0=数据读取，1=编程模式，2=HDLC（仅 Mode E）'))

        self.stage('ack', 'ok', _(MODE_Y[y]) if y in MODE_Y else '')
        self._sleep_reply()
        self._switch_baud(want)
        if y == '0':
            self._end_session(self._send_readout())
        elif y == '1':
            seed = c.address or c.identification
            p0 = frame_with_bcc(SOH, b'P0' + bytes([STX]) + ('(%s)' % seed).encode(ENC) + bytes([ETX]))
            self.stage('data', 'active', _('编程模式'))
            self._send(p0, _('口令请求 P0'))
            self.logged_in = not c.password
            self._set_state('PROG')
        else:
            self.stage('data', 'active', 'HDLC')
            self.info(_('已进入 HDLC 二进制模式。模拟器未实现 DLMS/COSEM 应用层，只记录收到的 HDLC 帧'))
            self._set_state('BINARY')

    # ---- PROG：编程模式命令
    def _proc_prog(self):
        buf = self.buf
        while buf and buf[0] not in (SOH, STX, ACK, NAK):
            idx = [k for k in (buf.find(bytes([s])) for s in (SOH, STX, ACK, NAK)) if k != -1]
            cut = min(idx) if idx else len(buf)
            self._junk(bytes(buf[:cut]))
            del buf[:cut]
        if not buf:
            return
        if self.junk:
            self._report_junk()
        if buf[0] == ACK:
            del buf[0]
            return
        if buf[0] == NAK:
            del buf[0]
            self.warn(_('主站发送 NAK，要求电表重发上一条报文'))
            if self.last_tx:
                self._send(self.last_tx, _('重发'))
            return
        ends = [k for k in (buf.find(bytes([ETX]), 1), buf.find(bytes([EOT]), 1)) if k != -1]
        if not ends:
            if len(buf) > 512:
                self.problem(_('命令报文超过 512 字节仍没有 <ETX>'), _('每条命令必须以 <ETX><BCC> 结束'))
                buf.clear()
            return
        end = min(ends)
        if len(buf) < end + 2:
            return  # 等 BCC
        frame = bytes(buf[:end + 2])
        del buf[:end + 2]
        self._on_command(frame)

    def _on_command(self, frame: bytes):
        c = self.cfg
        self.state_since = time.time()
        body, got = frame[1:-1], frame[-1]
        want = calc_bcc(body)
        if frame[0] == STX:
            self.problem(_('编程模式下命令应以 <SOH> 开头，收到的是 <STX>：%s') % readable(frame),
                         _('命令格式：<SOH>命令<STX>数据<ETX><BCC>，例如 <SOH>R1<STX>1.8.0()<ETX><BCC>'))
            self._send(bytes([NAK]), 'NAK')
            return
        if (got & 0x7F) != want:
            self.problem(_('BCC 校验错误：收到 0x%02X，正确应为 0x%02X') % (got, want),
                         _('BCC 从 SOH 之后的第一个字节开始、到 ETX（含）为止逐字节异或，'
                           '不含 SOH 本身，也不含 BCC。本报文正确写法：%s')
                         % to_hex(frame[:-1] + bytes([want])))
            self._send(bytes([NAK]), _('NAK（BCC 错误）'))
            return
        if len(body) < 3:
            self.problem(_('命令报文太短：%s') % readable(frame), _('格式：<SOH>命令<STX>数据<ETX><BCC>'))
            self._send(bytes([NAK]), 'NAK')
            return
        cmd, ctype = chr(body[0]), chr(body[1])
        label = cmd + ctype
        if cmd not in 'PWREB' or not ctype.isdigit():
            self.problem(_('未知命令 "%s"') % label,
                         _('有效命令：P1/P2 口令，R1~R6 读，W1~W5 写，E1/E2 执行，B0/B1 结束'))
            self._send(error_message(), _('错误应答'))
            return
        rest = body[2:-1]
        if rest and rest[0] != STX:
            self.problem(_('命令字 %s 之后应紧跟 <STX>') % label, _('正确示例：<SOH>R1<STX>1.8.0()<ETX><BCC>'))
            self._send(bytes([NAK]), 'NAK')
            return
        data = rest[1:].decode(ENC) if rest else ''
        self.info(_('收到命令 %s，数据：%s') % (label, data or _('（无）')))

        if cmd == 'B':
            self.info(_('收到结束命令 %s，会话结束') % label)
            self.stage('data', 'ok', _('编程会话结束'))
            self._end_session(True)
            return

        if cmd == 'P':
            if ctype == '0':
                self.problem(_('P0 是电表发给主站的口令请求，主站不应发送'),
                             _('主站应发送 P1（明文口令）或 P2（加密口令）'))
                self._send(bytes([NAK]), 'NAK')
                return
            if not (data.startswith('(') and data.endswith(')')):
                self.problem(_('口令数据应放在括号内，收到：%s') % data,
                             _('例如 <SOH>P1<STX>(%s)<ETX><BCC>') % (c.password or _('口令')))
            pw = data[1:-1] if data.startswith('(') and data.endswith(')') else data
            if not c.password or ctype == '2':
                if ctype == '2':
                    self.info(_('P2 为加密口令，模拟器不校验，直接通过'))
                self.logged_in = True
                self._send(bytes([ACK]), _('口令通过'))
            elif pw == c.password:
                self.logged_in = True
                self._send(bytes([ACK]), _('口令正确'))
            else:
                self.problem(_('口令错误：收到 "%s"') % pw,
                             _('电表配置的口令为 "%s"，请在 DTU 中修正。电表发送 B0 中止会话') % c.password)
                self._send(frame_with_bcc(SOH, b'B0' + bytes([ETX])), _('中止 B0'))
                self.stage('data', 'fail', _('口令错误'))
                self._end_session(False)
            return

        if not self.logged_in:
            self.problem(_('未通过口令验证就发送了 %s') % label,
                         _('应先发送 <SOH>P1<STX>(口令)<ETX><BCC>，收到电表 <ACK> 后再读写'))
            self._send(error_message(), _('错误应答'))
            return

        if cmd == 'R':
            if '(' not in data or not data.endswith(')'):
                self.warn(_('读命令的数据通常为 地址(参数)，例如 1.8.0()，收到：%s') % data)
            addr = data.split('(', 1)[0]
            item = next((it for it in c.items if it[0] == addr), None)
            if item:
                msg = frame_with_bcc(STX, data_set(*item).encode(ENC) + bytes([ETX]))
                self._send(msg, _('读 %s 应答') % addr)
            else:
                sep = _('、')
                similar = [it[0] for it in c.items if obis_core(it[0]) == obis_core(addr)]
                hint = _('表中有相近地址 %s，OBIS 写法需与电表完全一致') % sep.join(similar) if similar else \
                    _('可用地址：%s。可在数据项表中添加') % sep.join(it[0] for it in c.items[:12])
                self.problem(_('读取的地址 "%s" 不存在') % addr, hint)
                self._send(error_message(), _('错误应答'))
            return

        if cmd == 'W':
            if '(' not in data or not data.endswith(')'):
                self.problem(_('写命令数据格式错误：%s') % data,
                             _('格式为 地址(值)，例如 <SOH>W1<STX>C.1.0(1234)<ETX><BCC>'))
                self._send(error_message(), _('错误应答'))
                return
            addr, value = data[:-1].split('(', 1)
            items = list(c.items)
            for k, it in enumerate(items):
                if it[0] == addr:
                    items[k] = (addr, value, it[2])
                    break
            else:
                items.append((addr, value, ''))
            self.cfg = replace(c, items=items)
            self.emit('items', _('主站写入 %s = %s') % (addr, value), items=items)
            self._send(bytes([ACK]), _('写入成功'))
            return

        if cmd == 'E':
            self._send(bytes([ACK]), _('执行成功'))

    # ---- BINARY：HDLC 只记录
    def _proc_binary(self):
        if self.buf:
            self.info(_('HDLC 数据 %d 字节（未解析）') % len(self.buf))
            self.buf.clear()

    # ---- Mode D：主动推送
    def _push_mode_d(self):
        c = self.cfg
        self._new_session()
        self.stage('ident', 'active')
        self._send(build_identification('D', c.manufacturer, c.baud_char, c.identification),
                   _('Mode D 推送：标识'))
        self.stage('ident', 'ok')
        self._sleep_reply()
        self._end_session(self._send_readout())


# ---------------------------------------------------------------- 传输层
def split_hostport(text, default_host='0.0.0.0'):
    text = text.strip()
    if ':' in text:
        h, p = text.rsplit(':', 1)
        return (h or default_host), int(p)
    return default_host, int(text)


def list_serial_ports():
    if list_ports is None:
        return []
    return [p.device for p in list_ports.comports()]


class BaseLink(threading.Thread):
    """传输线程：收数据交给 engine.feed()，并周期调用 engine.tick()。"""

    def __init__(self, engine: MeterEngine, emit):
        super().__init__(daemon=True)
        self.engine = engine
        self._emit = emit
        self.running = True
        self.baud = None        # 网络连接为 None
        self.init_baud = None
        engine.attach(self)

    def log(self, kind, text, **extra):
        self._emit(make_event(kind, text, **extra))

    def open(self):
        """在启动线程前同步调用，失败直接抛异常给调用方。"""

    def stop(self):
        self.running = False

    def run(self):
        try:
            self._run()
        except Exception as e:
            self.log('error', _('连接异常：%s') % e)
        finally:
            self._close()
            self.log('link', _('已停止'), up=False, stopped=True)

    def _pump(self, data):
        if data:
            self.engine.feed(data)
        self.engine.tick()

    def send(self, data: bytes):
        raise NotImplementedError

    def drain(self):
        pass

    def set_baud(self, baud):
        pass

    def _run(self):
        raise NotImplementedError

    def _close(self):
        pass


class SerialLink(BaseLink):
    def __init__(self, engine, emit, port, baud=300, bytesize=7, parity='E', stopbits=1):
        super().__init__(engine, emit)
        self.port = port
        self.baud = self.init_baud = int(baud)
        self.bytesize, self.parity, self.stopbits = int(bytesize), parity, int(stopbits)
        self.ser = None
        self._tx_done_at = 0.0

    def open(self):
        if serial is None:
            raise RuntimeError(_('未安装 pyserial，请执行：pip install pyserial'))
        self.ser = serial.Serial(
            self.port, baudrate=self.baud,
            bytesize=serial.SEVENBITS if self.bytesize == 7 else serial.EIGHTBITS,
            parity={'N': serial.PARITY_NONE, 'E': serial.PARITY_EVEN, 'O': serial.PARITY_ODD}[self.parity],
            stopbits=serial.STOPBITS_TWO if self.stopbits == 2 else serial.STOPBITS_ONE,
            timeout=0.05, xonxoff=False, rtscts=False, dsrdtr=False)

    def _run(self):
        self.log('link', _('串口 %s 已打开：%d bps %d%s%d，等待主站请求…')
                 % (self.port, self.baud, self.bytesize, self.parity, self.stopbits), up=True)
        self.engine.on_link_up()
        while self.running:
            self._pump(self.ser.read(self.ser.in_waiting or 1))

    def _bits_per_char(self):
        return 1 + self.bytesize + (0 if self.parity == 'N' else 1) + self.stopbits

    def send(self, data):
        self.ser.write(data)
        start = max(time.time(), self._tx_done_at)
        self._tx_done_at = start + len(data) * self._bits_per_char() / float(self.baud)

    def drain(self):
        """等数据真正发完再切波特率（USB 转串口有缓存，flush 不一定等到线上发完）。"""
        self.ser.flush()
        wait = self._tx_done_at - time.time()
        if wait > 0:
            time.sleep(wait + 0.01)

    def set_baud(self, baud):
        self.ser.baudrate = baud
        self.baud = baud
        self.log('info', _('串口波特率已切换为 %d bps') % baud)

    def _close(self):
        if self.ser:
            try:
                self.ser.close()
            except Exception:
                pass


class TcpServerLink(BaseLink):
    def __init__(self, engine, emit, host, port):
        super().__init__(engine, emit)
        self.host, self.port = host, int(port)
        self.srv = None
        self.conn = None

    def open(self):
        self.srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.srv.bind((self.host, self.port))
        self.srv.listen(1)
        self.srv.settimeout(0.2)

    def _run(self):
        self.log('link', _('TCP 服务端监听 %s:%d，等待主站连接…') % (self.host, self.port), up=False)
        while self.running:
            try:
                conn, peer = self.srv.accept()
            except socket.timeout:
                continue
            conn.settimeout(0.05)
            self.conn = conn
            self.log('link', _('主站已连接：%s:%d') % peer, up=True)
            self.engine.on_link_up()
            while self.running:
                try:
                    data = conn.recv(4096)
                    if not data:
                        break
                except socket.timeout:
                    data = b''
                except OSError:
                    break
                self._pump(data)
            self.conn = None
            conn.close()
            self.engine.on_link_down()
            self.log('link', _('主站已断开：%s:%d，继续监听…') % peer, up=False)

    def send(self, data):
        if self.conn:
            self.conn.sendall(data)
        else:
            self.log('warn', _('没有已连接的主站，数据未发送'))

    def _close(self):
        for s in (self.conn, self.srv):
            if s:
                try:
                    s.close()
                except Exception:
                    pass


class TcpClientLink(BaseLink):
    def __init__(self, engine, emit, host, port):
        super().__init__(engine, emit)
        self.host, self.port = host, int(port)
        self.sock = None

    def _run(self):
        while self.running:
            self.log('link', _('正在连接 %s:%d …') % (self.host, self.port), up=False)
            try:
                self.sock = socket.create_connection((self.host, self.port), timeout=3)
            except OSError as e:
                self.log('warn', _('连接失败：%s，3 秒后重试') % e)
                self._sleep(3)
                continue
            self.sock.settimeout(0.05)
            self.log('link', _('已连接到主站 %s:%d') % (self.host, self.port), up=True)
            self.engine.on_link_up()
            while self.running:
                try:
                    data = self.sock.recv(4096)
                    if not data:
                        break
                except socket.timeout:
                    data = b''
                except OSError:
                    break
                self._pump(data)
            self.sock.close()
            self.sock = None
            self.engine.on_link_down()
            if self.running:
                self.log('link', _('连接断开，3 秒后重连'), up=False)
                self._sleep(3)

    def _sleep(self, sec):
        end = time.time() + sec
        while self.running and time.time() < end:
            time.sleep(0.1)

    def send(self, data):
        if self.sock:
            self.sock.sendall(data)
        else:
            self.log('warn', _('未连接，数据未发送'))

    def _close(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass


class UdpLink(BaseLink):
    """绑定本地端口；应答发给最近一次发来数据的主站，或固定的目标地址。"""

    def __init__(self, engine, emit, host, port, target=None):
        super().__init__(engine, emit)
        self.host, self.port = host, int(port)
        self.target = target   # (host, port) 或 None
        self.peer = None
        self.sock = None

    def open(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.settimeout(0.05)

    def _run(self):
        self.log('link', _('UDP 已绑定 %s:%d，等待主站数据…') % (self.host, self.port), up=True)
        self.engine.on_link_up()
        while self.running:
            try:
                data, peer = self.sock.recvfrom(4096)
                if peer != self.peer:
                    self.peer = peer
                    self.log('link', _('UDP 主站：%s:%d') % peer, up=True)
            except socket.timeout:
                data = b''
            except OSError:
                data = b''
            self._pump(data)

    def send(self, data):
        dest = self.peer or self.target
        if dest:
            self.sock.sendto(data, dest)
        else:
            self.log('warn', _('还没有收到过主站数据，也未配置目标地址，数据未发送'))

    def _close(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass


# ---------------------------------------------------------------- 命令行入口
def main():
    import i18n
    ap = argparse.ArgumentParser(description=_('IEC 62056-21 电表模拟器（命令行版）'))
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--serial', metavar='PORT', help=_('串口，如 COM3 或 /dev/ttyUSB0'))
    g.add_argument('--tcp-server', metavar='HOST:PORT', help=_('作为 TCP 服务端监听'))
    g.add_argument('--tcp-client', metavar='HOST:PORT', help=_('作为 TCP 客户端连接主站'))
    g.add_argument('--udp', metavar='HOST:PORT', help=_('绑定 UDP 端口'))
    ap.add_argument('--udp-target', metavar='HOST:PORT', help=_('UDP 默认目标（Mode D 推送用）'))
    ap.add_argument('--mode', default='C', choices=list('ABCDE'))
    ap.add_argument('--baud', type=int, help=_('串口初始波特率（默认按模式：D=2400，其余 300）'))
    ap.add_argument('--format', default='7E1', help=_('串口帧格式，如 7E1 / 8N1'))
    ap.add_argument('--baud-char', help=_('标识中的波特率字符（默认按模式）'))
    ap.add_argument('--manufacturer', default='INH')
    ap.add_argument('--ident', default='MG301-SIM')
    ap.add_argument('--address', default='')
    ap.add_argument('--password', default='00000000')
    ap.add_argument('--delay', type=int, default=200, help=_('响应延时 ms'))
    ap.add_argument('--push-interval', type=float, default=0, help=_('Mode D 推送间隔秒'))
    ap.add_argument('--strip-high-bit', action='store_true')
    ap.add_argument('--log', help=_('退出时保存日志（.txt 或 .csv）'))
    ap.add_argument('--lang', choices=list(i18n.LANGS), help='en / zh / es')
    a = ap.parse_args()
    if a.lang:
        i18n.set_lang(a.lang)

    init_baud, bchar = MODE_DEFAULTS[a.mode]
    cfg = MeterConfig(mode=a.mode, manufacturer=a.manufacturer, baud_char=a.baud_char or bchar,
                      identification=a.ident, address=a.address, password=a.password,
                      reply_delay_ms=a.delay, push_interval_s=a.push_interval,
                      strip_high_bit=a.strip_high_bit)
    events = []

    def emit(ev):
        events.append(ev)
        print(format_event(ev), flush=True)

    engine = MeterEngine(cfg, emit)
    if a.serial:
        f = a.format.upper()
        link = SerialLink(engine, emit, a.serial, a.baud or init_baud, int(f[0]), f[1], int(f[2]))
    elif a.tcp_server:
        link = TcpServerLink(engine, emit, *split_hostport(a.tcp_server))
    elif a.tcp_client:
        link = TcpClientLink(engine, emit, *split_hostport(a.tcp_client, '127.0.0.1'))
    else:
        target = split_hostport(a.udp_target, '127.0.0.1') if a.udp_target else None
        link = UdpLink(engine, emit, *split_hostport(a.udp), target=target)
    link.open()
    link.start()
    try:
        while link.is_alive():
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass
    link.stop()
    link.join(2)
    if a.log:
        save_events(a.log, events)
        print(_('日志已保存：%s') % a.log)


if __name__ == '__main__':
    main()
