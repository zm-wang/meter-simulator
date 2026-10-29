# -*- coding: utf-8 -*-
"""
多语言：源码里直接写中文，用 _('中文') 取当前语言的文字；模块级常量用 N_() 标记、显示时再 _()。
译文在 translations.py：{中文: (English, Español)}。缺译文时显示中文原文，master测试.py 会检查遗漏。
"""

from translations import T

LANGS = {'en': 'English', 'zh': '简体中文', 'es': 'Español'}
DEFAULT_LANG = 'en'
_lang = DEFAULT_LANG


def set_lang(code):
    global _lang
    _lang = code if code in LANGS else DEFAULT_LANG


def get_lang():
    return _lang


def N_(text):
    return text


def _(text):
    if _lang == 'zh':
        return text
    t = T.get(text)
    if t is None:
        return text
    return t[0] if _lang == 'en' else t[1]
