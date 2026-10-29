# -*- coding: utf-8 -*-
"""程序内“使用方法”的内容。格式：# 一级标题，## 二级标题，- 列表，四个空格开头为报文示例。"""

HELP = {}

HELP['en'] = """
# IEC 62056-21 Meter Simulator — How to Use

This tool plays the role of an IEC 62056-21 electricity meter (slave). Point your DTU / data collector (master) at it, then watch every step of the handshake. When the master sends something wrong, the log tells you what is wrong and what the correct message should be.

## Quick start (Mode C over serial)
- Connect the DTU's RS-232/RS-485 port to the PC with a USB-serial adapter (TX↔RX, GND↔GND; for RS-485 A↔A, B↔B).
- Connection: choose "Serial", select the port, keep 300 bps, 7 data bits, parity E, 1 stop bit (7E1).
- Meter settings: Protocol mode C. Keep the defaults unless your real meter differs.
- Click "▶ Start", then let the DTU read the meter.
- Watch "Connection process": each step turns green ✓ or red ✗. A red step shows the problem and a suggestion underneath.

## Connection types
- Serial: initial baud, data bits, parity and stop bits. Mode C/E switch to the negotiated baud after the ACK and switch back when the session ends.
- TCP server: the simulator listens; the DTU (or a transparent serial server) connects to it.
- TCP client: the simulator connects to the master's IP:port and reconnects automatically.
- UDP: binds a local port and replies to whoever sent the last datagram. "Push target" is used by Mode D before any master has sent data.
- Over the network there is no baud switching. If the device forwards 7E1 bytes unchanged, tick "Strip high bit on receive".

## Protocol modes
- Mode A: request → identification → data, all at one baud rate.
- Mode B: request → identification → switch baud (characters A~F) → data, no ACK.
- Mode C: request → identification → ACK option select → switch baud → data readout or programming mode. Most common.
- Mode D: the meter pushes identification + data at 2400 bps without being asked. Use "Push now" or a push interval.
- Mode E: like Mode C, identification carries \\2; ACK with V=2/Y=2 enters HDLC. The simulator only logs HDLC frames (no DLMS/COSEM).

## Meter settings
- Manufacturer ID: 3 letters. A lowercase third letter means 20 ms minimum reaction time; uppercase means 200 ms.
- Baud character: the baud rate the meter offers in its identification (Mode C/E: 0=300 … 5=9600, 6=19200).
- Meter address: empty accepts any address. If set, requests with another address are rejected and reported.
- Password: used by programming mode (P1). Empty means no check.
- Reply delay: time before each reply (standard 20/200 ~ 1500 ms). Increase it if the master switches baud slowly.
- Fault injection: no identification, no data after ACK, or a wrong BCC — to test how the DTU handles a faulty meter.
- Data items: double-click a cell to edit OBIS address, value and unit. Changes apply immediately while running.

## Programming mode (Mode C, Y=1)
The meter answers with P0; the master sends P1 (password), then R1~R6 (read), W1~W5 (write), E1/E2 (execute) and finally B0 (break). NAK makes the meter repeat its last message.
    /?!<CR><LF>  →  /INH5MG301-SIM<CR><LF>  →  <ACK>051<CR><LF>  →  <SOH>P0<STX>(…)<ETX><BCC>

## Log, export and diagnostics
- The log shows received (RX) and sent (TX) messages with control characters such as <STX>, plus HEX and millisecond timestamps.
- "Problems only" filters the log down to problems, suggestions, warnings and connection events.
- "Export log…" saves TXT or CSV (opens in Excel). "Auto-save log" writes every session to the log folder (File → Open log folder).
- Detected problems include: missing CR LF, wrong address, wrong request format, ACK timeout, incomplete or invalid ACK, baud rate higher than offered, HDLC requested outside Mode E, request repeated instead of ACK, 7E1 received as 8N1, garbled bytes (baud mismatch), echo on RS-485, BCC errors, wrong password, commands before login, unknown addresses.

## FAQ
- Nothing is received: check wiring, port, and that the DTU really uses the same initial baud (usually 300).
- The log says "high bit set": the DTU sends 7E1 but the simulator receives 8 bits — set 7 data bits / parity E (serial) or tick "Strip high bit" (network).
- The DTU repeats the request instead of sending ACK: it could not parse the identification. Check 7E1, the baud character and the DTU's timeout.
- ACK timeout: the DTU may work in Mode A/B (no ACK). Switch the simulator to Mode A or B to confirm.
- Garbled bytes right after the ACK: one side switched baud too early or not at all.

## Language and updates
- Language menu: English, 简体中文, Español. The choice is remembered.
- Help → Check for updates… compares this version with the latest release. Automatic checking on start-up can be turned off in the same menu.
"""

