# -*- coding: utf-8 -*-
"""版本更新检测：读取 GitHub Releases 的最新版本，与当前版本比较。"""

import json
import platform
import re
import ssl
import sys
import urllib.error
import urllib.request

from app_info import GITHUB_REPO, VERSION
from i18n import _


class UpdateError(Exception):
    pass


def parse_version(text):
    return tuple(int(x) for x in re.findall(r'\d+', text)[:4])


def is_newer(latest, current=VERSION):
    return parse_version(latest) > parse_version(current)


def platform_tag():
    """与 packaging/build.py 生成的安装包文件名对应。"""
    if sys.platform == 'win32':
        return 'windows'
    if sys.platform == 'darwin':
        return 'macos-arm64' if platform.machine().lower() in ('arm64', 'aarch64') else 'macos-x86_64'
    return 'linux'


def _ssl_context():
    try:  # 打包后的程序不一定能找到系统证书，优先用 certifi 自带的
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def check_latest(repo=GITHUB_REPO, timeout=8, api='https://api.github.com'):
    """返回 {'version', 'page', 'download', 'notes'}；失败抛 UpdateError（文字已翻译）。"""
    if not repo:
        raise UpdateError(_('未配置更新源（app_info.py 中的 GITHUB_REPO 为空）'))
    url = '%s/repos/%s/releases/latest' % (api, repo)
    req = urllib.request.Request(url, headers={'Accept': 'application/vnd.github+json',
                                               'User-Agent': 'MeterSimulator/' + VERSION})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_ssl_context()) as r:
            data = json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise UpdateError(_('还没有发布过版本，或仓库 %s 不是公开仓库') % repo)
        raise UpdateError(_('检查更新失败：HTTP %d') % e.code)
    except (urllib.error.URLError, OSError, ValueError) as e:
        raise UpdateError(_('检查更新失败：%s') % getattr(e, 'reason', e))
    tag = platform_tag()
    download = next((a.get('browser_download_url') for a in data.get('assets', [])
                     if tag in a.get('name', '').lower()), None)
    return {'version': data.get('tag_name', '').lstrip('vV'),
            'page': data.get('html_url') or 'https://github.com/%s/releases' % repo,
            'download': download,
            'notes': (data.get('body') or '').strip()}
