#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用 master（主站）验证电表模拟器本身是否正确。

- Mode C 读数 / 编程模式：使用独立的开源实现 pwitab iec62056-21 作为主站
- Mode A/B/D/E、UDP、各类错误报文诊断：用原始报文模拟主站
- 可选：--serial PORT_A PORT_B  用一对已连好的串口（或 socat 虚拟串口）跑 pwitab 串口读数

依赖：pip install pyserial iec62056-21
运行：python3 master测试.py
"""

import ast
import os
import re
import socket
import sys
import threading
import time
from collections import Counter
from dataclasses import replace

import i18n
import meter_core as mc

i18n.set_lang('zh')  # 下面的用例按中文日志断言；多语言另由 test_i18n 检查

try:
    from iec62056_21.client import Iec6205621Client
except ImportError:
    Iec6205621Client = None

RESULTS = []


def check(name, ok, detail=''):
    RESULTS.append((name, ok))
    print('%s  %s%s' % ('通过' if ok else '失败', name, ('   ' + detail) if detail and not ok else ''))


class Sim:
    """在本进程内启动一个模拟器。"""

    def __init__(self, cfg, kind='tcp', **kw):
        self.events = []
        self.lock = threading.Lock()
        self.engine = mc.MeterEngine(cfg, self._emit)
        if kind == 'tcp':
            self.link = mc.TcpServerLink(self.engine, self._emit, '127.0.0.1', 0)
        elif kind == 'udp':
            self.link = mc.UdpLink(self.engine, self._emit, '127.0.0.1', 0)
        else:
            self.link = mc.SerialLink(self.engine, self._emit, kw['port'], kw.get('baud', 300))
        self.link.open()
        sock = getattr(self.link, 'srv', None) or getattr(self.link, 'sock', None)
        self.port = sock.getsockname()[1] if sock else None
        self.link.start()
        time.sleep(0.2)

    def _emit(self, ev):
        with self.lock:
            self.events.append(ev)

    def has(self, kind, text):
        with self.lock:
            return any(ev['kind'] == kind and text in (ev['text'] or '') for ev in self.events)

    def stop(self):
        self.link.stop()
        self.link.join(2)


class RawTcp:
    def __init__(self, port, udp=False):
        self.udp = udp
        if udp:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.addr = ('127.0.0.1', port)
        else:
            self.s = socket.create_connection(('127.0.0.1', port))
        self.s.settimeout(0.1)
        time.sleep(0.1)

    def send(self, data):
        if self.udp:
            self.s.sendto(data, self.addr)
        else:
            self.s.sendall(data)

    def recv_until(self, pred, timeout=3.0):
        buf = b''
        end = time.time() + timeout
        while time.time() < end:
            try:
                buf += self.s.recv(4096)
            except socket.timeout:
                pass
            if pred(buf):
                break
        return buf

    def close(self):
        self.s.close()


def ends_with_frame(b):
    return len(b) >= 2 and b[-2] in (mc.ETX, mc.EOT)


def bcc_ok(msg):
    i = msg.find(bytes([mc.STX]))
    j = msg.find(bytes([mc.SOH]))
    start = j if j != -1 and (i == -1 or j < i) else i
    return start != -1 and mc.calc_bcc(msg[start + 1:-1]) == msg[-1]


def pwitab_send_password(cli, password):
    """pwitab 0.0.2 的 send_password() 有 bug（DataSet 缺 address 参数），这里用它的报文类手工发 P1。"""
    from iec62056_21 import messages
    ds = messages.DataSet(address='', value=password)
    cli.transport.send(messages.CommandMessage(command='P', command_type=1, data_set=ds).to_bytes())


def cfg(**kw):
    kw.setdefault('reply_delay_ms', 50)
    return replace(mc.MeterConfig(), **kw)


# ---------------------------------------------------------------- pwitab 用例
def test_pwitab():
    if Iec6205621Client is None:
        print('跳过  pwitab 用例（未安装 iec62056-21）')
        return
    sim = Sim(cfg(mode='C'))
    try:
        cli = Iec6205621Client.with_tcp_transport(address=('127.0.0.1', sim.port))
        cli.transport.timeout = 5
        cli.connect()
        resp = cli.standard_readout()
        vals = {d.address: d.value for d in resp.data}
        check('pwitab Mode C 标准读数', vals.get('1.8.0') == '012345.678', repr(vals))
        cli.disconnect()

        time.sleep(0.3)
        cli = Iec6205621Client.with_tcp_transport(address=('127.0.0.1', sim.port), password='00000000')
        cli.transport.timeout = 5
        cli.connect()
        p0 = cli.access_programming_mode()
        check('pwitab 进入编程模式收到 P0', p0.command == 'P' and p0.command_type == 0)
        pwitab_send_password(cli, '00000000')
        v = cli.read_single_value('32.7.0')
        check('pwitab 编程模式 R1 读值', v.value == '230.5' and v.unit == 'V', repr(v))
        cli.write_single_value('C.1.0', '999')
        check('pwitab 编程模式 W1 写值', sim.has('items', 'C.1.0 = 999'))
        cli.send_break()
        time.sleep(0.3)
        check('收到 B0 后会话结束', sim.has('info', '收到结束命令 B0'))
        cli.disconnect()

        time.sleep(0.3)
        cli = Iec6205621Client.with_tcp_transport(address=('127.0.0.1', sim.port), password='bad')
        cli.transport.timeout = 5
        cli.connect()
        cli.access_programming_mode()
        pwitab_send_password(cli, 'bad')
        time.sleep(0.5)
        check('口令错误被指出', sim.has('error', '口令错误'))
        cli.disconnect()
    except Exception as e:
        check('pwitab 用例运行', False, repr(e))
    finally:
        sim.stop()


# ---------------------------------------------------------------- 各模式
def test_modes():
    for mode, bchar in (('A', 'J'), ('B', 'E')):
        sim = Sim(cfg(mode=mode, baud_char=bchar))
        m = RawTcp(sim.port)
        m.send(b'/?!\r\n')
        out = m.recv_until(ends_with_frame)
        check('Mode %s：请求后直接返回标识 + 数据' % mode,
              out.startswith(('/INH%s' % bchar).encode()) and bcc_ok(out) and b'1.8.0(012345.678*kWh)' in out,
              mc.readable(out))
        m.close()
        sim.stop()

    sim = Sim(cfg(mode='E'))
    m = RawTcp(sim.port)
    m.send(b'/?!\r\n')
    ident = m.recv_until(lambda b: b.endswith(b'\r\n'))
    check('Mode E：标识带 \\2', ident.startswith(b'/INH5\\2'), mc.readable(ident))
    m.send(b'\x06252\r\n')
    time.sleep(0.3)
    m.send(bytes.fromhex('7EA00A000200232193BF5C7E'))
    time.sleep(0.3)
    check('Mode E：ACK 2 后进入 HDLC 并记录帧', sim.has('info', 'HDLC 数据'))
    m.close()
    sim.stop()

    sim = Sim(cfg(mode='C'))
    m = RawTcp(sim.port)
    m.send(b'/?!\r\n')
    m.recv_until(lambda b: b.endswith(b'\r\n'))
    m.send(b'\x06050\r\n')
    out = m.recv_until(ends_with_frame)
    check('Mode C 原始报文读数 + BCC 正确', bcc_ok(out), mc.readable(out))
    m.close()
    sim.stop()

    sim = Sim(cfg(mode='D', baud_char='3'))
    m = RawTcp(sim.port)
    time.sleep(0.2)
    sim.engine.push()
    out = m.recv_until(ends_with_frame)
    check('Mode D：主动推送标识 + 数据', out.startswith(b'/INH3') and bcc_ok(out), mc.readable(out))
    m.close()
    sim.stop()

    sim = Sim(cfg(mode='C'), kind='udp')
    m = RawTcp(sim.port, udp=True)
    m.send(b'/?!\r\n')
    m.recv_until(lambda b: b.endswith(b'\r\n'))
    m.send(b'\x06050\r\n')
    out = m.recv_until(ends_with_frame)
    check('UDP：Mode C 完整读数', bcc_ok(out) and b'2.8.0' in out, mc.readable(out))
    m.close()
    sim.stop()


# ---------------------------------------------------------------- 诊断
def run_case(config, steps, wait):
    sim = Sim(config)
    m = RawTcp(sim.port)
    for s in steps:
        if isinstance(s, (int, float)):
            time.sleep(s)
        else:
            m.send(s)
            time.sleep(0.2)
    time.sleep(wait)
    m.close()
    sim.stop()
    return sim


def diag(name, config, steps, kind, text, wait=0.5):
    sim = run_case(config, steps, wait)
    ok = sim.has(kind, text)
    hint = any(ev['kind'] == 'hint' for ev in sim.events) if kind == 'error' else True
    check('诊断：' + name, ok and hint,
          ' | '.join(mc.format_event(e, False) for e in sim.events if e['kind'] in ('error', 'hint', 'warn')))
    return sim


def diag_cases():
    """(名称, 配置, 主站发送序列, 期望事件类型, 期望中文片段, 等待秒数)"""
    parity = bytes(b | 0x80 if bin(b).count('1') % 2 else b for b in b'/?!\r\n')  # 7E1 帧被按 8 位接收
    p1_bad = b'\x01P1\x02(00000000)\x03\x00'
    good_r1 = mc.frame_with_bcc(mc.SOH, b'R1\x029.9.9()\x03')
    good_p1 = mc.frame_with_bcc(mc.SOH, b'P1\x02(00000000)\x03')
    return [
        ('请求缺少 CRLF', cfg(), [b'/?!'], 'error', '缺少结尾的 <CR><LF>', 0.8),
        ('请求地址不一致', cfg(address='12345678'), [b'/?999!\r\n'], 'error', '不一致', 0.5),
        ('请求格式错误（缺 ?）', cfg(), [b'/12!\r\n'], 'error', '请求报文格式错误', 0.5),
        ('ACK 超时', replace(cfg(), ack_timeout_s=1.0), [b'/?!\r\n'], 'error', '没有收到主站的 ACK', 1.5),
        ('ACK 不完整', replace(cfg(), ack_timeout_s=1.0), [b'/?!\r\n', b'\x06'], 'error', '不完整', 1.5),
        ('ACK 波特率字符无效', cfg(), [b'/?!\r\n', b'\x06090\r\n'], 'error', '无效', 0.5),
        ('ACK 波特率高于提议', cfg(baud_char='3'), [b'/?!\r\n', b'\x06050\r\n'], 'error', '高于', 0.5),
        ('Mode C 收到 HDLC 请求', cfg(), [b'/?!\r\n', b'\x06252\r\n'], 'error', 'HDLC', 0.5),
        ('未发 ACK 就重发请求', cfg(), [b'/?!\r\n', 0.3, b'/?!\r\n'], 'error', '重新发送了请求', 0.5),
        ('空闲时收到 ACK', cfg(), [b'\x06050\r\n'], 'error', '没有进行中的会话', 0.5),
        ('7E1 被按 8 位接收', cfg(), [parity], 'error', '最高位被置位', 0.5),
        ('乱码（波特率不一致）', cfg(), [b'\x00\xff\x80\xfe'], 'error', '无法识别', 0.5),
        ('编程模式 BCC 错误', cfg(), [b'/?!\r\n', b'\x06051\r\n', 0.3, p1_bad], 'error', 'BCC 校验错误', 0.5),
        ('读取不存在的地址', cfg(), [b'/?!\r\n', b'\x06051\r\n', 0.3, good_p1, good_r1], 'error', '不存在', 0.5),
        ('未登录就读取', cfg(), [b'/?!\r\n', b'\x06051\r\n', 0.3, good_r1], 'error', '未通过口令验证', 0.5),
        ('Mode D 收到请求', cfg(mode='D', baud_char='3'), [b'/?!\r\n'], 'error', 'Mode D', 0.5),
    ]


def test_diagnostics():
    for name, config, steps, kind, text, wait in diag_cases():
        diag(name, config, steps, kind, text, wait)


# ---------------------------------------------------------------- 日志导出
def test_export(tmpdir):
    import os
    sim = diag('（导出用）', cfg(), [b'/?!'], 'error', 'CR', wait=0.8)
    txt = os.path.join(tmpdir, 'export_test.txt')
    csv_path = os.path.join(tmpdir, 'export_test.csv')
    mc.save_events(txt, sim.events)
    mc.save_events(csv_path, sim.events)
    with open(txt, encoding='utf-8') as f:
        t = f.read()
    with open(csv_path, encoding='utf-8-sig') as f:
        c = f.read()
    check('导出 TXT 含报文与 HEX', 'HEX 2F 3F 21' in t and '建议' in t)
    check('导出 CSV 含表头', c.startswith('时间,类型'))


# ---------------------------------------------------------------- 多语言 / 帮助 / 更新
SOURCES = ['meter_core.py', '电表模拟器.py', 'updater.py']
PLACEHOLDER = re.compile(r'%[-#0 +]*\d*(?:\.\d+)?[sdifxXc%]')
CJK = re.compile(r'[一-鿿]')


def str_value(node):
    """字符串字面量的值（Python 3.7 的 ast.Str 与 3.8+ 的 ast.Constant 都支持），否则 None。"""
    value = getattr(node, 'value', getattr(node, 's', None))
    return value if isinstance(value, str) else None


def i18n_keys(path):
    tree = ast.parse(open(path, encoding='utf-8').read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ('_', 'N_'):
            for a in node.args:
                if str_value(a) is not None:
                    yield str_value(a)


def test_i18n():
    from translations import T
    here = os.path.dirname(os.path.abspath(__file__))
    keys = set()
    for src in SOURCES:
        keys.update(i18n_keys(os.path.join(here, src)))
    missing = sorted(k for k in keys if k not in T)
    check('多语言：每条界面/日志文字都有英文和西班牙文译文', not missing, repr(missing[:5]))
    bad = [k for k, (en, es) in T.items()
           if not (PLACEHOLDER.findall(k) == PLACEHOLDER.findall(en) == PLACEHOLDER.findall(es))]
    check('多语言：译文占位符与原文一致', not bad, repr(bad[:5]))
    tree = ast.parse(open(os.path.join(here, 'translations.py'), encoding='utf-8').read())
    table = next(n.value for n in tree.body if isinstance(n, ast.Assign))
    dup = [k for k, c in Counter(str_value(k) for k in table.keys).items() if c > 1]
    check('多语言：译文表没有重复的 key', not dup, repr(dup))
    leftover = [k for k, (en, es) in T.items() if CJK.search(en + es)]
    check('多语言：译文里没有残留中文', not leftover, repr(leftover[:5]))

    # 英文 / 西班牙文下把所有诊断用例跑一遍：必须给出问题 + 建议，且日志里没有中文
    for lang in ('en', 'es'):
        i18n.set_lang(lang)
        fails = []
        try:
            for name, config, steps, kind, _text, wait in diag_cases():
                sim = run_case(config, steps, wait)
                lines = [mc.format_event(e) for e in sim.events]
                has_err = any(e['kind'] == 'error' for e in sim.events)
                has_hint = any(e['kind'] == 'hint' for e in sim.events)
                cjk = [ln for ln in lines if CJK.search(ln)]
                if not (has_err and has_hint) or cjk:
                    fails.append('%s: %s' % (name, cjk[:1] or 'no problem/suggestion'))
            sim = Sim(cfg(mode='C'))
            m = RawTcp(sim.port)
            m.send(b'/?!\r\n')
            m.recv_until(lambda b: b.endswith(b'\r\n'))
            m.send(b'\x06050\r\n')
            m.recv_until(ends_with_frame)
            m.close()
            sim.stop()
            lines = [mc.format_event(e) for e in sim.events]
            if any(CJK.search(ln) for ln in lines):
                fails.append('readout: ' + next(ln for ln in lines if CJK.search(ln)))
        finally:
            i18n.set_lang('zh')
        check('多语言：%s 下 16 种诊断和正常读数的日志完整且无中文' % lang, not fails, ' | '.join(fails[:3]))

    import help_content
    sections = {lang: help_content.get(lang).count('\n## ') for lang in i18n.LANGS}
    check('使用方法：三种语言都有且章节数一致', len(set(sections.values())) == 1 and sections['en'] >= 6,
          repr(sections))


def test_updater():
    import json
    from http.server import BaseHTTPRequestHandler, HTTPServer
    import updater

    check('更新：版本比较', updater.is_newer('1.0.10', '1.0.9') and not updater.is_newer('v1.0.0', '1.0.0')
          and updater.is_newer('v2.0', '1.9.9'))
    try:
        updater.check_latest(repo='')
        check('更新：未配置仓库时给出提示', False)
    except updater.UpdateError as e:
        check('更新：未配置仓库时给出提示', 'GITHUB_REPO' in str(e))

    tag = updater.platform_tag()
    release = {'tag_name': 'v9.9.9', 'html_url': 'https://example.invalid/release', 'body': 'notes',
               'assets': [{'name': 'MeterSimulator-9.9.9-%s.bin' % t,
                           'browser_download_url': 'https://example.invalid/%s' % t}
                          for t in ('windows', 'macos-arm64', 'macos-x86_64', 'linux')]}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            ok = self.path == '/repos/demo/sim/releases/latest'
            body = json.dumps(release if ok else {'message': 'Not Found'}).encode()
            self.send_response(200 if ok else 404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            pass

    srv = HTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    api = 'http://127.0.0.1:%d' % srv.server_address[1]
    try:
        r = updater.check_latest(repo='demo/sim', api=api)
        check('更新：读取最新版本并选中本平台安装包',
              r['version'] == '9.9.9' and r['download'] == 'https://example.invalid/' + tag and r['notes'] == 'notes',
              repr(r))
        try:
            updater.check_latest(repo='demo/none', api=api)
            check('更新：仓库没有发布时给出提示', False)
        except updater.UpdateError as e:
            check('更新：仓库没有发布时给出提示', 'demo/none' in str(e))
    finally:
        srv.shutdown()


# ---------------------------------------------------------------- 串口
def test_serial(port_sim, port_master):
    if Iec6205621Client is None:
        print('跳过  串口用例（未安装 iec62056-21）')
        return
    # pwitab 发完 ACK 后约 0.75 秒才切速，所以响应延时要更长
    sim = Sim(cfg(mode='C', reply_delay_ms=1000), kind='serial', port=port_sim, baud=300)
    try:
        cli = Iec6205621Client.with_serial_transport(port=port_master)
        cli.transport.timeout = 6
        cli.connect()
        resp = cli.standard_readout()
        vals = {d.address: d.value for d in resp.data}
        check('串口：pwitab 300→9600 读数', vals.get('1.8.0') == '012345.678', repr(vals))
        time.sleep(1.0)  # 等模拟器发完数据后恢复初始波特率
        check('串口：模拟器切速并恢复', sim.has('stage', '300 → 9600') and sim.has('info', '恢复初始波特率'))
        cli.disconnect()
    except Exception as e:
        check('串口用例运行', False, repr(e))
    finally:
        sim.stop()


def main():
    import tempfile
    args = sys.argv[1:]
    if args[:1] == ['--serial'] and len(args) >= 3:
        test_serial(args[1], args[2])
    else:
        test_pwitab()
        test_modes()
        test_diagnostics()
        test_export(tempfile.gettempdir())
        test_i18n()
        test_updater()
    failed = [n for n, ok in RESULTS if not ok]
    print('\n共 %d 项，通过 %d，失败 %d' % (len(RESULTS), len(RESULTS) - len(failed), len(failed)))
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