HELP['zh'] = """
# IEC 62056-21 电表模拟器使用方法

本工具模拟一块 IEC 62056-21 电表（从站）。让 DTU / 采集器（主站）来读它，界面会显示握手的每一步；主站报文有问题时，日志会指出问题，并给出正确的报文写法。

## 快速开始（Mode C，串口）
- 用 USB 转串口线把 DTU 的 RS-232/RS-485 口接到电脑（TX↔RX、GND↔GND；RS-485 为 A↔A、B↔B）。
- 连接方式：选“串口”，选择端口，保持 300 bps、7 数据位、偶校验 E、1 停止位（7E1）。
- 电表设置：协议模式选 C。如果真实电表参数不同，再按实际修改。
- 点“▶ 启动”，然后让 DTU 去抄表。
- 看“连接过程”：每一步变绿 ✓ 或变红 ✗；红色步骤下方会写出问题和建议。

## 连接方式
- 串口：设置初始波特率、数据位、校验、停止位。Mode C/E 在 ACK 之后切换到协商波特率，会话结束后自动切回。
- TCP 服务端：模拟器监听端口，DTU（或透传串口服务器）连进来。
- TCP 客户端：模拟器主动连接主站的 IP:端口，断开后自动重连。
- UDP：绑定本地端口，应答发给最近一次发来数据的一方；“推送目标”供 Mode D 在主站还没发过数据时使用。
- 网络连接不切换波特率。如果设备把 7E1 字节原样透传，请勾选“接收时去掉最高位”。

## 协议模式
- Mode A：请求 → 标识 → 数据，全程同一波特率。
- Mode B：请求 → 标识 → 按波特率字符（A~F）切速 → 数据，无 ACK。
- Mode C：请求 → 标识 → ACK 选项确认 → 切速 → 数据读取或编程模式。最常用。
- Mode D：电表以 2400 bps 主动推送标识和数据。可点“立即推送”或设置推送间隔。
- Mode E：握手同 Mode C，标识带 \\2；ACK 选 V=2/Y=2 后进入 HDLC。模拟器只记录 HDLC 帧，不实现 DLMS/COSEM。

## 电表设置
- 厂商ID：3 个字母。第 3 个字母小写表示最短响应 20 ms，大写表示 200 ms。
- 波特率字符：电表在标识中提议的波特率（Mode C/E：0=300 … 5=9600，6=19200）。
- 表地址：留空表示接受任意地址；填写后，地址不符的请求会被拒绝并在日志中指出。
- 编程口令：编程模式 P1 校验用，留空表示不校验。
- 响应延时：每次应答前的等待时间（标准 20/200 ~ 1500 ms）。主站切速慢时适当加大。
- 故障注入：不回标识、ACK 后不发数据、BCC 故意出错，用来测试 DTU 对异常电表的处理。
- 数据项：双击单元格修改 OBIS 地址、值、单位；运行中修改会立即生效。

## 编程模式（Mode C，Y=1）
电表回 P0；主站发 P1（口令），然后 R1~R6（读）、W1~W5（写）、E1/E2（执行），最后 B0（结束）。收到 NAK 时电表重发上一条报文。
    /?!<CR><LF>  →  /INH5MG301-SIM<CR><LF>  →  <ACK>051<CR><LF>  →  <SOH>P0<STX>(…)<ETX><BCC>

## 日志、导出与诊断
- 日志显示收（RX）、发（TX）的报文，控制字符写成 <STX> 这样的形式，并附 HEX 和毫秒时间戳。
- “只看问题”只显示问题、建议、警告和连接事件。
- “导出日志…”保存为 TXT 或 CSV（可用 Excel 打开）。“自动保存日志”把每次会话写入日志文件夹（文件 → 打开日志文件夹）。
- 能诊断的问题包括：缺少 CR LF、地址不符、请求格式错误、ACK 超时、ACK 不完整或无效、波特率高于电表提议、非 Mode E 却请求 HDLC、没发 ACK 而重发请求、7E1 被按 8N1 接收、乱码（波特率不一致）、RS-485 回显、BCC 错误、口令错误、未登录就读写、读取不存在的地址。

## 常见问题
- 收不到任何数据：检查接线、端口，以及 DTU 的初始波特率是否一致（一般为 300）。
- 日志提示“最高位被置位”：DTU 按 7E1 发送而模拟器按 8 位接收。串口改为 7 位 / 偶校验 E，网络勾选“接收时去掉最高位”。
- DTU 不发 ACK 而重发请求：它没能解析标识报文。检查 7E1、波特率字符和 DTU 的超时设置。
- ACK 超时：DTU 可能按 Mode A/B 工作（不发 ACK）。把模拟器切到 Mode A 或 B 验证。
- ACK 之后马上出现乱码：有一方切速太早或根本没切。

## 语言与更新
- “语言”菜单可选 English、简体中文、Español，选择会被记住。
- 帮助 → 检查更新…：与最新发布的版本比较。启动时自动检查可以在同一菜单里关闭。
"""

