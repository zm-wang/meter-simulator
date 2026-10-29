#!/usr/bin/env python3
"""
一键打包电表模拟器。PyInstaller 不能跨平台打包：在哪个系统上运行，就生成哪个系统的安装包。

  macOS   → dist/MeterSimulator-<版本>-macos-<arm64|x86_64>.dmg
  Windows → dist/MeterSimulator-<版本>-windows-setup.exe（需要 Inno Setup 6；没装则生成 -windows.zip）
  Linux   → dist/MeterSimulator-<版本>-linux-x86_64.tar.gz

用法（Python 3.8+）：
    pip install pyinstaller pyserial pillow certifi
    python packaging/build.py

版本号取自 app_info.py 的 VERSION。
"""

import os
import platform
import plistlib
import re
import shutil
import subprocess
import sys
import tarfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BUILD = os.path.join(ROOT, 'build')
DIST = os.path.join(ROOT, 'dist')
APP_NAME = 'MeterSimulator'              # 程序文件名用英文，避免各系统路径/编码问题
DISPLAY_NAME = 'IEC 62056-21 Meter Simulator'
FILE_NAME = 'MeterSimulator'
MANUAL = os.path.join(ROOT, '电表模拟器使用说明.html')
BUNDLE_ID = 'com.inhand.metersimulator'


def version():
    with open(os.path.join(ROOT, 'app_info.py'), encoding='utf-8') as f:
        return re.search(r"VERSION = '([^']+)'", f.read()).group(1)


def arch():
    m = platform.machine().lower()
    return {'amd64': 'x86_64', 'aarch64': 'arm64'}.get(m, m)


def run(cmd, **kw):
    print('>', ' '.join(cmd), flush=True)
    subprocess.check_call(cmd, **kw)


def pyinstaller():
    icon = os.path.join(HERE, 'icon.ico' if os.name == 'nt' else 'icon.png')
    cmd = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--windowed',
           '--name', APP_NAME,
           '--distpath', os.path.join(BUILD, 'dist'),
           '--workpath', os.path.join(BUILD, 'work'),
           '--specpath', BUILD,
           '--paths', ROOT,
           '--add-data', os.path.join(HERE, 'icon.png') + os.pathsep + '.',
           '--osx-bundle-identifier', BUNDLE_ID]
    if not sys.platform.startswith('linux'):
        cmd += ['--icon', icon]
    run(cmd + [os.path.join(ROOT, '电表模拟器.py')])
    return os.path.join(BUILD, 'dist')


def package_macos(out, ver):
    app = os.path.join(out, APP_NAME + '.app')
    # 写入版本号；改了 Info.plist 要重新做 ad-hoc 签名，否则 Apple 芯片上打不开
    plist = os.path.join(app, 'Contents', 'Info.plist')
    with open(plist, 'rb') as f:
        info = plistlib.load(f)
    info.update(CFBundleShortVersionString=ver, CFBundleVersion=ver,
                CFBundleDisplayName=DISPLAY_NAME, NSHighResolutionCapable=True,
                NSHumanReadableCopyright='© InHand Networks')
    with open(plist, 'wb') as f:
        plistlib.dump(info, f)
    run(['codesign', '--force', '--deep', '--sign', '-', app])

    stage = os.path.join(BUILD, 'dmg')
    shutil.rmtree(stage, ignore_errors=True)
    os.makedirs(stage)
    shutil.copytree(app, os.path.join(stage, APP_NAME + '.app'), symlinks=True)
    os.symlink('/Applications', os.path.join(stage, 'Applications'))
    shutil.copy(MANUAL, stage)
    dmg = os.path.join(DIST, '%s-%s-macos-%s.dmg' % (FILE_NAME, ver, arch()))
    run(['hdiutil', 'create', '-volname', '%s %s' % (DISPLAY_NAME, ver), '-srcfolder', stage,
         '-ov', '-format', 'UDZO', dmg])
    return dmg


def find_iscc():
    for p in (shutil.which('iscc'),
              r'C:\Program Files (x86)\Inno Setup 6\ISCC.exe',
              r'C:\Program Files\Inno Setup 6\ISCC.exe'):
        if p and os.path.exists(p):
            return p
    return None


def package_windows(out, ver):
    src = os.path.join(out, APP_NAME)
    iscc = find_iscc()
    if iscc:
        run([iscc, '/Q',
             '/DAppVersion=' + ver,
             '/DAppName=' + DISPLAY_NAME,
             '/DAppExe=' + APP_NAME + '.exe',
             '/DSourceDir=' + src,
             '/DOutputDir=' + DIST,
             '/DManual=' + MANUAL,
             '/DIconFile=' + os.path.join(HERE, 'icon.ico'),
             os.path.join(HERE, 'installer.iss')])
        return os.path.join(DIST, '%s-%s-windows-setup.exe' % (FILE_NAME, ver))
    print('未找到 Inno Setup，改为生成免安装 zip 包')
    shutil.copy(MANUAL, src)
    base = os.path.join(DIST, '%s-%s-windows' % (FILE_NAME, ver))
    return shutil.make_archive(base, 'zip', out, APP_NAME)


def package_linux(out, ver):
    src = os.path.join(out, APP_NAME)
    shutil.copy(MANUAL, src)
    path = os.path.join(DIST, '%s-%s-linux-%s.tar.gz' % (FILE_NAME, ver, arch()))
    with tarfile.open(path, 'w:gz') as tar:
        tar.add(src, arcname=APP_NAME)
    return path


def main():
    ver = version()
    os.makedirs(DIST, exist_ok=True)
    out = pyinstaller()
    if sys.platform == 'darwin':
        result = package_macos(out, ver)
    elif os.name == 'nt':
        result = package_windows(out, ver)
    else:
        result = package_linux(out, ver)
    print('\n完成：' + result)


if __name__ == '__main__':
    main()
