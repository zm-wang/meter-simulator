# -*- coding: utf-8 -*-
"""译文表：{中文原文: (English, Español)}。占位符（%s、%d…）的数量和顺序必须与原文一致。"""

T = {
    # ---------------------------------------------------------------- 协议常量
    '双向，不切换波特率：请求 → 标识 → 数据（全程同一波特率）': (
        'Bidirectional, no baud switch: request → identification → data (one baud rate throughout)',
        'Bidireccional, sin cambio de velocidad: solicitud → identificación → datos (misma velocidad siempre)'),
    '请求 → 标识 → 按波特率字符(A~F)切速 → 数据，无 ACK': (
        'Request → identification → switch baud by character (A~F) → data, no ACK',
        'Solicitud → identificación → cambio de velocidad según carácter (A~F) → datos, sin ACK'),
    '最常用：请求 → 标识 → ACK 选项确认 → 切速 → 数据读取 / 编程模式': (
        'Most common: request → identification → ACK option select → switch baud → readout / programming',
        'El más común: solicitud → identificación → ACK de opción → cambio de velocidad → lectura / programación'),
    '单向推送：电表以 2400 bps 主动发送标识和数据，不响应请求': (
        'Push only: the meter sends identification and data at 2400 bps on its own and ignores requests',
        'Solo envío: el medidor envía identificación y datos a 2400 bps por sí mismo y no atiende solicitudes'),
    '同 Mode C 握手，标识带 \\2；ACK 选 2 后进入 HDLC（DLMS）二进制模式': (
        'Same handshake as Mode C, identification carries \\2; ACK with 2 enters HDLC (DLMS) binary mode',
        'Mismo inicio que el Modo C, la identificación lleva \\2; un ACK con 2 entra en modo binario HDLC (DLMS)'),
    '数据读取': ('Data readout', 'Lectura de datos'),
    '编程模式': ('Programming mode', 'Modo de programación'),
    '二进制 HDLC': ('Binary HDLC', 'HDLC binario'),
    '厂商自定义': ('Manufacturer specific', 'Específico del fabricante'),
    '未知': ('unknown', 'desconocido'),
    '无': ('None', 'Ninguno'),
    '不回复标识': ('No identification reply', 'No responder identificación'),
    '收到 ACK 后不发数据': ('No data after ACK', 'Sin datos tras el ACK'),
    '数据 BCC 故意出错': ('Wrong BCC in data', 'BCC erróneo en los datos'),
    '请求': ('Request', 'Solicitud'),
    '标识': ('Identification', 'Identificación'),
    '数据': ('Data', 'Datos'),
    '结束': ('End', 'Fin'),
    '切速': ('Baud switch', 'Cambio de velocidad'),
    'ACK确认': ('ACK option', 'ACK de opción'),
    '数据/编程': ('Data/Programming', 'Datos/Programación'),
    '数据/HDLC': ('Data/HDLC', 'Datos/HDLC'),

    # ---------------------------------------------------------------- 日志标签
    '收': ('RX', 'RX'),
    '发': ('TX', 'TX'),
    '信息': ('INFO', 'INFO'),
    '阶段': ('STEP', 'PASO'),
    '警告': ('WARN', 'AVISO'),
    '问题': ('PROBLEM', 'PROBLEMA'),
    '建议': ('SUGGEST', 'SUGERENCIA'),
    '连接': ('LINK', 'CONEXIÓN'),
    '会话': ('SESSION', 'SESIÓN'),
    '进行中': ('in progress', 'en curso'),
    '完成': ('done', 'completado'),
    '失败': ('failed', 'fallido'),
    '跳过': ('skipped', 'omitido'),
    '%s：%s': ('%s: %s', '%s: %s'),
    '（%s）': (' (%s)', ' (%s)'),
    '、': (', ', ', '),
    '时间': ('Time', 'Hora'),
    '类型': ('Type', 'Tipo'),
    '说明': ('Description', 'Descripción'),
    '报文(可读)': ('Message (readable)', 'Mensaje (legible)'),
    '报文(HEX)': ('Message (HEX)', 'Mensaje (HEX)'),

    # ---------------------------------------------------------------- 引擎：会话与状态
    '连接断开，当前会话中止': ('Connection lost, current session aborted', 'Conexión perdida, sesión actual cancelada'),
    '%.0f 秒无通信，会话超时结束': ('No traffic for %.0f s, session timed out',
                           'Sin tráfico durante %.0f s, la sesión expiró'),
    '只有 Mode D 支持主动推送': ('Only Mode D supports pushing', 'Solo el Modo D admite envío espontáneo'),
    '会话 #%d 开始（Mode %s）': ('Session #%d started (Mode %s)', 'Sesión #%d iniciada (Modo %s)'),
    '网络连接，无需切换波特率': ('Network link, no baud switch needed', 'Conexión de red, no hace falta cambiar velocidad'),
    '波特率不变 %d': ('Baud rate unchanged %d', 'Velocidad sin cambios %d'),
    '已恢复初始波特率 %d bps，等待下一次请求': ('Restored initial baud rate %d bps, waiting for the next request',
                                  'Velocidad inicial %d bps restaurada, esperando la siguiente solicitud'),
    '回显（模拟器自己发出的数据被送回），不参与解析': (
        'Echo (the simulator\'s own data came back), ignored',
        'Eco (los datos enviados por el simulador volvieron), se ignora'),
    '检测到回显：收到了模拟器刚发出的报文': ('Echo detected: received the message the simulator just sent',
                            'Eco detectado: se recibió el mensaje que el simulador acaba de enviar'),
    '常见于 RS-485 半双工或光口回环。DTU 同样会收到自己发出的请求，需在 DTU 侧丢弃回显，或改用收发自动切换的 485 模块': (
        'Common with half-duplex RS-485 or optical loopback. The DTU also receives its own request; it must discard '
        'the echo, or use an RS-485 module with automatic direction control',
        'Habitual en RS-485 semidúplex o en el bucle óptico. El DTU también recibe su propia solicitud; debe descartar '
        'el eco o usar un módulo RS-485 con control automático de dirección'),
    '请求报文 /?设备地址!<CR><LF>（广播为 /?!<CR><LF>）': (
        'a request /?address!<CR><LF> (broadcast: /?!<CR><LF>)',
        'una solicitud /?dirección!<CR><LF> (difusión: /?!<CR><LF>)'),
    'ACK 选项报文 <ACK>0%s0<CR><LF>（HEX 06 30 %02X 30 0D 0A）': (
        'an ACK option message <ACK>0%s0<CR><LF> (HEX 06 30 %02X 30 0D 0A)',
        'un mensaje ACK de opción <ACK>0%s0<CR><LF> (HEX 06 30 %02X 30 0D 0A)'),
    '编程命令 <SOH>命令<STX>数据<ETX><BCC>，例如 <SOH>R1<STX>1.8.0()<ETX><BCC>': (
        'a programming command <SOH>cmd<STX>data<ETX><BCC>, e.g. <SOH>R1<STX>1.8.0()<ETX><BCC>',
        'un comando de programación <SOH>cmd<STX>datos<ETX><BCC>, p. ej. <SOH>R1<STX>1.8.0()<ETX><BCC>'),
    'HDLC 帧': ('HDLC frames', 'tramas HDLC'),

    # ---------------------------------------------------------------- 引擎：无法识别的数据
    '收到的字节最高位被置位，去掉最高位后为：%s': (
        'Received bytes have the high bit set; with the high bit removed they read: %s',
        'Los bytes recibidos tienen el bit alto activado; sin el bit alto se leen: %s'),
    '主站按 7 数据位 + 偶校验（7E1）发送，而模拟器按 8 数据位接收。串口：把模拟器改为 7 位 / 偶校验 E；网络：勾选「接收时去掉最高位」。反过来也说明：DTU 应使用 7E1，IEC 62056-21 规定的就是 7E1': (
        'The master sends 7 data bits + even parity (7E1) but the simulator receives 8 data bits. Serial: set the '
        'simulator to 7 bits / parity E; network: tick "Strip high bit on receive". It also confirms the DTU should '
        'use 7E1, which is what IEC 62056-21 specifies',
        'El maestro envía 7 bits de datos + paridad par (7E1) pero el simulador recibe 8 bits. Serie: configure el '
        'simulador con 7 bits / paridad E; red: marque "Quitar bit alto al recibir". También confirma que el DTU debe '
        'usar 7E1, que es lo que exige IEC 62056-21'),
    '收到 ACK 选项报文，但当前没有进行中的会话：%s': (
        'Received an ACK option message but no session is in progress: %s',
        'Se recibió un ACK de opción pero no hay ninguna sesión en curso: %s'),
    '必须先发请求 /?!<CR><LF> 并收到电表标识后，才能发 ACK 选项。也可能会话已超时（ACK 超时 %.1f 秒），或主站的请求没被电表收到': (
        'Send the request /?!<CR><LF> and receive the meter identification before the ACK option. The session may also '
        'have timed out (ACK timeout %.1f s), or the meter never received the master\'s request',
        'Primero envíe la solicitud /?!<CR><LF> y reciba la identificación antes del ACK de opción. También puede que la '
        'sesión haya expirado (tiempo de ACK %.1f s) o que el medidor no recibiera la solicitud'),
    '收到编程命令，但电表当前不在编程模式：%s': (
        'Received a programming command but the meter is not in programming mode: %s',
        'Se recibió un comando de programación pero el medidor no está en modo de programación: %s'),
    '进入编程模式的顺序：/?!<CR><LF> → 收标识 → <ACK>0Z1<CR><LF> → 收 P0 → 发 P1 口令': (
        'To enter programming mode: /?!<CR><LF> → receive identification → <ACK>0Z1<CR><LF> → receive P0 → send P1 password',
        'Para entrar en programación: /?!<CR><LF> → recibir identificación → <ACK>0Z1<CR><LF> → recibir P0 → enviar contraseña P1'),
    '收到无法识别的字节：%s': ('Received unrecognisable bytes: %s', 'Se recibieron bytes irreconocibles: %s'),
    '常见原因是双方波特率或数据位/校验位不一致，例如主站 9600、电表 300；或波特率切换时机不对（主站在发 ACK 之前就切了速，或电表切速后主站还没切）。Mode C 应在 ACK 之后才切换到协商波特率': (
        'Usually the baud rate or data bits/parity differ, e.g. master 9600 and meter 300; or the baud switch happens '
        'at the wrong time (the master switched before sending the ACK, or has not switched after the meter did). '
        'In Mode C the negotiated baud rate applies only after the ACK',
        'Normalmente la velocidad o los bits de datos/paridad no coinciden, p. ej. maestro 9600 y medidor 300; o el cambio '
        'de velocidad ocurre en mal momento (el maestro cambió antes de enviar el ACK o no cambió después del medidor). '
        'En el Modo C la velocidad negociada se aplica solo después del ACK'),
    '收到不符合协议的数据：%s': ('Received data that does not follow the protocol: %s',
                       'Se recibieron datos que no siguen el protocolo: %s'),
    '当前应收到 %s': ('Expected now: %s', 'Ahora se esperaba: %s'),

    # ---------------------------------------------------------------- 引擎：请求
    '收到以 / 开头的数据但一直没有结束符 !：%s': (
        'Received data starting with / but no closing !: %s',
        'Se recibieron datos que empiezan por / pero sin el ! final: %s'),
    '请求报文格式为 /?设备地址!<CR><LF>，! 不能省略': (
        'The request format is /?address!<CR><LF>; the ! is mandatory',
        'El formato de la solicitud es /?dirección!<CR><LF>; el ! es obligatorio'),
    '收到请求 %s，但 Mode D 电表只单向推送、不响应请求': (
        'Received request %s, but a Mode D meter only pushes and never answers requests',
        'Se recibió la solicitud %s, pero un medidor en Modo D solo envía y nunca responde'),
    '若 DTU 需要主动抄表，请把模拟器切到 Mode A/B/C；若电表确实是 Mode D，DTU 应以 2400 bps 7E1 被动接收': (
        'If the DTU polls the meter, switch the simulator to Mode A/B/C; if the meter really is Mode D, the DTU should '
        'just listen at 2400 bps 7E1',
        'Si el DTU interroga al medidor, cambie el simulador a Modo A/B/C; si el medidor es realmente Modo D, el DTU debe '
        'solo escuchar a 2400 bps 7E1'),
    '请求报文格式错误：%s': ('Malformed request: %s', 'Solicitud mal formada: %s'),
    '正确格式为 /?设备地址!<CR><LF>：第 2 个字符必须是 ?。例如 /?!<CR><LF>（HEX 2F 3F 21 0D 0A）': (
        'Correct format is /?address!<CR><LF>: the 2nd character must be ?. Example: /?!<CR><LF> (HEX 2F 3F 21 0D 0A)',
        'El formato correcto es /?dirección!<CR><LF>: el 2.º carácter debe ser ?. Ejemplo: /?!<CR><LF> (HEX 2F 3F 21 0D 0A)'),
    '请求报文缺少结尾的 <CR><LF>': ('The request is missing the trailing <CR><LF>',
                           'A la solicitud le falta el <CR><LF> final'),
    '应发送 %s<CR><LF>（HEX 末尾 0D 0A）。模拟器仍会应答，但很多真实电表会直接不应答': (
        'Send %s<CR><LF> (HEX ending 0D 0A). The simulator still answers, but many real meters will not',
        'Envíe %s<CR><LF> (HEX terminado en 0D 0A). El simulador responde igualmente, pero muchos medidores reales no'),
    '设备地址长度 %d 超过标准规定的 32 个字符': (
        'Address length %d exceeds the 32 characters allowed by the standard',
        'La longitud de la dirección %d supera los 32 caracteres que permite la norma'),
    '检查 DTU 中的电表地址配置': ('Check the meter address configured in the DTU',
                         'Revise la dirección del medidor configurada en el DTU'),
    '设备地址含非字母数字字符："%s"，部分电表不接受': (
        'The address contains non-alphanumeric characters: "%s"; some meters reject this',
        'La dirección contiene caracteres no alfanuméricos: "%s"; algunos medidores no la aceptan'),
    '请求地址 "%s" 与电表地址 "%s" 不一致，电表不应答': (
        'Requested address "%s" does not match meter address "%s"; the meter does not answer',
        'La dirección solicitada "%s" no coincide con la del medidor "%s"; el medidor no responde'),
    'DTU 中把电表地址设为 %s，或在总线上只有一块表时使用广播请求 /?!<CR><LF>': (
        'Set the meter address in the DTU to %s, or use the broadcast request /?!<CR><LF> when only one meter is on the bus',
        'Configure en el DTU la dirección %s, o use la solicitud de difusión /?!<CR><LF> si solo hay un medidor en el bus'),
    '收到请求：设备地址 = %s': ('Request received: address = %s', 'Solicitud recibida: dirección = %s'),
    '（空，广播）': ('(empty, broadcast)', '(vacía, difusión)'),
    '故障注入：不回复标识报文': ('Fault injection: not sending identification',
                       'Inyección de fallos: no se envía la identificación'),
    '故障注入': ('Fault injection', 'Inyección de fallos'),
    '标识报文：厂商 %s，波特率字符 %s': ('Identification: manufacturer %s, baud character %s',
                              'Identificación: fabricante %s, carácter de velocidad %s'),
    'Mode B 的波特率字符应为 A~F，当前为 "%s"': ('Mode B baud character must be A~F, currently "%s"',
                                       'En el Modo B el carácter de velocidad debe ser A~F, ahora es "%s"'),
    '在电表设置中修改波特率字符': ('Change the baud character in the meter settings',
                        'Cambie el carácter de velocidad en los ajustes del medidor'),
    '等待主站 ACK 选项（%.1f 秒）': ('Waiting for the master\'s ACK option (%.1f s)',
                              'Esperando el ACK de opción del maestro (%.1f s)'),
    '故障注入：不发送数据报文': ('Fault injection: not sending data', 'Inyección de fallos: no se envían los datos'),
    '数据报文：%d 项，BCC=0x%02X%s': ('Data message: %d items, BCC=0x%02X%s', 'Mensaje de datos: %d elementos, BCC=0x%02X%s'),
    '（故意出错）': (' (deliberately wrong)', ' (erróneo a propósito)'),

    # ---------------------------------------------------------------- 引擎：ACK
    '主站没有发送 ACK 选项，而是重新发送了请求': (
        'The master repeated the request instead of sending the ACK option',
        'El maestro repitió la solicitud en lugar de enviar el ACK de opción'),
    '说明主站没能接收或解析电表的标识报文。请检查：① DTU 串口是否为 7E1（不是 8N1）；② DTU 是否支持标识中的波特率字符 "%s"；③ DTU 等待标识的超时是否太短（模拟器当前响应延时 %d ms）。若 DTU 按 Mode A/B 工作（不发 ACK），请把模拟器切到对应模式验证': (
        'The master could not receive or parse the identification. Check: (1) the DTU serial port is 7E1 (not 8N1); '
        '(2) the DTU supports baud character "%s"; (3) the DTU\'s identification timeout is not too short (current '
        'reply delay %d ms). If the DTU works in Mode A/B (no ACK), switch the simulator to that mode to confirm',
        'El maestro no pudo recibir o interpretar la identificación. Compruebe: (1) que el puerto del DTU sea 7E1 (no 8N1); '
        '(2) que el DTU admita el carácter de velocidad "%s"; (3) que el tiempo de espera del DTU no sea muy corto '
        '(retardo actual %d ms). Si el DTU trabaja en Modo A/B (sin ACK), cambie el simulador a ese modo para confirmarlo'),
    '在 ACK 选项确认之前收到了编程命令（SOH 开头）': (
        'Received a programming command (starting with SOH) before the ACK option',
        'Se recibió un comando de programación (empieza por SOH) antes del ACK de opción'),
    '应先发 <ACK>0%s1<CR><LF> 进入编程模式，收到电表 P0 后再发 P1 口令': (
        'First send <ACK>0%s1<CR><LF> to enter programming mode, then send the P1 password after the meter\'s P0',
        'Primero envíe <ACK>0%s1<CR><LF> para entrar en programación y, tras el P0 del medidor, envíe la contraseña P1'),
    '只收到 %s，ACK 选项报文不完整': ('Only received %s; the ACK option message is incomplete',
                            'Solo se recibió %s; el mensaje ACK de opción está incompleto'),
    'Mode C 的 ACK 选项报文共 6 字节：<ACK> V Z Y <CR><LF>，读数应为 <ACK>0%s0<CR><LF>（HEX 06 30 %02X 30 0D 0A）': (
        'The Mode C ACK option message has 6 bytes: <ACK> V Z Y <CR><LF>; for a readout send <ACK>0%s0<CR><LF> '
        '(HEX 06 30 %02X 30 0D 0A)',
        'El ACK de opción del Modo C tiene 6 bytes: <ACK> V Z Y <CR><LF>; para una lectura envíe <ACK>0%s0<CR><LF> '
        '(HEX 06 30 %02X 30 0D 0A)'),
    '发出标识后 %.1f 秒内没有收到主站的 ACK 选项报文': (
        'No ACK option from the master within %.1f s after the identification',
        'No llegó el ACK de opción del maestro en %.1f s tras la identificación'),
    'Mode C 要求主站收到标识后发送 <ACK>0%s0<CR><LF>（HEX 06 30 %02X 30 0D 0A）。可能原因：① DTU 按 Mode A/B 工作，不发 ACK 而直接等数据——可把模拟器切到 Mode A 或 B 验证；② DTU 没收到/没解析出标识报文（检查 7E1、波特率、接线）；③ DTU 先切了波特率再发 ACK，导致电表收到乱码': (
        'Mode C requires the master to send <ACK>0%s0<CR><LF> (HEX 06 30 %02X 30 0D 0A) after the identification. '
        'Possible causes: (1) the DTU works in Mode A/B and waits for data without an ACK — switch the simulator to '
        'Mode A or B to confirm; (2) the DTU did not receive/parse the identification (check 7E1, baud rate, wiring); '
        '(3) the DTU switched baud before sending the ACK, so the meter received garbage',
        'El Modo C exige que el maestro envíe <ACK>0%s0<CR><LF> (HEX 06 30 %02X 30 0D 0A) tras la identificación. '
        'Causas posibles: (1) el DTU trabaja en Modo A/B y espera datos sin ACK — cambie el simulador a Modo A o B para '
        'confirmarlo; (2) el DTU no recibió/interpretó la identificación (revise 7E1, velocidad, cableado); '
        '(3) el DTU cambió de velocidad antes de enviar el ACK y el medidor recibió basura'),
    '超时': ('timeout', 'tiempo agotado'),
    '<ACK>0%s0<CR><LF>（读数）或 <ACK>0%s1<CR><LF>（编程）': (
        '<ACK>0%s0<CR><LF> (readout) or <ACK>0%s1<CR><LF> (programming)',
        '<ACK>0%s0<CR><LF> (lectura) o <ACK>0%s1<CR><LF> (programación)'),
    '收到 ACK 选项：协议 V=%s，波特率 Z=%s，模式 Y=%s（%s）': (
        'ACK option received: protocol V=%s, baud Z=%s, mode Y=%s (%s)',
        'ACK de opción recibido: protocolo V=%s, velocidad Z=%s, modo Y=%s (%s)'),
    'ACK 选项报文缺少结尾的 <CR><LF>': ('The ACK option message is missing the trailing <CR><LF>',
                                'Al ACK de opción le falta el <CR><LF> final'),
    '完整格式为 %s': ('Full format: %s', 'Formato completo: %s'),
    '协议控制字符 V="%s" 无效': ('Invalid protocol control character V="%s"', 'Carácter de control de protocolo V="%s" no válido'),
    '正常协议应为 0（Mode E 进入 HDLC 时为 2）。正确报文：%s': (
        'Normal protocol is 0 (2 to enter HDLC in Mode E). Correct message: %s',
        'El protocolo normal es 0 (2 para entrar en HDLC en el Modo E). Mensaje correcto: %s'),
    '波特率字符 Z="%s" 无效（Mode C/E 只用 0~6）': ('Invalid baud character Z="%s" (Mode C/E only use 0~6)',
                                          'Carácter de velocidad Z="%s" no válido (los Modos C/E solo usan 0~6)'),
    '主站应回送电表标识中的波特率字符 "%s"。正确报文：%s': (
        'The master should echo the baud character "%s" from the identification. Correct message: %s',
        'El maestro debe devolver el carácter de velocidad "%s" de la identificación. Mensaje correcto: %s'),
    '主站要求 %d bps，高于电表在标识中提议的 %d bps': (
        'The master asked for %d bps, higher than the %d bps offered in the identification',
        'El maestro pidió %d bps, más que los %d bps ofrecidos en la identificación'),
    'Z 只能等于或低于标识中的 "%s"。正确报文：%s': (
        'Z must be equal to or lower than "%s" from the identification. Correct message: %s',
        'Z debe ser igual o menor que el "%s" de la identificación. Mensaje correcto: %s'),
    '主站选择了较低的波特率 %d bps（标准允许）': ('The master chose a lower baud rate %d bps (allowed by the standard)',
                                    'El maestro eligió una velocidad menor, %d bps (lo permite la norma)'),
    '主站请求厂商自定义模式 Y=%s，模拟器未实现': (
        'The master requested manufacturer-specific mode Y=%s, not implemented in the simulator',
        'El maestro pidió el modo específico del fabricante Y=%s, no implementado en el simulador'),
    '标准读数用 Y=0，编程用 Y=1': ('Use Y=0 for a standard readout and Y=1 for programming',
                          'Use Y=0 para una lectura estándar e Y=1 para programación'),
    '主站请求 HDLC 二进制模式（属于 Mode E），而电表当前为 Mode %s': (
        'The master requested binary HDLC mode (Mode E) but the meter is in Mode %s',
        'El maestro pidió el modo binario HDLC (Modo E) pero el medidor está en Modo %s'),
    '若 DTU 走 DLMS/COSEM，请把模拟器切到 Mode E；若只需读数，ACK 应为 %s': (
        'If the DTU uses DLMS/COSEM, switch the simulator to Mode E; for a plain readout the ACK should be %s',
        'Si el DTU usa DLMS/COSEM, cambie el simulador a Modo E; para una lectura simple el ACK debe ser %s'),
    '进入 HDLC 时 V 和 Y 通常都为 2，即 <ACK>2%s2<CR><LF>': (
        'To enter HDLC both V and Y are normally 2, i.e. <ACK>2%s2<CR><LF>',
        'Para entrar en HDLC, V e Y suelen ser 2, es decir <ACK>2%s2<CR><LF>'),
    '模式控制字符 Y="%s" 无效': ('Invalid mode control character Y="%s"', 'Carácter de control de modo Y="%s" no válido'),
    '0=数据读取，1=编程模式，2=HDLC（仅 Mode E）': ('0=data readout, 1=programming mode, 2=HDLC (Mode E only)',
                                         '0=lectura de datos, 1=programación, 2=HDLC (solo Modo E)'),
    '口令请求 P0': ('Password request P0', 'Solicitud de contraseña P0'),
    '已进入 HDLC 二进制模式。模拟器未实现 DLMS/COSEM 应用层，只记录收到的 HDLC 帧': (
        'Entered binary HDLC mode. The simulator does not implement the DLMS/COSEM layer; it only logs HDLC frames',
        'Modo binario HDLC activo. El simulador no implementa la capa DLMS/COSEM; solo registra las tramas HDLC'),

    # ---------------------------------------------------------------- 引擎：编程模式
    '主站发送 NAK，要求电表重发上一条报文': ('The master sent NAK, asking the meter to repeat its last message',
                             'El maestro envió NAK y pide repetir el último mensaje'),
    '重发': ('Repeat', 'Repetición'),
    '命令报文超过 512 字节仍没有 <ETX>': ('Command exceeds 512 bytes without an <ETX>', 'El comando supera 512 bytes sin <ETX>'),
    '每条命令必须以 <ETX><BCC> 结束': ('Every command must end with <ETX><BCC>', 'Cada comando debe terminar en <ETX><BCC>'),
    '编程模式下命令应以 <SOH> 开头，收到的是 <STX>：%s': (
        'In programming mode commands must start with <SOH>, received <STX>: %s',
        'En programación los comandos deben empezar por <SOH>, se recibió <STX>: %s'),
    '命令格式：<SOH>命令<STX>数据<ETX><BCC>，例如 <SOH>R1<STX>1.8.0()<ETX><BCC>': (
        'Command format: <SOH>cmd<STX>data<ETX><BCC>, e.g. <SOH>R1<STX>1.8.0()<ETX><BCC>',
        'Formato del comando: <SOH>cmd<STX>datos<ETX><BCC>, p. ej. <SOH>R1<STX>1.8.0()<ETX><BCC>'),
    'BCC 校验错误：收到 0x%02X，正确应为 0x%02X': ('BCC error: received 0x%02X, expected 0x%02X',
                                        'Error de BCC: se recibió 0x%02X, se esperaba 0x%02X'),
    'BCC 从 SOH 之后的第一个字节开始、到 ETX（含）为止逐字节异或，不含 SOH 本身，也不含 BCC。本报文正确写法：%s': (
        'The BCC is the XOR of every byte from the one after SOH up to and including ETX, excluding SOH and the BCC '
        'itself. This message should be: %s',
        'El BCC es el XOR de todos los bytes desde el siguiente a SOH hasta ETX inclusive, sin contar SOH ni el propio '
        'BCC. Este mensaje debería ser: %s'),
    'NAK（BCC 错误）': ('NAK (BCC error)', 'NAK (error de BCC)'),
    '命令报文太短：%s': ('Command too short: %s', 'Comando demasiado corto: %s'),
    '格式：<SOH>命令<STX>数据<ETX><BCC>': ('Format: <SOH>cmd<STX>data<ETX><BCC>', 'Formato: <SOH>cmd<STX>datos<ETX><BCC>'),
    '未知命令 "%s"': ('Unknown command "%s"', 'Comando desconocido "%s"'),
    '有效命令：P1/P2 口令，R1~R6 读，W1~W5 写，E1/E2 执行，B0/B1 结束': (
        'Valid commands: P1/P2 password, R1~R6 read, W1~W5 write, E1/E2 execute, B0/B1 break',
        'Comandos válidos: P1/P2 contraseña, R1~R6 leer, W1~W5 escribir, E1/E2 ejecutar, B0/B1 fin'),
    '错误应答': ('Error reply', 'Respuesta de error'),
    '命令字 %s 之后应紧跟 <STX>': ('Command %s must be followed by <STX>', 'El comando %s debe ir seguido de <STX>'),
    '正确示例：<SOH>R1<STX>1.8.0()<ETX><BCC>': ('Correct example: <SOH>R1<STX>1.8.0()<ETX><BCC>',
                                           'Ejemplo correcto: <SOH>R1<STX>1.8.0()<ETX><BCC>'),
    '收到命令 %s，数据：%s': ('Command %s received, data: %s', 'Comando %s recibido, datos: %s'),
    '（无）': ('(none)', '(ninguno)'),
    '收到结束命令 %s，会话结束': ('Break command %s received, session ended', 'Comando de fin %s recibido, sesión terminada'),
    '编程会话结束': ('Programming session ended', 'Sesión de programación terminada'),
    'P0 是电表发给主站的口令请求，主站不应发送': (
        'P0 is the password request sent by the meter; the master must not send it',
        'P0 es la solicitud de contraseña que envía el medidor; el maestro no debe enviarla'),
    '主站应发送 P1（明文口令）或 P2（加密口令）': ('The master should send P1 (plain password) or P2 (encrypted password)',
                                    'El maestro debe enviar P1 (contraseña en claro) o P2 (contraseña cifrada)'),
    '口令数据应放在括号内，收到：%s': ('The password must be in parentheses, received: %s',
                         'La contraseña debe ir entre paréntesis, se recibió: %s'),
    '例如 <SOH>P1<STX>(%s)<ETX><BCC>': ('e.g. <SOH>P1<STX>(%s)<ETX><BCC>', 'p. ej. <SOH>P1<STX>(%s)<ETX><BCC>'),
    '口令': ('password', 'contraseña'),
    'P2 为加密口令，模拟器不校验，直接通过': ('P2 is an encrypted password; the simulator accepts it without checking',
                              'P2 es una contraseña cifrada; el simulador la acepta sin verificar'),
    '口令通过': ('Password accepted', 'Contraseña aceptada'),
    '口令正确': ('Password correct', 'Contraseña correcta'),
    '口令错误：收到 "%s"': ('Wrong password: received "%s"', 'Contraseña incorrecta: se recibió "%s"'),
    '电表配置的口令为 "%s"，请在 DTU 中修正。电表发送 B0 中止会话': (
        'The meter password is "%s"; fix it in the DTU. The meter sends B0 to abort the session',
        'La contraseña del medidor es "%s"; corríjala en el DTU. El medidor envía B0 y cancela la sesión'),
    '中止 B0': ('Abort B0', 'Cancelar B0'),
    '口令错误': ('Wrong password', 'Contraseña incorrecta'),
    '未通过口令验证就发送了 %s': ('%s sent before the password was accepted', 'Se envió %s antes de aceptar la contraseña'),
    '应先发送 <SOH>P1<STX>(口令)<ETX><BCC>，收到电表 <ACK> 后再读写': (
        'First send <SOH>P1<STX>(password)<ETX><BCC> and wait for the meter\'s <ACK> before reading or writing',
        'Primero envíe <SOH>P1<STX>(contraseña)<ETX><BCC> y espere el <ACK> del medidor antes de leer o escribir'),
    '读命令的数据通常为 地址(参数)，例如 1.8.0()，收到：%s': (
        'Read command data is normally address(parameter), e.g. 1.8.0(), received: %s',
        'Los datos de lectura suelen ser dirección(parámetro), p. ej. 1.8.0(), se recibió: %s'),
    '读 %s 应答': ('Read %s reply', 'Respuesta de lectura %s'),
    '表中有相近地址 %s，OBIS 写法需与电表完全一致': (
        'Similar address(es) in the table: %s. The OBIS code must match the meter exactly',
        'Hay direcciones parecidas en la tabla: %s. El código OBIS debe coincidir exactamente'),
    '可用地址：%s。可在数据项表中添加': ('Available addresses: %s. You can add more in the data items table',
                          'Direcciones disponibles: %s. Puede añadir más en la tabla de datos'),
    '读取的地址 "%s" 不存在': ('Address "%s" does not exist', 'La dirección "%s" no existe'),
    '写命令数据格式错误：%s': ('Malformed write command data: %s', 'Datos de escritura mal formados: %s'),
    '格式为 地址(值)，例如 <SOH>W1<STX>C.1.0(1234)<ETX><BCC>': (
        'Format is address(value), e.g. <SOH>W1<STX>C.1.0(1234)<ETX><BCC>',
        'El formato es dirección(valor), p. ej. <SOH>W1<STX>C.1.0(1234)<ETX><BCC>'),
    '主站写入 %s = %s': ('Master wrote %s = %s', 'El maestro escribió %s = %s'),
    '写入成功': ('Write OK', 'Escritura correcta'),
    '执行成功': ('Execute OK', 'Ejecución correcta'),
    'HDLC 数据 %d 字节（未解析）': ('HDLC data %d bytes (not parsed)', 'Datos HDLC %d bytes (sin interpretar)'),
    'Mode D 推送：标识': ('Mode D push: identification', 'Envío Modo D: identificación'),

    # ---------------------------------------------------------------- 传输层
    '连接异常：%s': ('Connection error: %s', 'Error de conexión: %s'),
    '已停止': ('Stopped', 'Detenido'),
    '未安装 pyserial，请执行：pip install pyserial': ('pyserial is not installed; run: pip install pyserial',
                                           'pyserial no está instalado; ejecute: pip install pyserial'),
    '串口 %s 已打开：%d bps %d%s%d，等待主站请求…': (
        'Serial port %s open: %d bps %d%s%d, waiting for the master…',
        'Puerto serie %s abierto: %d bps %d%s%d, esperando al maestro…'),
    '串口波特率已切换为 %d bps': ('Serial baud rate switched to %d bps', 'Velocidad del puerto serie cambiada a %d bps'),
    'TCP 服务端监听 %s:%d，等待主站连接…': ('TCP server listening on %s:%d, waiting for the master…',
                                  'Servidor TCP escuchando en %s:%d, esperando al maestro…'),
    '主站已连接：%s:%d': ('Master connected: %s:%d', 'Maestro conectado: %s:%d'),
    '主站已断开：%s:%d，继续监听…': ('Master disconnected: %s:%d, still listening…',
                            'Maestro desconectado: %s:%d, se sigue escuchando…'),
    '没有已连接的主站，数据未发送': ('No master connected, data not sent', 'No hay maestro conectado, datos no enviados'),
    '正在连接 %s:%d …': ('Connecting to %s:%d …', 'Conectando a %s:%d …'),
    '连接失败：%s，3 秒后重试': ('Connection failed: %s, retrying in 3 s', 'Fallo de conexión: %s, reintento en 3 s'),
    '已连接到主站 %s:%d': ('Connected to master %s:%d', 'Conectado al maestro %s:%d'),
    '连接断开，3 秒后重连': ('Disconnected, reconnecting in 3 s', 'Desconectado, reconexión en 3 s'),
    '未连接，数据未发送': ('Not connected, data not sent', 'Sin conexión, datos no enviados'),
    'UDP 已绑定 %s:%d，等待主站数据…': ('UDP bound to %s:%d, waiting for the master…',
                                'UDP enlazado a %s:%d, esperando al maestro…'),
    'UDP 主站：%s:%d': ('UDP master: %s:%d', 'Maestro UDP: %s:%d'),
    '还没有收到过主站数据，也未配置目标地址，数据未发送': (
        'No data from a master yet and no target configured; data not sent',
        'Aún no hay datos de un maestro ni destino configurado; datos no enviados'),

    # ---------------------------------------------------------------- 命令行
    'IEC 62056-21 电表模拟器（命令行版）': ('IEC 62056-21 meter simulator (command line)',
                                  'Simulador de medidor IEC 62056-21 (línea de comandos)'),
    '串口，如 COM3 或 /dev/ttyUSB0': ('Serial port, e.g. COM3 or /dev/ttyUSB0', 'Puerto serie, p. ej. COM3 o /dev/ttyUSB0'),
    '作为 TCP 服务端监听': ('Listen as a TCP server', 'Escuchar como servidor TCP'),
    '作为 TCP 客户端连接主站': ('Connect to the master as a TCP client', 'Conectarse al maestro como cliente TCP'),
    '绑定 UDP 端口': ('Bind a UDP port', 'Enlazar un puerto UDP'),
    'UDP 默认目标（Mode D 推送用）': ('Default UDP target (for Mode D push)', 'Destino UDP por defecto (envío Modo D)'),
    '串口初始波特率（默认按模式：D=2400，其余 300）': (
        'Initial serial baud rate (default by mode: D=2400, others 300)',
        'Velocidad serie inicial (por defecto según modo: D=2400, resto 300)'),
    '串口帧格式，如 7E1 / 8N1': ('Serial frame format, e.g. 7E1 / 8N1', 'Formato de trama serie, p. ej. 7E1 / 8N1'),
    '标识中的波特率字符（默认按模式）': ('Baud character in the identification (default by mode)',
                         'Carácter de velocidad en la identificación (por defecto según modo)'),
    '响应延时 ms': ('Reply delay ms', 'Retardo de respuesta ms'),
    'Mode D 推送间隔秒': ('Mode D push interval in seconds', 'Intervalo de envío del Modo D en segundos'),
    '退出时保存日志（.txt 或 .csv）': ('Save the log on exit (.txt or .csv)', 'Guardar el registro al salir (.txt o .csv)'),
    '日志已保存：%s': ('Log saved: %s', 'Registro guardado: %s'),

    # ---------------------------------------------------------------- 界面
    'IEC 62056-21 电表模拟器': ('IEC 62056-21 Meter Simulator', 'Simulador de medidor IEC 62056-21'),
    '文件': ('File', 'Archivo'),
    '导出日志…': ('Export log…', 'Exportar registro…'),
    '打开日志文件夹': ('Open log folder', 'Abrir carpeta de registros'),
    '退出': ('Quit', 'Salir'),
    '语言': ('Language', 'Idioma'),
    '帮助': ('Help', 'Ayuda'),
    '使用方法': ('How to use', 'Modo de uso'),
    '检查更新…': ('Check for updates…', 'Buscar actualizaciones…'),
    '启动时自动检查更新': ('Check for updates on start-up', 'Buscar actualizaciones al iniciar'),
    '关于': ('About', 'Acerca de'),
    '连接方式': ('Connection', 'Conexión'),
    '方式': ('Type', 'Tipo'),
    '串口': ('Serial', 'Puerto serie'),
    'TCP 服务端': ('TCP server', 'Servidor TCP'),
    'TCP 客户端': ('TCP client', 'Cliente TCP'),
    'UDP': ('UDP', 'UDP'),
    '端口': ('Port', 'Puerto'),
    '刷新': ('Refresh', 'Actualizar'),
    '初始波特率': ('Initial baud', 'Velocidad inicial'),
    '数据位': ('Data bits', 'Bits de datos'),
    '校验': ('Parity', 'Paridad'),
    '停止位': ('Stop bits', 'Bits de parada'),
    '监听地址': ('Listen address', 'Dirección de escucha'),
    '主站地址': ('Master address', 'Dirección del maestro'),
    '本地地址': ('Local address', 'Dirección local'),
    '推送目标(可选) IP:端口': ('Push target (optional) IP:port', 'Destino de envío (opcional) IP:puerto'),
    '▶ 启动': ('▶ Start', '▶ Iniciar'),
    '■ 停止': ('■ Stop', '■ Detener'),
    '未启动': ('Not started', 'Sin iniciar'),
    '电表设置': ('Meter settings', 'Ajustes del medidor'),
    '协议模式': ('Protocol mode', 'Modo de protocolo'),
    '厂商ID(3位)': ('Manufacturer ID (3)', 'ID fabricante (3)'),
    '波特率字符': ('Baud character', 'Carácter de velocidad'),
    '标识串': ('Identification', 'Identificación'),
    '表地址(空=任意)': ('Meter address (empty=any)', 'Dirección (vacía=cualquiera)'),
    '编程口令(空=不校验)': ('Password (empty=no check)', 'Contraseña (vacía=sin control)'),
    'ACK 超时 s': ('ACK timeout s', 'Espera ACK s'),
    '编程会话超时 s': ('Session timeout s', 'Espera de sesión s'),
    '接收时去掉最高位(网络透传 7E1)': ('Strip high bit on receive (7E1 over network)',
                           'Quitar bit alto al recibir (7E1 por red)'),
    'Mode D 推送间隔 s (0=手动)': ('Mode D push interval s (0=manual)', 'Intervalo de envío Modo D s (0=manual)'),
    '立即推送': ('Push now', 'Enviar ahora'),
    '应用设置': ('Apply settings', 'Aplicar ajustes'),
    '运行中修改设置后点「应用设置」生效；串口参数需重新启动': (
        'While running, click "Apply settings" after changes; serial parameters need a restart',
        'En marcha, pulse "Aplicar ajustes" tras cambiar algo; los parámetros serie requieren reiniciar'),
    '连接过程': ('Connection process', 'Proceso de conexión'),
    '会话 —': ('Session —', 'Sesión —'),
    '会话 #%d': ('Session #%d', 'Sesión #%d'),
    '数据项（双击编辑）': ('Data items (double-click to edit)', 'Elementos de datos (doble clic para editar)'),
    '地址 / OBIS': ('Address / OBIS', 'Dirección / OBIS'),
    '值': ('Value', 'Valor'),
    '单位': ('Unit', 'Unidad'),
    '添加': ('Add', 'Añadir'),
    '删除': ('Delete', 'Eliminar'),
    '恢复默认': ('Reset to defaults', 'Restablecer'),
    '交互日志': ('Communication log', 'Registro de comunicación'),
    '显示 HEX': ('Show HEX', 'Mostrar HEX'),
    '只看问题': ('Problems only', 'Solo problemas'),
    '自动保存日志': ('Auto-save log', 'Guardar registro automáticamente'),
    '清空': ('Clear', 'Borrar'),
    '会话 %d 次 · 问题 %d 条 · 日志 %d 条': ('%d sessions · %d problems · %d log entries',
                                    '%d sesiones · %d problemas · %d entradas'),
    '自动保存：%s': ('Auto-saving: %s', 'Guardando en: %s'),
    '问题：%s': ('Problem: %s', 'Problema: %s'),
    '建议：%s': ('Suggestion: %s', 'Sugerencia: %s'),
    'Mode %s 的标准初始波特率是 %d，当前串口为 %s；如需修改请停止后重新启动': (
        'The standard initial baud rate for Mode %s is %d; the port is at %s. Stop and start again to change it',
        'La velocidad inicial estándar del Modo %s es %d; el puerto está a %s. Detenga e inicie de nuevo para cambiarla'),
    '未安装 pyserial，串口不可用（pip install pyserial）；网络模式可正常使用': (
        'pyserial is not installed, serial ports are unavailable (pip install pyserial); network modes still work',
        'pyserial no está instalado, el puerto serie no está disponible (pip install pyserial); la red sí funciona'),
    '厂商ID应为 3 个字母': ('The manufacturer ID should be 3 letters', 'El ID de fabricante debe tener 3 letras'),
    '波特率字符 "%s" 不符合 Mode %s 规定（可选 %s）': (
        'Baud character "%s" is not valid for Mode %s (allowed: %s)',
        'El carácter de velocidad "%s" no es válido para el Modo %s (permitidos: %s)'),
    'Mode A 的波特率字符不能是 0~9、A~I、/、!': ('The Mode A baud character cannot be 0~9, A~I, / or !',
                                       'El carácter de velocidad del Modo A no puede ser 0~9, A~I, / ni !'),
    '响应延时 %d ms 超出标准范围 %d~1500 ms（厂商ID第3个字母%s写→最短 %d ms）': (
        'Reply delay %d ms is outside the standard range %d~1500 ms (3rd letter of manufacturer ID is %s → minimum %d ms)',
        'El retardo %d ms está fuera del rango estándar %d~1500 ms (3.ª letra del ID de fabricante en %s → mínimo %d ms)'),
    '小': ('lowercase', 'minúscula'),
    '大': ('uppercase', 'mayúscula'),
    '设置提示：%s': ('Settings note: %s', 'Nota de ajustes: %s'),
    '设置有误': ('Invalid settings', 'Ajustes no válidos'),
    '请检查数字类设置：%s': ('Please check the numeric settings: %s', 'Revise los ajustes numéricos: %s'),
    '提示': ('Notice', 'Aviso'),
    '请选择串口': ('Please select a serial port', 'Seleccione un puerto serie'),
    '启动失败': ('Failed to start', 'No se pudo iniciar'),
    '已应用设置（Mode %s）': ('Settings applied (Mode %s)', 'Ajustes aplicados (Modo %s)'),
    '请先启动': ('Please start the simulator first', 'Primero inicie el simulador'),
    '日志为空': ('The log is empty', 'El registro está vacío'),
    '导出交互日志': ('Export communication log', 'Exportar registro de comunicación'),
    '文本日志': ('Text log', 'Registro de texto'),
    'CSV 表格（Excel 可打开）': ('CSV table (opens in Excel)', 'Tabla CSV (se abre en Excel)'),
    '导出失败': ('Export failed', 'Error al exportar'),
    '日志已导出：%s': ('Log exported: %s', 'Registro exportado: %s'),
    '自动保存到：%s': ('Auto-saving to: %s', 'Guardando automáticamente en: %s'),
    '切换语言': ('Change language', 'Cambiar idioma'),
    '切换语言需要先停止模拟器，是否继续？': ('Changing the language stops the simulator. Continue?',
                            'Cambiar el idioma detiene el simulador. ¿Continuar?'),
    '关闭': ('Close', 'Cerrar'),

    # ---------------------------------------------------------------- 关于 / 更新
    '版本 %s': ('Version %s', 'Versión %s'),
    '模拟 IEC 62056-21 电表（Mode A~E），用于调试 DTU / 采集器': (
        'Simulates an IEC 62056-21 meter (Mode A~E) for debugging DTUs and data collectors',
        'Simula un medidor IEC 62056-21 (Modo A~E) para depurar DTU y concentradores'),
    '开发者': ('Developer', 'Desarrollador'),
    '联系邮箱': ('Contact', 'Contacto'),
    '网站': ('Website', 'Sitio web'),
    '更新源': ('Update source', 'Fuente de actualizaciones'),
    '未配置': ('Not configured', 'Sin configurar'),
    '运行环境': ('Runtime', 'Entorno'),
    '正在检查更新…': ('Checking for updates…', 'Buscando actualizaciones…'),
    '检查更新': ('Check for updates', 'Buscar actualizaciones'),
    '已是最新版本（%s）': ('You have the latest version (%s)', 'Ya tiene la última versión (%s)'),
    '发现新版本': ('Update available', 'Actualización disponible'),
    '发现新版本 %s（当前 %s）': ('Version %s is available (you have %s)', 'La versión %s está disponible (tiene la %s)'),
    '更新内容：': ('What\'s new:', 'Novedades:'),
    '下载新版本': ('Download', 'Descargar'),
    '稍后提醒': ('Remind me later', 'Recordar más tarde'),
    '跳过此版本': ('Skip this version', 'Omitir esta versión'),
    '未配置更新源（app_info.py 中的 GITHUB_REPO 为空）': (
        'No update source configured (GITHUB_REPO in app_info.py is empty)',
        'No hay fuente de actualizaciones (GITHUB_REPO en app_info.py está vacío)'),
    '还没有发布过版本，或仓库 %s 不是公开仓库': ('No release published yet, or repository %s is not public',
                                   'Aún no hay versiones publicadas, o el repositorio %s no es público'),
    '检查更新失败：HTTP %d': ('Update check failed: HTTP %d', 'Error al buscar actualizaciones: HTTP %d'),
    '检查更新失败：%s': ('Update check failed: %s', 'Error al buscar actualizaciones: %s'),
}
