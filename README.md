# IEC 62056-21 Meter Simulator

Simulates an IEC 62056-21 electricity meter (slave) for debugging DTUs and data collectors.
模拟 IEC 62056-21 电表（从站），用于调试 DTU / 采集器。

- Modes A / B / C / D / E (Mode C programming mode: P1, R1~R6, W1~W5, E1/E2, B0)
- Serial, TCP server, TCP client, UDP
- Step-by-step connection view; log export to TXT / CSV
- Diagnoses malformed master messages and suggests the correct message
- English / 简体中文 / Español; built-in help; update check

## Download / 下载

Installers for Windows, macOS (Apple silicon / Intel) and Linux: see [Releases](../../releases/latest).
The installers are not code-signed yet: on macOS use System Settings → Privacy & Security → "Open Anyway"; on Windows click "More info → Run anyway".

## Run from source / 源码运行

```bash
pip install -r requirements.txt
python3 电表模拟器.py
```

Tests: `python3 master测试.py`. Full manual (Chinese): `电表模拟器使用说明.html`.

## Release / 发布

Set `VERSION` in `app_info.py`, commit, then push a tag `vX.Y.Z`. GitHub Actions runs the tests, builds the installers and publishes the release; installed copies detect it via "Help → Check for updates".

Developer: InHand Networks · zeming.wang@inhand.com