HELP['es'] = """
# Simulador de medidor IEC 62056-21 — Modo de uso

Esta herramienta actúa como un medidor eléctrico IEC 62056-21 (esclavo). Conecte su DTU / concentrador (maestro) y observe cada paso del protocolo. Si el maestro envía un mensaje incorrecto, el registro indica el problema y cuál debería ser el mensaje correcto.

## Inicio rápido (Modo C por puerto serie)
- Conecte el puerto RS-232/RS-485 del DTU al PC con un adaptador USB-serie (TX↔RX, GND↔GND; en RS-485 A↔A, B↔B).
- Conexión: elija "Puerto serie", seleccione el puerto y mantenga 300 bps, 7 bits de datos, paridad E, 1 bit de parada (7E1).
- Ajustes del medidor: modo de protocolo C. Mantenga los valores por defecto salvo que su medidor real sea distinto.
- Pulse "▶ Iniciar" y deje que el DTU lea el medidor.
- Observe "Proceso de conexión": cada paso se pone verde ✓ o rojo ✗. Bajo un paso rojo aparecen el problema y una sugerencia.

## Tipos de conexión
- Puerto serie: velocidad inicial, bits de datos, paridad y bits de parada. Los modos C/E cambian a la velocidad negociada tras el ACK y vuelven al terminar la sesión.
- Servidor TCP: el simulador escucha; el DTU (o un servidor serie transparente) se conecta a él.
- Cliente TCP: el simulador se conecta a la IP:puerto del maestro y se reconecta automáticamente.
- UDP: se enlaza a un puerto local y responde a quien envió el último datagrama. El "destino de envío" lo usa el Modo D antes de que el maestro haya enviado datos.
- En red no hay cambio de velocidad. Si el equipo reenvía los bytes 7E1 sin cambios, marque "Quitar bit alto al recibir".

## Modos de protocolo
- Modo A: solicitud → identificación → datos, todo a una misma velocidad.
- Modo B: solicitud → identificación → cambio de velocidad (caracteres A~F) → datos, sin ACK.
- Modo C: solicitud → identificación → ACK de selección de opción → cambio de velocidad → lectura de datos o modo de programación. El más habitual.
- Modo D: el medidor envía identificación + datos a 2400 bps sin que se lo pidan. Use "Enviar ahora" o un intervalo de envío.
- Modo E: como el Modo C, la identificación lleva \\2; un ACK con V=2/Y=2 entra en HDLC. El simulador solo registra las tramas HDLC (sin DLMS/COSEM).

## Ajustes del medidor
- ID de fabricante: 3 letras. Una tercera letra minúscula indica un tiempo de reacción mínimo de 20 ms; mayúscula, 200 ms.
- Carácter de velocidad: la velocidad que ofrece el medidor en su identificación (Modos C/E: 0=300 … 5=9600, 6=19200).
- Dirección del medidor: vacía acepta cualquier dirección. Si se define, las solicitudes con otra dirección se rechazan y se informan.
- Contraseña: la usa el modo de programación (P1). Vacía significa sin verificación.
- Retardo de respuesta: tiempo antes de cada respuesta (norma 20/200 ~ 1500 ms). Auméntelo si el maestro cambia de velocidad lentamente.
- Inyección de fallos: sin identificación, sin datos tras el ACK o BCC erróneo, para probar cómo reacciona el DTU ante un medidor defectuoso.
- Elementos de datos: doble clic en una celda para editar dirección OBIS, valor y unidad. Los cambios se aplican al momento.

## Modo de programación (Modo C, Y=1)
El medidor responde con P0; el maestro envía P1 (contraseña), luego R1~R6 (leer), W1~W5 (escribir), E1/E2 (ejecutar) y por último B0 (fin). Un NAK hace que el medidor repita su último mensaje.
    /?!<CR><LF>  →  /INH5MG301-SIM<CR><LF>  →  <ACK>051<CR><LF>  →  <SOH>P0<STX>(…)<ETX><BCC>

## Registro, exportación y diagnóstico
- El registro muestra mensajes recibidos (RX) y enviados (TX) con caracteres de control como <STX>, además de HEX y marcas de tiempo en milisegundos.
- "Solo problemas" filtra el registro a problemas, sugerencias, avisos y eventos de conexión.
- "Exportar registro…" guarda TXT o CSV (se abre en Excel). "Guardar registro automáticamente" escribe cada sesión en la carpeta de registros (Archivo → Abrir carpeta de registros).
- Problemas detectados: falta CR LF, dirección incorrecta, formato de solicitud erróneo, tiempo de espera del ACK, ACK incompleto o inválido, velocidad mayor que la ofrecida, HDLC fuera del Modo E, solicitud repetida en lugar de ACK, 7E1 recibido como 8N1, bytes ilegibles (velocidad distinta), eco en RS-485, errores de BCC, contraseña incorrecta, comandos antes de iniciar sesión, direcciones inexistentes.

## Preguntas frecuentes
- No se recibe nada: revise el cableado, el puerto y que el DTU use la misma velocidad inicial (normalmente 300).
- El registro dice "bit alto activado": el DTU envía 7E1 pero el simulador recibe 8 bits. Ponga 7 bits / paridad E (serie) o marque "Quitar bit alto" (red).
- El DTU repite la solicitud en lugar de enviar ACK: no pudo interpretar la identificación. Revise 7E1, el carácter de velocidad y el tiempo de espera del DTU.
- Tiempo de espera del ACK: el DTU puede trabajar en Modo A/B (sin ACK). Cambie el simulador a Modo A o B para confirmarlo.
- Bytes ilegibles justo después del ACK: un lado cambió de velocidad demasiado pronto o no cambió.

## Idioma y actualizaciones
- Menú Idioma: English, 简体中文, Español. La elección se recuerda.
- Ayuda → Buscar actualizaciones… compara esta versión con la última publicada. La comprobación automática al iniciar se puede desactivar en el mismo menú.
"""


def get(lang):
    return HELP.get(lang) or HELP['en']
