#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IEC 62056-21 电表模拟器（GUI）

- 模拟电表（从站），支持 Mode A / B / C / D / E
- 连接方式：串口 / TCP 服务端 / TCP 客户端 / UDP
- 显示每次会话的连接过程；记录收发日志并可导出（TXT / CSV）
- 主站报文有问题时，日志里指出问题并给出正确写法
- 界面语言：English（默认）/ 简体中文 / Español；内置使用方法、关于、版本更新检测

依赖：Python 3.7+，pip install pyserial（只用网络模式可不装）
运行：python3 电表模拟器.py      （Windows：py 电表模拟器.py）
"""

import json
import os
import platform
import queue
import subprocess
import sys
import threading
import time
import tkinter as tk
import webbrowser
from tkinter import ttk, messagebox, filedialog
from tkinter import font as tkfont

import app_info
import help_content
import i18n
import meter_core as mc
import updater
from i18n import _, N_

TRANSPORTS = [('serial', N_('串口')), ('tcp_server', N_('TCP 服务端')),
              ('tcp_client', N_('TCP 客户端')), ('udp', N_('UDP'))]
HOST_LABEL = {'tcp_server': N_('监听地址'), 'tcp_client': N_('主站地址'), 'udp': N_('本地地址')}
STEP_STYLE = {  # 状态: (背景, 文字, 标记)
    'idle': ('#ECEFF1', '#78909C', ''),
    'active': ('#FFF3C4', '#E65100', ' …'),
    'ok': ('#DCF5E3', '#1B5E20', ' ✓'),
    'fail': ('#FFDCDC', '#B71C1C', ' ✗'),
    'skip': ('#F2F2F2', '#9E9E9E', ' –'),
}
TAG_COLORS = {'rx': '#1565C0', 'tx': '#2E7D32', 'info': '#546E7A', 'stage': '#6A1B9A', 'warn': '#E65100',
              'error': '#C62828', 'hint': '#AD1457', 'link': '#00838F', 'session': '#212121', 'items': '#546E7A'}
PROBLEM_KINDS = ('error', 'hint', 'warn', 'session', 'link')
BAUDS = ['300', '600', '1200', '2400', '4800', '9600', '19200']
FAULT_KEYS = list(mc.FAULTS)
# 记住的界面设置：变量名 → 属性名
REMEMBER = ['v_port', 'v_baud', 'v_bits', 'v_parity', 'v_stop', 'v_host', 'v_netport', 'v_target',
            'v_mfr', 'v_ident', 'v_addr', 'v_pw', 'v_delay', 'v_ack_to', 'v_sess_to', 'v_strip', 'v_push',
            'v_hex', 'v_only_problem', 'v_autosave']


# ---------------------------------------------------------------- 路径与设置
def app_dir():
    return getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))


def find_icon():
    for p in (os.path.join(app_dir(), 'icon.png'), os.path.join(app_dir(), 'packaging', 'icon.png')):
        if os.path.exists(p):
            return p
    return None


def log_folder():
    # 打包成程序后，程序目录可能只读或是临时目录，日志改存到“文稿/MeterSimulator Logs”
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.expanduser('~'), 'Documents', 'MeterSimulator Logs')
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')


def settings_path():
    if sys.platform == 'win32':
        base = os.environ.get('APPDATA') or os.path.expanduser('~')
    elif sys.platform == 'darwin':
        base = os.path.expanduser('~/Library/Application Support')
    else:
        base = os.environ.get('XDG_CONFIG_HOME') or os.path.expanduser('~/.config')
    return os.path.join(base, 'MeterSimulator', 'settings.json')


def load_settings():
    try:
        with open(settings_path(), encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_settings(data):
    try:
        os.makedirs(os.path.dirname(settings_path()), exist_ok=True)
        with open(settings_path(), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
    except OSError:
        pass


def open_path(path):
    if sys.platform == 'win32':
        os.startfile(path)
    elif sys.platform == 'darwin':
        subprocess.Popen(['open', path])
    else:
        subprocess.Popen(['xdg-open', path])


# ---------------------------------------------------------------- 主窗口
class App:
    def __init__(self, root, settings, state=None, events=None):
        self.root = root
        self.settings = settings
        root.title(_('IEC 62056-21 电表模拟器') + ' v' + app_info.VERSION)
        self.q = queue.Queue()
        self.events = []
        self.engine = None
        self.link = None
        self.autosave = None
        self.problem_count = 0
        self.help_win = None

        base = tkfont.nametofont('TkFixedFont').copy()
        base.configure(size=max(10, abs(base.cget('size'))))
        self.mono = base

        self._build_menu()
        self._build_connection()
        self._build_meter()
        self._build_stepper_frame()
        self._build_bottom()
        self._on_transport()
        self._on_mode(init=True)
        self._refresh_ports(quiet=True)
        self._restore(state if state is not None else settings.get('last', {}))
        for ev in events or []:
            self.q.put(ev)

        root.protocol('WM_DELETE_WINDOW', self._on_close)
        self._after_id = root.after(80, self._drain)
        if state is None and settings.get('auto_update', True) and app_info.GITHUB_REPO:
            root.after(3000, lambda: self._check_update(manual=False))

    # ================================================================ 菜单
    def _build_menu(self):
        bar = tk.Menu(self.root)
        if sys.platform == 'darwin':  # macOS：“关于”放到应用菜单
            appmenu = tk.Menu(bar, name='apple', tearoff=0)
            appmenu.add_command(label=_('关于'), command=self._about)
            bar.add_cascade(menu=appmenu)
            self.root.createcommand('tkAboutDialog', self._about)

        m_file = tk.Menu(bar, tearoff=0)
        m_file.add_command(label=_('导出日志…'), command=self._export)
        m_file.add_command(label=_('打开日志文件夹'), command=self._open_log_folder)
        m_file.add_separator()
        m_file.add_command(label=_('退出'), command=self._on_close)
        bar.add_cascade(label=_('文件'), menu=m_file)

        m_lang = tk.Menu(bar, tearoff=0)
        self.v_lang = tk.StringVar(value=i18n.get_lang())
        for code, name in i18n.LANGS.items():
            m_lang.add_radiobutton(label=name, value=code, variable=self.v_lang,
                                   command=lambda c=code: self._set_language(c))
        lang_title = _('语言')
        bar.add_cascade(label=lang_title if i18n.get_lang() == 'en' else lang_title + ' (Language)', menu=m_lang)

        m_help = tk.Menu(bar, tearoff=0, name='help' if sys.platform == 'darwin' else None)
        m_help.add_command(label=_('使用方法'), accelerator='F1', command=self._show_help)
        m_help.add_separator()
        m_help.add_command(label=_('检查更新…'), command=lambda: self._check_update(manual=True))
        self.v_auto_update = tk.BooleanVar(value=self.settings.get('auto_update', True))
        m_help.add_checkbutton(label=_('启动时自动检查更新'), variable=self.v_auto_update,
                               command=self._toggle_auto_update)
        if sys.platform != 'darwin':
            m_help.add_separator()
            m_help.add_command(label=_('关于'), command=self._about)
        bar.add_cascade(label=_('帮助'), menu=m_help)
        self.root.config(menu=bar)
        self.root.bind('<F1>', lambda e: self._show_help())

    # ================================================================ 界面
    def _build_connection(self):
        f = ttk.LabelFrame(self.root, text=_('连接方式'))
        f.pack(fill='x', padx=8, pady=(8, 4))
        pad = dict(padx=4, pady=3)

        top = ttk.Frame(f)
        top.pack(fill='x')
        ttk.Label(top, text=_('方式')).pack(side='left', **pad)
        self.cb_transport = ttk.Combobox(top, values=[_(t[1]) for t in TRANSPORTS], state='readonly', width=13)
        self.cb_transport.current(0)
        self.cb_transport.pack(side='left', **pad)
        self.cb_transport.bind('<<ComboboxSelected>>', lambda e: self._on_transport())
        self.btn_start = ttk.Button(top, text=_('▶ 启动'), command=self._toggle)
        self.btn_start.pack(side='left', padx=10)
        self.v_link = tk.StringVar(value=_('未启动'))
        ttk.Label(top, textvariable=self.v_link, foreground='#00838F').pack(side='left', fill='x', expand=True)

        # 第二行：串口参数 / 网络参数（二选一）
        self.f_params = ttk.Frame(f)
        self.f_params.pack(fill='x', pady=(0, 4))
        self.f_serial = ttk.Frame(self.f_params)
        self.v_port = tk.StringVar()
        self.v_baud = tk.StringVar(value='300')
        self.v_bits = tk.StringVar(value='7')
        self.v_parity = tk.StringVar(value='E')
        self.v_stop = tk.StringVar(value='1')
        ttk.Label(self.f_serial, text=_('端口')).pack(side='left', padx=(4, 2))
        self.cb_port = ttk.Combobox(self.f_serial, textvariable=self.v_port, width=24)
        self.cb_port.pack(side='left')
        ttk.Button(self.f_serial, text=_('刷新'), command=self._refresh_ports).pack(side='left', padx=2)
        for label, var, vals, w in ((_('初始波特率'), self.v_baud, BAUDS, 7), (_('数据位'), self.v_bits, ['7', '8'], 3),
                                    (_('校验'), self.v_parity, ['E', 'N', 'O'], 3),
                                    (_('停止位'), self.v_stop, ['1', '2'], 3)):
            ttk.Label(self.f_serial, text=label).pack(side='left', padx=(8, 2))
            ttk.Combobox(self.f_serial, textvariable=var, values=vals, width=w).pack(side='left')

        # 网络参数
        self.f_net = ttk.Frame(self.f_params)
        self.v_host = tk.StringVar(value='0.0.0.0')
        self.v_netport = tk.StringVar(value='7000')
        self.v_target = tk.StringVar(value='')
        self.lbl_host = ttk.Label(self.f_net, text=_('监听地址'))
        self.lbl_host.pack(side='left', padx=(4, 2))
        ttk.Entry(self.f_net, textvariable=self.v_host, width=16).pack(side='left')
        ttk.Label(self.f_net, text=_('端口')).pack(side='left', padx=(8, 2))
        ttk.Entry(self.f_net, textvariable=self.v_netport, width=7).pack(side='left')
        self.lbl_target = ttk.Label(self.f_net, text=_('推送目标(可选) IP:端口'))
        self.ent_target = ttk.Entry(self.f_net, textvariable=self.v_target, width=20)

    def _build_meter(self):
        f = ttk.LabelFrame(self.root, text=_('电表设置'))
        f.pack(fill='x', padx=8, pady=4)
        pad = dict(padx=4, pady=3, sticky='w')

        r0 = ttk.Frame(f)
        r0.grid(row=0, column=0, columnspan=12, sticky='we')
        ttk.Label(r0, text=_('协议模式')).pack(side='left', padx=4)
        self.v_mode = tk.StringVar(value='C')
        cb = ttk.Combobox(r0, textvariable=self.v_mode, values=list('ABCDE'), state='readonly', width=4)
        cb.pack(side='left')
        cb.bind('<<ComboboxSelected>>', lambda e: self._on_mode())
        self.v_mode_desc = tk.StringVar()
        ttk.Label(r0, textvariable=self.v_mode_desc, foreground='#546E7A').pack(side='left', padx=10)

        self.v_mfr = tk.StringVar(value='INH')
        self.v_bchar = tk.StringVar(value='5')
        self.v_ident = tk.StringVar(value='MG301-SIM')
        self.v_addr = tk.StringVar(value='')
        self.v_pw = tk.StringVar(value='00000000')
        self.v_delay = tk.StringVar(value='200')
        self.v_ack_to = tk.StringVar(value='3')
        self.v_sess_to = tk.StringVar(value='60')
        self.v_strip = tk.BooleanVar(value=False)
        self.v_push = tk.StringVar(value='0')

        def field(row, col, label, var, width):
            ttk.Label(f, text=label).grid(row=row, column=col, **pad)
            e = ttk.Entry(f, textvariable=var, width=width)
            e.grid(row=row, column=col + 1, **pad)
            return e

        field(1, 0, _('厂商ID(3位)'), self.v_mfr, 6)
        ttk.Label(f, text=_('波特率字符')).grid(row=1, column=2, **pad)
        self.cb_bchar = ttk.Combobox(f, textvariable=self.v_bchar, width=4)
        self.cb_bchar.grid(row=1, column=3, **pad)
        field(1, 4, _('标识串'), self.v_ident, 18)
        field(1, 6, _('表地址(空=任意)'), self.v_addr, 16)

        field(2, 0, _('响应延时 ms'), self.v_delay, 6)
        field(2, 2, _('ACK 超时 s'), self.v_ack_to, 5)
        field(2, 4, _('编程会话超时 s'), self.v_sess_to, 6)
        field(2, 6, _('编程口令(空=不校验)'), self.v_pw, 16)

        ttk.Label(f, text=_('故障注入')).grid(row=3, column=0, **pad)
        self.cb_fault = ttk.Combobox(f, values=[_(mc.FAULTS[k]) for k in FAULT_KEYS], state='readonly', width=24)
        self.cb_fault.current(0)
        self.cb_fault.grid(row=3, column=1, columnspan=3, **pad)
        ttk.Checkbutton(f, text=_('接收时去掉最高位(网络透传 7E1)'), variable=self.v_strip).grid(
            row=3, column=4, columnspan=4, **pad)

        r4 = ttk.Frame(f)
        r4.grid(row=4, column=0, columnspan=12, sticky='we', pady=(2, 0))
        ttk.Label(r4, text=_('Mode D 推送间隔 s (0=手动)')).pack(side='left', padx=4)
        self.ent_push = ttk.Entry(r4, textvariable=self.v_push, width=6)
        self.ent_push.pack(side='left')
        self.btn_push = ttk.Button(r4, text=_('立即推送'), command=self._push)
        self.btn_push.pack(side='left', padx=6)
        ttk.Button(r4, text=_('应用设置'), command=self._apply).pack(side='left', padx=(24, 6))
        ttk.Label(f, text=_('运行中修改设置后点「应用设置」生效；串口参数需重新启动'),
                  foreground='#90A4AE').grid(row=5, column=0, columnspan=12, sticky='w', padx=4, pady=(0, 4))

    def _build_stepper_frame(self):
        f = ttk.LabelFrame(self.root, text=_('连接过程'))
        f.pack(fill='x', padx=8, pady=4)
        self.step_frame = tk.Frame(f)
        self.step_frame.pack(fill='x', padx=6, pady=6)
        self.v_step_note = tk.StringVar(value='')
        tk.Label(f, textvariable=self.v_step_note, fg='#B71C1C', anchor='w', justify='left',
                 wraplength=1100).pack(fill='x', padx=8, pady=(0, 4))

    def _build_stepper(self):
        for w in self.step_frame.winfo_children():
            w.destroy()
        self.v_session = tk.StringVar(value=_('会话 —'))
        tk.Label(self.step_frame, textvariable=self.v_session, width=12, anchor='w').pack(side='left')
        self.steps = {}
        for i, (key, label) in enumerate(mc.STAGES[self.v_mode.get()]):
            if i:
                tk.Label(self.step_frame, text='→', fg='#90A4AE').pack(side='left')
            w = tk.Label(self.step_frame, text=_(label), padx=12, pady=5, relief='groove', bd=1)
            w.pack(side='left', padx=3)
            self.steps[key] = (w, _(label))
        self._reset_steps()

    def _reset_steps(self):
        for key in self.steps:
            self._set_step(key, 'idle')
        self.v_step_note.set('')

    def _set_step(self, key, status, text=''):
        if key not in self.steps:
            return
        w, label = self.steps[key]
        bg, fg, mark = STEP_STYLE.get(status, STEP_STYLE['idle'])
        w.config(bg=bg, fg=fg, text=label + mark + (('\n' + text) if text else ''))

    def _build_bottom(self):
        pw = ttk.PanedWindow(self.root, orient='horizontal')
        pw.pack(fill='both', expand=True, padx=8, pady=(4, 0))

        # 数据项
        fd = ttk.LabelFrame(pw, text=_('数据项（双击编辑）'))
        self.tree = ttk.Treeview(fd, columns=('addr', 'value', 'unit'), show='headings', height=10)
        for col, text, w in (('addr', _('地址 / OBIS'), 130), ('value', _('值'), 110), ('unit', _('单位'), 50)):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=w, stretch=(col != 'unit'))
        self.tree.pack(fill='both', expand=True, padx=4, pady=4)
        self.tree.bind('<Double-1>', self._edit_cell)
        fb = ttk.Frame(fd)
        fb.pack(fill='x', padx=4, pady=(0, 4))
        ttk.Button(fb, text=_('添加'), command=self._add_row).pack(side='left')
        ttk.Button(fb, text=_('删除'), command=self._del_row).pack(side='left', padx=4)
        ttk.Button(fb, text=_('恢复默认'), command=self._default_rows).pack(side='left')
        self._set_items(mc.DEFAULT_ITEMS)
        pw.add(fd, weight=1)

        # 日志
        fl = ttk.LabelFrame(pw, text=_('交互日志'))
        bar = ttk.Frame(fl)
        bar.pack(fill='x', padx=4, pady=(4, 0))
        self.v_hex = tk.BooleanVar(value=True)
        self.v_only_problem = tk.BooleanVar(value=False)
        self.v_autosave = tk.BooleanVar(value=False)
        ttk.Checkbutton(bar, text=_('显示 HEX'), variable=self.v_hex, command=self._rerender).pack(side='left')
        ttk.Checkbutton(bar, text=_('只看问题'), variable=self.v_only_problem, command=self._rerender).pack(
            side='left', padx=8)
        ttk.Checkbutton(bar, text=_('自动保存日志'), variable=self.v_autosave,
                        command=self._toggle_autosave).pack(side='left')
        ttk.Button(bar, text=_('导出日志…'), command=self._export).pack(side='right')
        ttk.Button(bar, text=_('清空'), command=self._clear_log).pack(side='right', padx=4)

        body = ttk.Frame(fl)
        body.pack(fill='both', expand=True, padx=4, pady=4)
        self.txt = tk.Text(body, wrap='none', font=self.mono, height=18, undo=False)
        ys = ttk.Scrollbar(body, orient='vertical', command=self.txt.yview)
        xs = ttk.Scrollbar(body, orient='horizontal', command=self.txt.xview)
        self.txt.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)
        self.txt.grid(row=0, column=0, sticky='nsew')
        ys.grid(row=0, column=1, sticky='ns')
        xs.grid(row=1, column=0, sticky='ew')
        body.rowconfigure(0, weight=1)
        body.columnconfigure(0, weight=1)
        bold = self.mono.copy()
        bold.configure(weight='bold')
        for kind, color in TAG_COLORS.items():
            self.txt.tag_config(kind, foreground=color)
        self.txt.tag_config('error', font=bold)
        self.txt.tag_config('session', font=bold, background='#F5F5F5')
        self.txt.config(state='disabled')  # 只读，仍可选中复制
        pw.add(fl, weight=3)

        self.v_status = tk.StringVar(value='')
        ttk.Label(self.root, textvariable=self.v_status, foreground='#607D8B', anchor='w').pack(
            fill='x', padx=10, pady=(2, 6))
        self._update_status()

    # ================================================================ 交互
    def _transport(self):
        return TRANSPORTS[max(0, self.cb_transport.current())][0]

    def _on_transport(self):
        t = self._transport()
        if t == 'serial':
            self.f_net.pack_forget()
            self.f_serial.pack(side='left')
        else:
            self.f_serial.pack_forget()
            self.f_net.pack(side='left')
            self.lbl_host.config(text=_(HOST_LABEL[t]))
            if t == 'tcp_client' and self.v_host.get() == '0.0.0.0':
                self.v_host.set('127.0.0.1')
            elif t != 'tcp_client' and self.v_host.get() == '127.0.0.1':
                self.v_host.set('0.0.0.0')
            if t == 'udp':
                self.lbl_target.pack(side='left', padx=(8, 2))
                self.ent_target.pack(side='left')
            else:
                self.lbl_target.pack_forget()
                self.ent_target.pack_forget()

    def _on_mode(self, init=False):
        mode = self.v_mode.get()
        baud, bchar = mc.MODE_DEFAULTS[mode]
        self.v_mode_desc.set(_(mc.MODE_INFO[mode]))
        self.cb_bchar['values'] = mc.MODE_BAUD_CHARS[mode]
        self.v_bchar.set(bchar)
        if not self.link:
            self.v_baud.set(str(baud))
        state = 'normal' if mode == 'D' else 'disabled'
        self.ent_push.config(state=state)
        self.btn_push.config(state=state)
        self._build_stepper()
        if self.link and not init:
            self._apply()
            if self._transport() == 'serial' and int(self.v_baud.get()) != baud:
                self._log_local('warn', _('Mode %s 的标准初始波特率是 %d，当前串口为 %s；如需修改请停止后重新启动')
                                % (mode, baud, self.v_baud.get()))

    def _refresh_ports(self, quiet=False):
        ports = mc.list_serial_ports()
        self.cb_port['values'] = ports
        if ports and self.v_port.get() not in ports:
            self.v_port.set(ports[0])
        if mc.serial is None and not quiet:
            self._log_local('warn', _('未安装 pyserial，串口不可用（pip install pyserial）；网络模式可正常使用'))

    def _read_config(self):
        mode = self.v_mode.get()
        cfg = mc.MeterConfig(
            mode=mode,
            manufacturer=(self.v_mfr.get().strip() or 'XXX')[:3],
            baud_char=(self.v_bchar.get().strip() or mc.MODE_DEFAULTS[mode][1])[0],
            identification=self.v_ident.get().strip(),
            address=self.v_addr.get().strip(),
            password=self.v_pw.get().strip(),
            reply_delay_ms=int(float(self.v_delay.get() or 0)),
            ack_timeout_s=float(self.v_ack_to.get() or 3),
            session_timeout_s=float(self.v_sess_to.get() or 60),
            strip_high_bit=self.v_strip.get(),
            push_interval_s=float(self.v_push.get() or 0),
            fault=FAULT_KEYS[max(0, self.cb_fault.current())],
            items=self._items(),
        )
        notes = []
        if len(self.v_mfr.get().strip()) != 3:
            notes.append(_('厂商ID应为 3 个字母'))
        if cfg.baud_char not in mc.MODE_BAUD_CHARS[mode] and mode != 'A':
            notes.append(_('波特率字符 "%s" 不符合 Mode %s 规定（可选 %s）')
                         % (cfg.baud_char, mode, '/'.join(mc.MODE_BAUD_CHARS[mode])))
        if mode == 'A' and (cfg.baud_char.isdigit() or cfg.baud_char in 'ABCDEFGHI/!'):
            notes.append(_('Mode A 的波特率字符不能是 0~9、A~I、/、!'))
        short = cfg.manufacturer[-1:].islower()
        lo = 20 if short else 200
        if not lo <= cfg.reply_delay_ms <= 1500:
            notes.append(_('响应延时 %d ms 超出标准范围 %d~1500 ms（厂商ID第3个字母%s写→最短 %d ms）')
                         % (cfg.reply_delay_ms, lo, _('小') if short else _('大'), lo))
        for n in notes:
            self._log_local('warn', _('设置提示：%s') % n)
        return cfg

    def _toggle(self):
        if self.link:
            self._stop()
        else:
            self._start()

    def _start(self):
        try:
            cfg = self._read_config()
        except ValueError as e:
            messagebox.showerror(_('设置有误'), _('请检查数字类设置：%s') % e)
            return
        emit = self.q.put
        engine = mc.MeterEngine(cfg, emit)
        t = self._transport()
        try:
            if t == 'serial':
                if not self.v_port.get().strip():
                    messagebox.showwarning(_('提示'), _('请选择串口'))
                    return
                link = mc.SerialLink(engine, emit, self.v_port.get().strip(), int(self.v_baud.get()),
                                     int(self.v_bits.get()), self.v_parity.get(), int(self.v_stop.get()))
            else:
                host, port = self.v_host.get().strip(), int(self.v_netport.get())
                if t == 'tcp_server':
                    link = mc.TcpServerLink(engine, emit, host or '0.0.0.0', port)
                elif t == 'tcp_client':
                    link = mc.TcpClientLink(engine, emit, host or '127.0.0.1', port)
                else:
                    target = mc.split_hostport(self.v_target.get(), '127.0.0.1') if self.v_target.get().strip() else None
                    link = mc.UdpLink(engine, emit, host or '0.0.0.0', port, target)
            link.open()
        except Exception as e:
            messagebox.showerror(_('启动失败'), str(e))
            return
        self.engine, self.link = engine, link
        link.start()
        self.btn_start.config(text=_('■ 停止'))
        self._set_conn_state('disabled')
        self._reset_steps()
        if self.v_autosave.get():
            self._open_autosave()

    def _stop(self):
        if self.link:
            self.link.stop()
            self.link.join(1.5)
        self._on_stopped()

    def _on_stopped(self):
        self.link = None
        self.engine = None
        self.btn_start.config(text=_('▶ 启动'))
        self.v_link.set(_('未启动'))
        self._set_conn_state('normal')

    def fit_width(self):
        """按当前语言的内容宽度调整窗口（西班牙语等较长时自动加宽，最多到屏幕宽度）。"""
        self.root.update_idletasks()
        need = min(self.root.winfo_reqwidth() + 20, self.root.winfo_screenwidth() - 40)
        if self.root.winfo_width() < need:
            self.root.geometry('%dx%d' % (need, max(self.root.winfo_height(), 820)))
        self.root.minsize(min(need, 1000), 680)

    def _set_conn_state(self, state):
        self.cb_transport.config(state='readonly' if state == 'normal' else 'disabled')
        for frame in (self.f_serial, self.f_net):
            for w in frame.winfo_children():
                try:
                    w.config(state=state if not isinstance(w, ttk.Label) else 'normal')
                except tk.TclError:
                    pass

    def _apply(self):
        try:
            cfg = self._read_config()
        except ValueError as e:
            messagebox.showerror(_('设置有误'), str(e))
            return
        if self.engine:
            self.engine.update_config(cfg)
            self._log_local('info', _('已应用设置（Mode %s）') % cfg.mode)

    def _push(self):
        if self.engine:
            self._apply()
            self.engine.push()
        else:
            messagebox.showinfo(_('提示'), _('请先启动'))

    # ---- 数据项表
    def _items(self):
        return [tuple(str(x) for x in self.tree.item(i, 'values')) for i in self.tree.get_children()]

    def _set_items(self, items):
        self.tree.delete(*self.tree.get_children())
        for it in items:
            self.tree.insert('', 'end', values=tuple(it))

    def _add_row(self):
        self.tree.insert('', 'end', values=('1.8.0', '000000.000', 'kWh'))
        self._apply_if_running()

    def _del_row(self):
        for i in self.tree.selection():
            self.tree.delete(i)
        self._apply_if_running()

    def _default_rows(self):
        self._set_items(mc.DEFAULT_ITEMS)
        self._apply_if_running()

    def _apply_if_running(self):
        if self.engine:
            self._apply()

    def _edit_cell(self, event):
        item = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if not item or not col:
            return
        idx = int(col[1:]) - 1
        box = self.tree.bbox(item, col)
        if not box:
            return
        x, y, w, h = box
        ed = ttk.Entry(self.tree)
        ed.insert(0, self.tree.item(item, 'values')[idx])
        ed.select_range(0, 'end')
        ed.focus()
        ed.place(x=x, y=y, width=w, height=h)

        def commit(_e=None):
            vals = list(self.tree.item(item, 'values'))
            vals[idx] = ed.get().strip()
            self.tree.item(item, values=vals)
            ed.destroy()
            self._apply_if_running()

        ed.bind('<Return>', commit)
        ed.bind('<FocusOut>', commit)
        ed.bind('<Escape>', lambda e: ed.destroy())

    # ---- 记住 / 恢复界面设置
    def _snapshot(self):
        state = {name: getattr(self, name).get() for name in REMEMBER}
        state.update(transport=self._transport(), mode=self.v_mode.get(), bchar=self.v_bchar.get(),
                     fault=FAULT_KEYS[max(0, self.cb_fault.current())], items=[list(i) for i in self._items()])
        return state

    def _restore(self, state):
        if not state:
            return
        try:
            keys = [t[0] for t in TRANSPORTS]
            if state.get('transport') in keys:
                self.cb_transport.current(keys.index(state['transport']))
            if state.get('mode') in mc.MODE_DEFAULTS:
                self.v_mode.set(state['mode'])
            self._on_mode(init=True)
            for name in REMEMBER:
                if name in state:
                    getattr(self, name).set(state[name])
            if state.get('bchar'):
                self.v_bchar.set(state['bchar'])
            if state.get('fault') in FAULT_KEYS:
                self.cb_fault.current(FAULT_KEYS.index(state['fault']))
            if state.get('items'):
                self._set_items([tuple(i) for i in state['items']])
            self._on_transport()
        except (tk.TclError, TypeError, ValueError):
            pass  # 设置文件损坏时忽略，用默认值

    # ================================================================ 语言 / 帮助 / 关于 / 更新
    def _set_language(self, code):
        if code == i18n.get_lang():
            return
        if self.link:
            if not messagebox.askyesno(_('切换语言'), _('切换语言需要先停止模拟器，是否继续？')):
                self.v_lang.set(i18n.get_lang())
                return
            self._stop()
        state = self._snapshot()
        events = list(self.events)
        if self.autosave:
            self.autosave.close()
            self.autosave = None
        if self.help_win is not None and self.help_win.winfo_exists():
            self.help_win.destroy()
        self.settings['lang'] = code
        save_settings(self.settings)
        i18n.set_lang(code)
        self.root.after_cancel(self._after_id)
        for w in self.root.winfo_children():
            w.destroy()
        App(self.root, self.settings, state, events).fit_width()

    def _show_help(self):
        if self.help_win is not None and self.help_win.winfo_exists():
            self.help_win.lift()
            return
        win = tk.Toplevel(self.root)
        win.title(_('使用方法'))
        win.geometry('820x680')
        self.help_win = win
        body = ttk.Frame(win)
        body.pack(fill='both', expand=True, padx=8, pady=8)
        txt = tk.Text(body, wrap='word', padx=14, pady=10, relief='flat', spacing1=2, spacing3=2)
        ys = ttk.Scrollbar(body, orient='vertical', command=txt.yview)
        txt.configure(yscrollcommand=ys.set)
        txt.pack(side='left', fill='both', expand=True)
        ys.pack(side='right', fill='y')
        base = tkfont.nametofont('TkDefaultFont')
        size = abs(base.cget('size')) or 11
        txt.configure(font=(base.cget('family'), size + 1))
        txt.tag_config('h1', font=(base.cget('family'), size + 7, 'bold'), spacing1=6, spacing3=8)
        txt.tag_config('h2', font=(base.cget('family'), size + 3, 'bold'), foreground='#1565C0',
                       spacing1=14, spacing3=4)
        txt.tag_config('li', lmargin1=14, lmargin2=30)
        txt.tag_config('code', font=self.mono, background='#F1F3F4')
        for line in help_content.get(i18n.get_lang()).strip('\n').split('\n'):
            if line.startswith('# '):
                txt.insert('end', line[2:] + '\n', 'h1')
            elif line.startswith('## '):
                txt.insert('end', line[3:] + '\n', 'h2')
            elif line.startswith('    '):
                txt.insert('end', line.strip() + '\n', 'code')
            elif line.startswith('- '):
                txt.insert('end', '•  ' + line[2:] + '\n', 'li')
            else:
                txt.insert('end', line + '\n')
        txt.config(state='disabled')
        ttk.Button(win, text=_('关闭'), command=win.destroy).pack(pady=(0, 8))

    def _about(self):
        win = tk.Toplevel(self.root)
        win.title(_('关于'))
        win.resizable(False, False)
        win.transient(self.root)
        f = ttk.Frame(win, padding=20)
        f.pack(fill='both', expand=True)
        icon = find_icon()
        if icon:
            try:
                img = tk.PhotoImage(file=icon).subsample(8)
                lbl = ttk.Label(f, image=img)
                lbl.image = img
                lbl.pack()
            except tk.TclError:
                pass
        title = tkfont.nametofont('TkDefaultFont').copy()
        title.configure(size=abs(title.cget('size')) + 5, weight='bold')
        ttk.Label(f, text=_('IEC 62056-21 电表模拟器'), font=title).pack(pady=(8, 2))
        ttk.Label(f, text=_('版本 %s') % app_info.VERSION).pack()
        ttk.Label(f, text=_('模拟 IEC 62056-21 电表（Mode A~E），用于调试 DTU / 采集器'),
                  foreground='#546E7A').pack(pady=(4, 12))

        grid = ttk.Frame(f)
        grid.pack()

        def row(r, label, value, url=None):
            ttk.Label(grid, text=label, foreground='#607D8B').grid(row=r, column=0, sticky='e', padx=6, pady=2)
            w = ttk.Label(grid, text=value, foreground='#1565C0' if url else '', cursor='hand2' if url else '')
            w.grid(row=r, column=1, sticky='w', pady=2)
            if url:
                w.bind('<Button-1>', lambda e: webbrowser.open(url))

        row(0, _('开发者'), app_info.DEVELOPER)
        row(1, _('联系邮箱'), app_info.CONTACT, 'mailto:' + app_info.CONTACT)
        row(2, _('网站'), app_info.WEBSITE, app_info.WEBSITE)
        repo = app_info.GITHUB_REPO
        row(3, _('更新源'), ('github.com/' + repo) if repo else _('未配置'),
            'https://github.com/%s/releases' % repo if repo else None)
        row(4, _('运行环境'), 'Python %s · Tk %s · %s %s' % (
            platform.python_version(), tk.TkVersion, platform.system(), platform.machine()))
        ttk.Label(f, text=app_info.COPYRIGHT, foreground='#90A4AE').pack(pady=(12, 8))
        bf = ttk.Frame(f)
        bf.pack()
        ttk.Button(bf, text=_('检查更新…'), command=lambda: self._check_update(manual=True)).pack(side='left', padx=4)
        ttk.Button(bf, text=_('关闭'), command=win.destroy).pack(side='left', padx=4)

    def _toggle_auto_update(self):
        self.settings['auto_update'] = self.v_auto_update.get()
        save_settings(self.settings)

    def _check_update(self, manual):
        if manual:
            self.v_status.set(_('正在检查更新…'))

        def work():
            try:
                result, err = updater.check_latest(), None
            except updater.UpdateError as e:
                result, err = None, str(e)
            self.q.put({'kind': '_call', 'fn': lambda: self._update_result(result, err, manual)})

        threading.Thread(target=work, daemon=True).start()

    def _update_result(self, result, err, manual):
        self._update_status()
        if err:
            if manual:
                messagebox.showwarning(_('检查更新'), err)
            return
        latest = result['version']
        if not updater.is_newer(latest):
            if manual:
                messagebox.showinfo(_('检查更新'), _('已是最新版本（%s）') % app_info.VERSION)
            return
        if not manual and self.settings.get('skip_version') == latest:
            return
        self._show_update(result)

    def _show_update(self, result):
        win = tk.Toplevel(self.root)
        win.title(_('发现新版本'))
        win.transient(self.root)
        f = ttk.Frame(win, padding=16)
        f.pack(fill='both', expand=True)
        title = tkfont.nametofont('TkDefaultFont').copy()
        title.configure(size=abs(title.cget('size')) + 3, weight='bold')
        lbl = ttk.Label(f, text=_('发现新版本 %s（当前 %s）') % (result['version'], app_info.VERSION), font=title)
        lbl.font = title
        lbl.pack(anchor='w')
        if result['notes']:
            ttk.Label(f, text=_('更新内容：')).pack(anchor='w', pady=(10, 2))
            notes = tk.Text(f, width=64, height=12, wrap='word', relief='flat', background='#F5F7F8')
            notes.insert('1.0', result['notes'][:4000])
            notes.config(state='disabled')
            notes.pack(fill='both', expand=True)
        bf = ttk.Frame(f)
        bf.pack(fill='x', pady=(12, 0))

        def download():
            webbrowser.open(result['download'] or result['page'])
            win.destroy()

        def skip():
            self.settings['skip_version'] = result['version']
            save_settings(self.settings)
            win.destroy()

        ttk.Button(bf, text=_('下载新版本'), command=download).pack(side='right')
        ttk.Button(bf, text=_('稍后提醒'), command=win.destroy).pack(side='right', padx=6)
        ttk.Button(bf, text=_('跳过此版本'), command=skip).pack(side='left')

    def _open_log_folder(self):
        folder = log_folder()
        os.makedirs(folder, exist_ok=True)
        try:
            open_path(folder)
        except OSError as e:
            messagebox.showerror(_('提示'), str(e))

    # ================================================================ 日志
    def _log_local(self, kind, text):
        self.q.put(mc.make_event(kind, text))

    def _drain(self):
        n = 0
        try:
            while n < 500:
                ev = self.q.get_nowait()
                n += 1
                if ev['kind'] == '_call':
                    ev['fn']()
                else:
                    self._handle(ev)
        except queue.Empty:
            pass
        if n:
            self.txt.see('end')
            self._update_status()
        self._after_id = self.root.after(80, self._drain)

    def _handle(self, ev):
        self.events.append(ev)
        kind = ev['kind']
        if kind == 'session':
            self._reset_steps()
            self.v_session.set(_('会话 #%d') % ev.get('session', 0))
        elif kind == 'stage':
            self._set_step(ev.get('stage'), ev.get('status'), ev.get('text', ''))
        elif kind == 'error':
            self.problem_count += 1
            self.v_step_note.set(_('问题：%s') % ev['text'])
        elif kind == 'hint' and self.v_step_note.get():
            self.v_step_note.set(self.v_step_note.get().split('\n')[0] + '\n' + _('建议：%s') % ev['text'])
        elif kind == 'items':
            self._set_items(ev.get('items', []))
        elif kind == 'link':
            self.v_link.set(ev['text'])
            if ev.get('stopped') and self.link is not None and not self.link.is_alive():
                self._on_stopped()
        if self.autosave:
            try:
                self.autosave.write(mc.format_event(ev) + '\n')
                self.autosave.flush()
            except OSError:
                pass
        self._render(ev)

    def _render(self, ev):
        if self.v_only_problem.get() and ev['kind'] not in PROBLEM_KINDS:
            return
        self.txt.config(state='normal')
        if ev['kind'] == 'session':
            self.txt.insert('end', '\n')
        self.txt.insert('end', mc.format_event(ev, self.v_hex.get()) + '\n', ev['kind'])
        self.txt.config(state='disabled')

    def _rerender(self):
        self._clear_text()
        for ev in self.events:
            self._render(ev)
        self.txt.see('end')

    def _clear_text(self):
        self.txt.config(state='normal')
        self.txt.delete('1.0', 'end')
        self.txt.config(state='disabled')

    def _clear_log(self):
        self.events = []
        self.problem_count = 0
        self._clear_text()
        self._update_status()

    def _export(self):
        if not self.events:
            messagebox.showinfo(_('提示'), _('日志为空'))
            return
        name = time.strftime('MeterSimulator_%Y%m%d_%H%M%S')
        path = filedialog.asksaveasfilename(
            title=_('导出交互日志'), initialfile=name + '.txt', defaultextension='.txt',
            filetypes=[(_('文本日志'), '*.txt'), (_('CSV 表格（Excel 可打开）'), '*.csv')])
        if not path:
            return
        try:
            mc.save_events(path, self.events)
        except OSError as e:
            messagebox.showerror(_('导出失败'), str(e))
            return
        self._log_local('info', _('日志已导出：%s') % path)

    def _toggle_autosave(self):
        if self.v_autosave.get():
            if self.link:
                self._open_autosave()
        elif self.autosave:
            self.autosave.close()
            self.autosave = None
            self._update_status()

    def _open_autosave(self):
        if self.autosave:
            return
        folder = log_folder()
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, time.strftime('session_%Y%m%d_%H%M%S.txt'))
        self.autosave = open(path, 'w', encoding='utf-8')
        self.autosave_path = path
        for ev in self.events:
            self.autosave.write(mc.format_event(ev) + '\n')
        self._log_local('info', _('自动保存到：%s') % path)

    def _update_status(self):
        sessions = sum(1 for e in self.events if e['kind'] == 'session')
        s = _('会话 %d 次 · 问题 %d 条 · 日志 %d 条') % (sessions, self.problem_count, len(self.events))
        if self.autosave:
            s += ' · ' + _('自动保存：%s') % self.autosave_path
        self.v_status.set(s)

    def _on_close(self):
        if self.link:
            self._stop()
        if self.autosave:
            self.autosave.close()
        self.settings['last'] = self._snapshot()
        save_settings(self.settings)
        self.root.after_cancel(self._after_id)
        self.root.destroy()


def main():
    try:  # Windows 高分屏下避免界面模糊
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    settings = load_settings()
    i18n.set_lang(settings.get('lang', i18n.DEFAULT_LANG))
    root = tk.Tk()
    icon = find_icon()
    if icon:
        try:
            root.iconphoto(True, tk.PhotoImage(file=icon))
        except tk.TclError:
            pass
    app = App(root, settings)
    root.geometry('1240x820')
    app.fit_width()
    root.mainloop()


if __name__ == '__main__':
    main()
