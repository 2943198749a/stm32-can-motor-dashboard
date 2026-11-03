from pathlib import Path
from datetime import date

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(r"D:\aiguigu\STM32F407\42_lcd_hal")
OUT = ROOT / "docs" / "STM32F103_LVGL_CAN汽车转速仪表盘工程说明.docx"

BLUE = "2E74B5"
DARK_BLUE = "1F4D78"
LIGHT_BLUE = "E8EEF5"
LIGHT_GRAY = "F2F4F7"
CODE_GRAY = "F6F8FA"
GREEN = "2E7D32"
RED = "B3261E"
GOLD = "7A5A00"


def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=80, start=120, bottom=80, end=120):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for margin, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{margin}"))
        if node is None:
            node = OxmlElement(f"w:{margin}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_repeat_table_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def keep_table_row_together(row):
    """禁止 Word/LibreOffice 把同一表格行拆到两页。"""
    tr_pr = row._tr.get_or_add_trPr()
    cant_split = OxmlElement("w:cantSplit")
    cant_split.set(qn("w:val"), "true")
    tr_pr.append(cant_split)


def set_cell_width(cell, width_inches):
    width = int(width_inches * 1440)
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_w = tc_pr.find(qn("w:tcW"))
    if tc_w is None:
        tc_w = OxmlElement("w:tcW")
        tc_pr.append(tc_w)
    tc_w.set(qn("w:w"), str(width))
    tc_w.set(qn("w:type"), "dxa")


def set_table_fixed_layout(table, widths):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    tbl_pr = table._tbl.tblPr
    layout = tbl_pr.find(qn("w:tblLayout"))
    if layout is None:
        layout = OxmlElement("w:tblLayout")
        tbl_pr.append(layout)
    layout.set(qn("w:type"), "fixed")
    for row in table.rows:
        for idx, cell in enumerate(row.cells):
            set_cell_width(cell, widths[idx])
            set_cell_margins(cell)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def set_run_font(run, east_asia="Microsoft YaHei", latin="Calibri", size=None, bold=None, color=None):
    run.font.name = latin
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), east_asia)
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), latin)
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), latin)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if color is not None:
        run.font.color.rgb = RGBColor.from_string(color)


def add_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = paragraph.add_run("第 ")
    set_run_font(run, size=9, color="666666")
    fld_char1 = OxmlElement("w:fldChar")
    fld_char1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld_char2 = OxmlElement("w:fldChar")
    fld_char2.set(qn("w:fldCharType"), "end")
    run._r.append(fld_char1)
    run._r.append(instr)
    run._r.append(fld_char2)
    end = paragraph.add_run(" 页")
    set_run_font(end, size=9, color="666666")


def add_heading(doc, text, level=1):
    p = doc.add_paragraph(style=f"Heading {level}")
    p.paragraph_format.keep_with_next = True
    p.add_run(text)
    return p


def add_body(doc, text, bold_prefix=None):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Pt(22)
    if bold_prefix and text.startswith(bold_prefix):
        r1 = p.add_run(bold_prefix)
        set_run_font(r1, bold=True)
        r2 = p.add_run(text[len(bold_prefix):])
        set_run_font(r2)
    else:
        r = p.add_run(text)
        set_run_font(r)
    return p


def add_bullet(doc, text, level=0):
    p = doc.add_paragraph(style="List Bullet" if level == 0 else "List Bullet 2")
    p.paragraph_format.left_indent = Inches(0.38 + level * 0.25)
    p.paragraph_format.first_line_indent = Inches(-0.19)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(text)
    set_run_font(r)
    return p


def add_number(doc, text, number):
    # 使用显式序号，避免 Word 在不同章节之间延续上一组自动编号。
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.38)
    p.paragraph_format.first_line_indent = Inches(-0.19)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(f"{number}.  {text}")
    set_run_font(r)
    return p


def add_callout(doc, title, text, color=GOLD, fill="FFF8E1"):
    table = doc.add_table(rows=1, cols=1)
    set_table_fixed_layout(table, [6.5])
    cell = table.cell(0, 0)
    set_cell_shading(cell, fill)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run(title)
    set_run_font(r, bold=True, color=color)
    p2 = cell.add_paragraph()
    p2.paragraph_format.space_after = Pt(0)
    r2 = p2.add_run(text)
    set_run_font(r2)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)


def add_code(doc, code, caption=None):
    if caption:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(3)
        r = p.add_run(caption)
        set_run_font(r, bold=True, color=DARK_BLUE, size=9.5)
    table = doc.add_table(rows=1, cols=1)
    set_table_fixed_layout(table, [6.5])
    cell = table.cell(0, 0)
    set_cell_shading(cell, CODE_GRAY)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.0
    r = p.add_run(code.rstrip())
    set_run_font(r, east_asia="Microsoft YaHei", latin="Consolas", size=8.5)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)


def add_table(doc, headers, rows, widths, font_size=9):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    hdr = table.rows[0]
    set_repeat_table_header(hdr)
    keep_table_row_together(hdr)
    for idx, text in enumerate(headers):
        cell = hdr.cells[idx]
        set_cell_shading(cell, LIGHT_BLUE)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(str(text))
        set_run_font(r, bold=True, color=DARK_BLUE, size=font_size)
    for row_data in rows:
        row = table.add_row()
        keep_table_row_together(row)
        cells = row.cells
        for idx, value in enumerate(row_data):
            p = cells[idx].paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(str(value))
            set_run_font(r, size=font_size)
    set_table_fixed_layout(table, widths)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    return table


def add_flow(doc, items):
    table = doc.add_table(rows=1, cols=len(items) * 2 - 1)
    keep_table_row_together(table.rows[0])
    widths = []
    for idx, item in enumerate(items):
        cell = table.cell(0, idx * 2)
        set_cell_shading(cell, LIGHT_BLUE)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(item)
        set_run_font(r, bold=True, color=DARK_BLUE, size=9)
        widths.append(1.0)
        if idx < len(items) - 1:
            arrow = table.cell(0, idx * 2 + 1)
            p2 = arrow.paragraphs[0]
            p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
            rr = p2.add_run("→")
            set_run_font(rr, bold=True, color=BLUE, size=12)
            widths.append(0.375)
    scale = 6.5 / sum(widths)
    set_table_fixed_layout(table, [w * scale for w in widths])
    doc.add_paragraph().paragraph_format.space_after = Pt(0)


def add_function_section(doc, title, signature, purpose, inputs, outputs, calls, notes):
    add_heading(doc, title, 3)
    add_code(doc, signature)
    add_table(
        doc,
        ["项目", "说明"],
        [
            ("功能", purpose),
            ("输入", inputs),
            ("输出/返回", outputs),
            ("主要调用", calls),
            ("注意事项", notes),
        ],
        [1.18, 5.32],
        font_size=8.8,
    )


doc = Document()
section = doc.sections[0]
section.top_margin = Inches(1.0)
section.bottom_margin = Inches(1.0)
section.left_margin = Inches(1.0)
section.right_margin = Inches(1.0)
section.header_distance = Inches(0.492)
section.footer_distance = Inches(0.492)
section.different_first_page_header_footer = True

styles = doc.styles
normal = styles["Normal"]
normal.font.name = "Calibri"
normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
normal.font.size = Pt(11)
normal.paragraph_format.space_after = Pt(6)
normal.paragraph_format.line_spacing = 1.25

for name, size, color, before, after in (
    ("Heading 1", 16, BLUE, 18, 10),
    ("Heading 2", 13, BLUE, 14, 7),
    ("Heading 3", 12, DARK_BLUE, 10, 5),
):
    style = styles[name]
    style.font.name = "Calibri"
    style._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    style.font.size = Pt(size)
    style.font.bold = True
    style.font.color.rgb = RGBColor.from_string(color)
    style.paragraph_format.space_before = Pt(before)
    style.paragraph_format.space_after = Pt(after)
    style.paragraph_format.keep_with_next = True

header = section.header
hp = header.paragraphs[0]
hp.alignment = WD_ALIGN_PARAGRAPH.LEFT
hr = hp.add_run("STM32F103 + LVGL + CAN 汽车转速仪表盘工程说明")
set_run_font(hr, size=8.5, color="777777")
footer = section.footer
add_page_number(footer.paragraphs[0])

props = doc.core_properties
props.title = "STM32F103 LVGL CAN汽车转速仪表盘工程说明"
props.subject = "STM32F103ZET6、ILI9486、FreeRTOS、LVGL 9.5、CAN实时转速显示"
props.author = "工程项目文档"
props.keywords = "STM32F103, LVGL, ILI9486, FreeRTOS, CAN, RPM"

# 封面
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(95)
r = p.add_run("STM32F103 + LVGL + CAN")
set_run_font(r, size=26, bold=True, color=DARK_BLUE)
p2 = doc.add_paragraph()
p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p2.add_run("汽车转速仪表盘工程说明")
set_run_font(r, size=30, bold=True, color=BLUE)
p3 = doc.add_paragraph()
p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
p3.paragraph_format.space_before = Pt(26)
r = p3.add_run("STM32F103ZET6 · ILI9486 480×320 · LVGL 9.5 · FreeRTOS · CAN 100kbps")
set_run_font(r, size=12, color="555555")

cover = doc.add_table(rows=6, cols=2)
cover.style = "Table Grid"
cover.alignment = WD_TABLE_ALIGNMENT.CENTER
cover_data = [
    ("接收控制器", "STM32F103ZET6"),
    ("发送控制器", "STM32F407（编码器采集与 CAN 发送）"),
    ("显示控制器", "ILI9486，480×320，RGB565，FSMC 16 位并口"),
    ("电机", "JGB37-520，12V，额定约 320RPM，减速比 30:1"),
    ("编码器", "13 线 × 30 减速比 × 4 倍频 = 1560 计数/输出轴转"),
    ("文档版本", f"V1.0 · {date.today().isoformat()}"),
]
for i, (a, b) in enumerate(cover_data):
    cover.cell(i, 0).text = a
    cover.cell(i, 1).text = b
    set_cell_shading(cover.cell(i, 0), LIGHT_BLUE)
    for cell in cover.rows[i].cells:
        for run in cell.paragraphs[0].runs:
            set_run_font(run, size=10, bold=(cell is cover.cell(i, 0)))
set_table_fixed_layout(cover, [1.5, 4.5])

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(35)
r = p.add_run("工程路径：D:\\aiguigu\\STM32F407\\42_lcd_hal")
set_run_font(r, latin="Consolas", size=9, color="777777")
doc.add_page_break()

# 阅读说明与目录
add_heading(doc, "阅读说明", 1)
add_body(doc, "本文档以当前已通过 Keil 全量编译并在实物上验证正常的 STM32F103 工程为准。文档重点解释应用代码、外设配置、任务关系、数据协议和故障诊断；HAL、CMSIS、FreeRTOS 和 LVGL 官方库内部实现不逐行展开。")
add_callout(
    doc,
    "重要：CubeMX 配置文件与当前源码存在差异",
    "42_lcd_hal.ioc 中仍记录旧值：LVGL 栈 768 words、Task3 栈 128 words、FreeRTOS 堆 8192 字节；当前已验证源码实际使用 LVGL 栈 1536 words、Task3 栈 256 words、堆 12288 字节。如果重新 Generate Code，必须先在 CubeMX 中同步这些值，或生成后重新核对 freertos.c 与 FreeRTOSConfig.h，否则可能再次出现屏幕固定、串口停止的问题。",
    RED,
    "FDECEC",
)

add_heading(doc, "目录", 1)
toc_items = [
    "1. 工程目标与最终功能",
    "2. 系统总体架构与数据流",
    "3. 硬件组成与接线",
    "4. 系统时钟、GPIO、USART 与 FSMC 配置",
    "5. ILI9486 LCD 底层驱动",
    "6. LVGL 9.5 移植与显示端口",
    "7. FreeRTOS 任务设计与内存配置",
    "8. CAN 通信配置与 0x201 数据协议",
    "9. F407 编码器转速计算与发送端说明",
    "10. 汽车转速仪表盘实现",
    "11. 程序启动时序与运行流程",
    "12. 文件、函数、变量和宏定义详解",
    "13. 编译、下载与运行验证",
    "14. 故障诊断与维护注意事项",
    "附录A. 关键代码片段",
    "附录B. 参数速查表",
]
for item in toc_items:
    p = add_bullet(doc, item)
    # 目录采用紧凑排版，保证全部条目完整地落在同一页。
    p.paragraph_format.space_after = Pt(1)
    p.paragraph_format.line_spacing = 1.0
    for run in p.runs:
        set_run_font(run, size=9.5)
doc.add_page_break()

# 1
add_heading(doc, "1. 工程目标与最终功能", 1)
add_body(doc, "本工程使用 STM32F407 采集 JGB37-520 电机编码器、计算减速箱输出轴实时转速，并以 100kbps CAN 总线发送给 STM32F103ZET6。F103 接收标准帧 ID 0x201，把 RPM×10 数据交给 LVGL，在 ILI9486 480×320 LCD 上显示汽车式圆形转速表。")
add_table(doc, ["功能", "实现结果"], [
    ("电机转速采集", "F407 TIM2 编码器模式，13线×30减速比×4倍频=1560计数/输出轴转"),
    ("速度计算", "50ms 周期计算 RPM，并采用系数 0.25 的一阶低通滤波"),
    ("CAN 发送", "标准数据帧，ID 0x201，DLC=4，周期约 50ms"),
    ("CAN 接收", "F103 精确过滤 0x201，FIFO0 中断接收"),
    ("实时显示", "0.0～400.0 RPM；圆弧和中央数字同步更新"),
    ("红区警告", "达到 320.0 RPM 后指示圆弧变红"),
    ("链路诊断", "500ms 未收到有效帧则归零并显示 CAN LOST"),
    ("串口监视", "USART1 115200 输出帧序号、转速、方向和数据年龄"),
], [1.55, 4.95])
add_body(doc, "仪表盘只显示转速，不显示方向；方向仍保留在 CAN 数据 bit0 和串口日志中，便于以后扩展倒转提示。")

# 2
add_heading(doc, "2. 系统总体架构与数据流", 1)
add_heading(doc, "2.1 硬件数据链路", 2)
add_flow(doc, ["JGB37-520\n编码器", "F407\n计数/算RPM", "CAN收发器\n100kbps", "F103\n接收0x201", "ILI9486\nLVGL仪表"])
add_body(doc, "F407 是转速数据生产者；F103 是转速数据消费者和显示控制器。两块 MCU 之间只通过 CAN 数据协议耦合，因此显示端不需要了解 PWM、电机驱动或编码器硬件细节。")
add_heading(doc, "2.2 软件分层", 2)
add_table(doc, ["层级", "主要文件", "职责"], [
    ("应用界面层", "dashboard.c/.h", "创建仪表盘、显示转速、显示 CAN 状态"),
    ("实时任务层", "freertos.c", "轮询 CAN 快照、调用 LVGL、串口监视"),
    ("通信层", "can.c/.h", "CAN 初始化、过滤器、中断接收、协议解码"),
    ("LVGL 端口层", "lv_port_disp.c/.h", "注册显示、管理 10 行缓冲、刷新回调"),
    ("LCD 驱动层", "lcd.c/.h", "ILI9486 寄存器、窗口、FSMC 命令/数据写入"),
    ("HAL/BSP 层", "fsmc.c、gpio.c、usart.c、stm32f1xx_it.c", "时钟、引脚、中断和外设底层"),
], [1.15, 2.0, 3.35])

# 3
add_heading(doc, "3. 硬件组成与接线", 1)
add_heading(doc, "3.1 主要硬件", 2)
add_table(doc, ["器件", "规格/用途"], [
    ("STM32F103ZET6", "Cortex-M3，72MHz，512KB Flash，64KB SRAM；负责 CAN 接收和 LCD 显示"),
    ("STM32F407", "负责 PWM 驱动、TIM2 编码器计数、RPM 计算和 CAN 发送"),
    ("ILI9486 LCD", "480×320，16位 RGB565，经 FSMC 16位异步 SRAM 接口驱动"),
    ("JGB37-520", "12V 减速直流电机，额定约 320RPM，减速比 30:1"),
    ("增量编码器", "A/B 两相，13线，TIM2 TI12 四倍频"),
    ("CAN 收发器×2", "MCU 逻辑电平与差分 CANH/CANL 之间转换"),
], [1.6, 4.9])

add_heading(doc, "3.2 F103 CAN 接线", 2)
add_table(doc, ["F103 引脚", "连接", "说明"], [
    ("PB8 / CAN_RX", "CAN 收发器 RXD", "接收收发器输出，代码启用 CAN1 Remap2"),
    ("PB9 / CAN_TX", "CAN 收发器 TXD", "向收发器输出 CAN 逻辑信号"),
    ("GND", "收发器 GND、F407 GND", "两块板必须共地"),
    ("CANH", "F407 侧 CANH", "总线高线，只能接 CANH"),
    ("CANL", "F407 侧 CANL", "总线低线，只能接 CANL"),
], [1.35, 2.1, 3.05])
add_callout(doc, "终端电阻", "CAN 总线两端各使用 120Ω 终端电阻。断电测量 CANH 与 CANL，两个 120Ω 并联时通常约为 60Ω。短距离桌面测试也建议保留正确终端。")

add_heading(doc, "3.3 F103 调试串口", 2)
add_table(doc, ["引脚", "功能", "串口参数"], [
    ("PA9", "USART1_TX → USB-TTL RX", "115200 baud"),
    ("PA10", "USART1_RX ← USB-TTL TX（可不接）", "8 data bits"),
    ("GND", "与 USB-TTL 共地", "No parity, 1 stop bit"),
], [1.0, 3.7, 1.8])

add_heading(doc, "3.4 ILI9486 控制引脚与 FSMC", 2)
add_table(doc, ["信号", "STM32F103 引脚", "作用"], [
    ("FSMC_D0…D3", "PD14、PD15、PD0、PD1", "16位数据总线低4位"),
    ("FSMC_D4…D12", "PE7…PE15", "16位数据总线中间9位"),
    ("FSMC_D13…D15", "PD8、PD9、PD10", "16位数据总线高3位"),
    ("FSMC_NOE", "PD4", "读使能"),
    ("FSMC_NWE", "PD5", "写使能"),
    ("FSMC_NE4", "PG12", "Bank4 片选"),
    ("FSMC_A10", "PG0", "接 LCD RS/DC，区分命令与数据"),
    ("LCD_RESET", "PG15", "低脉冲硬件复位"),
    ("LCD_BL", "PB0", "高电平打开背光"),
], [1.35, 2.15, 3.0])

# 4
add_heading(doc, "4. 系统时钟、GPIO、USART 与 FSMC 配置", 1)
add_heading(doc, "4.1 系统时钟", 2)
add_table(doc, ["时钟域", "频率", "来源/用途"], [
    ("HSE", "8MHz", "外部晶振"),
    ("SYSCLK/HCLK", "72MHz", "HSE×9，CPU、AHB、FSMC"),
    ("PCLK1", "36MHz", "APB1，CAN1 和 TIM4 所在总线"),
    ("APB1 Timer", "72MHz", "APB1 分频不为1时，定时器时钟自动×2"),
    ("PCLK2", "72MHz", "USART1 等 APB2 外设"),
], [1.4, 1.2, 3.9])
add_code(doc, "CAN baud = PCLK1 / Prescaler / (1 + BS1 + BS2)\n         = 36,000,000 / 20 / (1 + 13 + 4)\n         = 100,000 bit/s", "CAN 波特率计算")

add_heading(doc, "4.2 FSMC 配置", 2)
add_table(doc, ["参数", "当前值", "含义"], [
    ("Bank", "NOR/SRAM Bank4", "对应基地址 0x6C000000"),
    ("Memory Type", "SRAM", "异步并行存储器时序"),
    ("Data Width", "16 bit", "一次传输一个 RGB565 像素"),
    ("AddressSetupTime", "15", "地址建立周期，当前配置偏保守"),
    ("DataSetupTime", "71", "数据保持周期，保证 LCD 稳定写入"),
    ("AccessMode", "Mode A", "标准异步 SRAM 访问模式"),
], [1.8, 1.7, 3.0])
add_body(doc, "FSMC 把 LCD 映射成内存。CPU 执行一次 16 位指针写操作，FSMC 自动产生 NE4、NWE、地址线和数据线时序，因此 LCD_WriteData() 只有一条赋值语句。")
add_code(doc, "#define LCD_ADDR_CMD  ((uint16_t *)0x6C000000)\n#define LCD_ADDR_DATA ((uint16_t *)(0x6C000000 + (1 << 11)))\n\n命令地址 = 0x6C000000\n数据地址 = 0x6C000800", "FSMC 命令/数据地址")
add_body(doc, "LCD 的 RS/DC 接到 FSMC_A10。16位总线按半字寻址，CPU 地址位相对外部地址线左移1位，因此 A10 对应 CPU 地址偏移 bit11，即 0x800。")

add_heading(doc, "4.3 USART1 与 printf 重定向", 2)
add_code(doc, "int fputc(int ch, FILE *file)\n{\n    (void)file;\n    HAL_UART_Transmit(&huart1, (uint8_t *)&ch, 1, 1000);\n    return ch;\n}")
add_body(doc, "fputc() 把 printf 的每个字符通过 USART1 阻塞发送。为了避免多任务同时进入 HAL_UART_Transmit()，运行期只有 Task3 使用 printf；LVGL 任务不打印。")

# 5
add_heading(doc, "5. ILI9486 LCD 底层驱动", 1)
add_heading(doc, "5.1 初始化顺序", 2)
add_flow(doc, ["LCD_Reset", "LCD_RegConfig", "LCD_SetLandscape", "LCD_ClearAll", "LVGL接管刷新"])
add_body(doc, "LCD_Init() 完成硬件复位、寄存器初始化和背光开启；StartLvglTask() 随后调用 LCD_SetLandscape() 设置已经实物验证正确的横屏/左右镜像方向，再清黑屏。")

add_heading(doc, "5.2 主要 ILI9486 命令", 2)
add_table(doc, ["命令", "名称", "工程用途"], [
    ("0xE0", "Positive Gamma Control", "设置正极性灰阶曲线"),
    ("0xE1", "Negative Gamma Control", "设置负极性灰阶曲线"),
    ("0xC0", "Power Control 1", "配置正/负伽马驱动电压"),
    ("0xC1", "Power Control 2", "配置电源相关参数"),
    ("0xC5", "VCOM Control", "设置公共电极电压"),
    ("0xB1", "Frame Rate Control", "设置正常模式帧率"),
    ("0xB4", "Display Inversion", "设置显示反转方式"),
    ("0xB6", "Display Function", "配置扫描和显示功能"),
    ("0xB7", "Entry Mode", "设置入口模式"),
    ("0x3A", "Pixel Format", "写 0x55，选择 16bit/pixel RGB565"),
    ("0x11", "Sleep Out", "退出休眠，之后等待120ms"),
    ("0x36", "MADCTL", "方向、行列交换和 RGB/BGR；横屏值 0xA8"),
    ("0x29", "Display On", "开启面板显示"),
    ("0x2A", "Column Address Set", "设置 X 起点和终点"),
    ("0x2B", "Page Address Set", "设置 Y 起点和终点"),
    ("0x2C", "Memory Write", "开始连续写入像素数据"),
], [0.8, 2.15, 3.55], font_size=8.5)

add_heading(doc, "5.3 区域写入", 2)
add_body(doc, "LCD_SetArea(x,y,w,h) 先用 0x2A 设置列范围 x～x+w-1，再用 0x2B 设置行范围 y～y+h-1。随后发送 0x2C，连续写入 w×h 个 RGB565 像素。LVGL 刷新回调正是复用这一过程。")

# 6
add_heading(doc, "6. LVGL 9.5 移植与显示端口", 1)
add_heading(doc, "6.1 当前 LVGL 配置", 2)
add_table(doc, ["配置项", "值", "说明"], [
    ("LVGL 版本", "9.5.0-dev", "由 lvgl/lv_version.h 确认"),
    ("LV_COLOR_DEPTH", "16", "RGB565，与 ILI9486 0x3A=0x55 一致"),
    ("LV_MEM_SIZE", "24KB", "LVGL 内部 TLSF 动态内存池"),
    ("分辨率", "480×320", "横屏"),
    ("刷新模式", "PARTIAL", "局部刷新，避免完整帧缓冲"),
    ("显示缓冲", "480×10×2=9600B", "10行、单缓冲、RGB565"),
    ("字体", "Montserrat 14/20/40", "刻度、单位和中央大数字"),
    ("Tick来源", "HAL_GetTick", "lv_tick_set_cb(HAL_GetTick)"),
], [1.65, 1.75, 3.1])

add_heading(doc, "6.2 LV_PortDisp_Init()", 2)
add_number(doc, "调用 lv_display_create(480, 320) 创建逻辑显示设备。", 1)
add_number(doc, "调用 lv_display_set_color_format(...RGB565) 指定像素格式。", 2)
add_number(doc, "注册 LV_PortDisp_Flush() 作为刷新回调。", 3)
add_number(doc, "把 9600 字节缓冲区注册为 PARTIAL 单缓冲。", 4)

add_heading(doc, "6.3 LV_PortDisp_Flush()", 2)
add_code(doc, "pixel_count = (x2 - x1 + 1) * (y2 - y1 + 1);\nLCD_SetArea(x1, y1, width, height);\nLCD_WriteCmd(0x2C);\nwhile(pixel_count > 0) LCD_WriteData(*pixels++);\nlv_display_flush_ready(display);")
add_body(doc, "LVGL 的 area 终点坐标是包含式，因此宽和高必须加1。全部像素写完后必须调用 lv_display_flush_ready()；如果漏掉，LVGL 会一直认为显示器仍在忙，后续画面不再刷新。")

# 7
add_heading(doc, "7. FreeRTOS 任务设计与内存配置", 1)
add_heading(doc, "7.1 任务表", 2)
add_table(doc, ["任务", "优先级", "栈", "周期/阻塞", "职责"], [
    ("defaultTask", "Low", "128×4=512B", "osDelay(1)", "保留 CubeMX 框架，目前无业务"),
    ("lvgl", "Normal", "1536×4=6144B", "osDelay(5)", "LCD/LVGL初始化、CAN状态轮询、界面刷新"),
    ("myTask03", "Normal", "256×4=1024B", "osDelay(200)", "串口打印 CAN 状态和栈/堆诊断"),
], [1.05, 0.85, 1.25, 1.15, 2.2], font_size=8.3)
add_body(doc, "LVGL 和 Task3 同为 Normal 优先级，依靠 FreeRTOS 时间片轮转。两个任务都必须周期性 osDelay()，否则会长期占用 CPU。defaultTask 为 Low，仅在 Normal 任务阻塞时运行。")

add_heading(doc, "7.2 为什么 LVGL 栈必须为 6KB", 2)
add_body(doc, "最初 LVGL 栈为 768×4=3072 字节。首次整屏绘制时画面停在数字4，进度条不动且串口停止，说明系统在 LVGL 深层渲染调用链附近发生栈溢出或 HardFault。LVGL 大量使用函数指针回调，Keil 静态栈分析不能完整覆盖真实调用链。扩大到 1536×4=6144 字节后，动态显示和 Task3 均恢复正常。")
add_callout(doc, "不能只扩大任务栈", "任务栈由 FreeRTOS heap_4 动态分配。只把 LVGL 栈增加 3KB 而仍保持 8KB 总堆，会使剩余堆接近耗尽。因此 configTOTAL_HEAP_SIZE 同时从 8192 增加到 12288 字节。", RED, "FDECEC")

add_heading(doc, "7.3 RAM 与 Flash 使用", 2)
add_table(doc, ["项目", "字节", "说明"], [
    ("Code", "289,836", "可执行机器码"),
    ("RO-data", "112,272", "常量、字体位图等只读数据"),
    ("RW-data", "352", "有初值的全局/静态变量"),
    ("ZI-data", "51,544", "零初始化数据，包括堆、LVGL内存池和显示缓冲"),
    ("Flash合计", "约402,108", "Code+RO-data，低于512KB Flash"),
    ("RAM合计", "51,896", "RW+ZI，低于64KB SRAM，静态余量约13,640B"),
], [1.45, 1.35, 3.7])

# 8
add_heading(doc, "8. CAN 通信配置与 0x201 数据协议", 1)
add_heading(doc, "8.1 CAN1 配置", 2)
add_table(doc, ["参数", "值", "说明"], [
    ("Mode", "Normal", "通过外部收发器接实际 CAN 总线"),
    ("Prescaler", "20", "36MHz CAN时钟分频"),
    ("SJW", "1TQ", "再同步跳转宽度"),
    ("BS1", "13TQ", "采样点之前的时间段"),
    ("BS2", "4TQ", "采样点之后的时间段"),
    ("Bitrate", "100kbps", "两端必须完全一致"),
    ("AutoBusOff", "Enable", "总线错误严重时自动进入 Bus-Off"),
    ("AutoRetransmission", "Enable", "发送失败时自动重发；F103当前主要接收"),
    ("RX IRQ", "USB_LP_CAN1_RX0，优先级5", "FIFO0 新消息中断"),
], [1.7, 1.6, 3.2])

add_heading(doc, "8.2 过滤器", 2)
add_body(doc, "CAN_ReceiveStart() 使用 Bank0、32位 IDMASK 模式。FilterIdHigh=0x201<<5，FilterMaskIdHigh=0x7FF<<5，低半字掩码 0x0006 同时要求 IDE=0 和 RTR=0。因此只有标准数据帧 ID 0x201 能进入 FIFO0。")
add_code(doc, "FilterIdHigh     = 0x201 << 5;\nFilterMaskIdHigh = 0x7FF << 5;\nFilterMaskIdLow  = 0x0006;  // 同时校验 IDE 和 RTR\nFilterFIFO       = FIFO0;")

add_heading(doc, "8.3 数据帧格式", 2)
add_table(doc, ["字节", "位", "含义", "示例"], [
    ("Byte0", "7:0", "RPM×10 低字节", "105.4RPM→1054→0x1E"),
    ("Byte1", "7:0", "RPM×10 高字节", "1054=0x041E→0x04"),
    ("Byte2", "7:0", "循环序号，每帧加1", "152、153、154…"),
    ("Byte3", "bit7", "有效标志，必须为1", "0x80"),
    ("Byte3", "bit0", "方向：0正转，1反转", "FWD=0，REV=1"),
    ("Byte3", "bit6:1", "保留", "当前为0"),
], [0.8, 0.8, 2.9, 2.0])
add_code(doc, "rpm_x10 = data[0] | (data[1] << 8);\nsequence  = data[2];\nreverse   = data[3] & 0x01;\nvalid     = (data[3] & 0x80) != 0;", "F103 解码规则")

add_heading(doc, "8.4 接收中断调用链", 2)
add_flow(doc, ["CAN FIFO0\n收到0x201", "USB_LP_CAN1_RX0\n_IRQHandler", "HAL_CAN\n_IRQHandler", "RxFifo0\nCallback", "更新共享变量"])
add_body(doc, "中断回调不调用 LVGL，也不 printf。它只取出报文、校验协议并更新 volatile 共享变量，从而缩短中断占用时间，避免在中断环境执行不可重入或耗时操作。")

add_heading(doc, "8.5 500ms 超时", 2)
add_code(doc, "can_online = (g_can_data_valid != 0U) &&\n             ((HAL_GetTick() - g_can_last_rx_tick) <= 500U);")
add_body(doc, "F407 正常每50ms发送一帧，500ms 超时相当于允许连续丢失约10个发送周期。超时后仪表显示 0.0 RPM、灰色指示弧和红色 CAN LOST；恢复收到有效帧后自动显示 CAN OK。使用无符号减法可正确处理 HAL tick 回绕。")

# 9
add_heading(doc, "9. F407 编码器转速计算与发送端说明", 1)
add_heading(doc, "9.1 每转计数", 2)
add_code(doc, "CPR = 编码器线数 × 减速比 × 程序倍频\n    = 13 × 30 × 4\n    = 1560 count / 输出轴一转")
add_body(doc, "TIM2 使用 TIM_ENCODERMODE_TI12，对 A/B 两相进行四倍频计数。这里的 1560 是减速箱输出轴一圈对应的计数，而不是电机高速轴一圈。")

add_heading(doc, "9.2 50ms 周期 RPM 公式", 2)
add_code(doc, "raw_rpm = delta_count × 60000 / (1560 × period_ms)\n\n当 period_ms=50：\nraw_rpm = delta_count × 60000 / 78000\n        ≈ delta_count × 0.7692308")
add_body(doc, "F407 每50ms读取并清零 TIM2 计数器，得到该周期增量 delta_count。符号由正反转决定。")

add_heading(doc, "9.3 一阶低通滤波", 2)
add_code(doc, "filtered_rpm = filtered_rpm + 0.25 × (raw_rpm - filtered_rpm)")
add_body(doc, "0.25 的滤波系数让仪表更稳定，同时保留较快响应。绝对值小于0.15RPM时强制归零，消除静止状态下的微小抖动。")

add_heading(doc, "9.4 CAN 发送", 2)
add_body(doc, "F407 的 CAN_SendMotorSpeed(float rpm) 取转速绝对值并四舍五入为 rpm_x10；负转速通过 Byte3 bit0 表示方向。DLC固定为4，StdId固定为0x201，序号每帧自增。发送邮箱满时返回 HAL_BUSY。")

# 10
add_heading(doc, "10. 汽车转速仪表盘实现", 1)
add_heading(doc, "10.1 界面对象", 2)
add_table(doc, ["对象", "LVGL类型", "功能"], [
    ("活动屏幕", "lv_screen_active", "深色不透明背景"),
    ("标题", "lv_label", "MOTOR TACHOMETER"),
    ("dashboard_arc", "lv_arc", "主部件绘灰色底弧，Indicator绘动态转速弧"),
    ("dashboard_rpm_label", "lv_label", "中央一位小数实时转速"),
    ("RPM单位", "lv_label", "显示 RPM"),
    ("dashboard_status_label", "lv_label", "绿色 CAN OK / 红色 CAN LOST"),
    ("5个刻度", "lv_label", "0、100、200、300、400"),
], [1.75, 1.45, 3.3])
add_body(doc, "表盘只创建一个 Arc 对象，LV_PART_MAIN 作为18像素宽灰色底弧，LV_PART_INDICATOR 作为14像素宽彩色指示弧。这样比叠加多个大型圆弧对象更省内存和绘制时间。")

add_heading(doc, "10.2 角度与量程", 2)
add_table(doc, ["参数", "值", "效果"], [
    ("Rotation", "135°", "从左下方开始"),
    ("Background angles", "0°～270°", "底部留90°开口"),
    ("Range", "0～400", "Arc值直接对应整数RPM"),
    ("尺寸", "272×272", "适合480×320横屏中央布局"),
], [1.8, 1.6, 3.1])

add_heading(doc, "10.3 Dashboard_Update()", 2)
add_number(doc, "如果 CAN 离线，把 rpm_x10 强制设为0。", 1)
add_number(doc, "如果在线转速超过4000，把显示值钳位为4000。", 2)
add_number(doc, "用除法和取模拆出整数位与小数位，避免浮点格式化。", 3)
add_number(doc, "用 (rpm_x10+5)/10 四舍五入得到 Arc 整数值。", 4)
add_number(doc, "在线且低于3200时使用青蓝色；达到3200后变红。", 5)
add_number(doc, "离线时显示 CAN LOST，并把指示弧改成灰色。", 6)
add_code(doc, "rpm_integer = rpm_x10 / 10U;\nrpm_decimal = rpm_x10 % 10U;\narc_value = (rpm_x10 + 5U) / 10U;\nlv_label_set_text_fmt(label, \"%u.%u\", rpm_integer, rpm_decimal);")

add_heading(doc, "10.4 减少无效重绘", 2)
add_body(doc, "StartLvglTask() 保存 last_display_rpm_x10 和 last_can_online。只有数值或状态改变才调用 Dashboard_Update()。CAN帧约50ms更新一次，而任务每20ms检查一次；这种设计既能快速发现新帧，又不会每20ms重复绘制完全相同的画面。")

# 11
add_heading(doc, "11. 程序启动时序与运行流程", 1)
add_heading(doc, "11.1 上电启动", 2)
for number, step in enumerate([
    "HAL_Init() 复位 HAL 状态并建立基础中断环境。",
    "SystemClock_Config() 把系统配置为72MHz。",
    "MX_GPIO_Init() 配置背光 PB0、复位 PG15 等引脚。",
    "MX_FSMC_Init() 配置16位 Bank4 LCD总线。",
    "MX_USART1_UART_Init() 配置115200调试串口。",
    "MX_CAN_Init() 配置100kbps CAN1和PB8/PB9重映射。",
    "CAN_ReceiveStart() 配置0x201过滤、启动CAN、打开FIFO0中断。",
    "osKernelInitialize() 初始化RTOS内核。",
    "MX_FREERTOS_Init() 创建三个任务并打印创建结果。",
    "osKernelStart() 启动调度器。",
], start=1):
    add_number(doc, step, number)

add_heading(doc, "11.2 LVGL 任务运行", 2)
add_flow(doc, ["LCD初始化", "LVGL初始化", "创建显示端口", "创建仪表盘", "20ms读CAN", "lv_timer_handler"])
add_body(doc, "每次循环最后调用 lv_timer_handler()，然后 osDelay(5)。lv_timer_handler() 负责执行 LVGL 定时器、布局、无效区域重绘和 LV_PortDisp_Flush()。")

add_heading(doc, "11.3 Task3 串口监视", 2)
add_body(doc, "Task3 启动后先等待1秒，让首次整屏刷新完成。之后每200ms读取共享 CAN 快照并打印。AGE 表示当前时刻距离最近有效帧的毫秒数；AGE 持续小于500表示链路活跃。")
add_code(doc, "CAN RX SEQ:152 RPM:105.4 DIR:FWD AGE:45\nCAN RX SEQ:156 RPM:105.6 DIR:FWD AGE:42")

# 12
add_heading(doc, "12. 文件、函数、变量和宏定义详解", 1)
add_heading(doc, "12.1 文件职责", 2)
add_table(doc, ["文件", "类型", "职责/维护建议"], [
    ("main.c", "CubeMX+USER", "外设初始化、CAN启动、RTOS启动、时钟配置"),
    ("freertos.c", "CubeMX+USER", "任务属性和业务循环；重新生成前必须同步栈配置"),
    ("can.c/.h", "CubeMX+USER", "CAN底层配置、过滤器、接收回调和共享变量"),
    ("dashboard.c/.h", "自定义", "汽车仪表盘全部对象和更新逻辑"),
    ("lv_port_disp.c/.h", "自定义", "LVGL与ILI9486之间的显示适配"),
    ("lcd.c/.h", "自定义/现成驱动", "ILI9486寄存器、FSMC访问和基础绘图"),
    ("fsmc.c", "CubeMX", "FSMC Bank4和GPIO复用配置"),
    ("gpio.c", "CubeMX", "背光、LCD复位等GPIO"),
    ("usart.c", "CubeMX+USER", "USART1和printf重定向"),
    ("stm32f1xx_it.c", "CubeMX", "CAN RX0和TIM4中断入口"),
    ("lvgl/lv_conf.h", "LVGL配置", "颜色、内存、字体、控件和日志开关"),
    ("FreeRTOSConfig.h", "RTOS配置", "12KB堆、栈检测、任务相关内核参数"),
], [1.75, 1.2, 3.55], font_size=8.3)

add_heading(doc, "12.2 核心函数逐项说明", 2)
add_function_section(doc, "main()", "int main(void)", "完成HAL、时钟、GPIO、FSMC、USART、CAN和FreeRTOS启动。", "无", "正常情况下不返回", "HAL_Init、SystemClock_Config、各MX_Init、CAN_ReceiveStart、osKernelStart", "CAN启动失败时进入 Error_Handler；调度器启动后不会回到 while(1)。")
add_function_section(doc, "SystemClock_Config()", "void SystemClock_Config(void)", "把8MHz HSE经PLL×9配置成72MHz系统时钟。", "无", "无；失败进入Error_Handler", "HAL_RCC_OscConfig、HAL_RCC_ClockConfig", "APB1必须保持36MHz，CAN波特率计算依赖此值。")
add_function_section(doc, "MX_CAN_Init()", "void MX_CAN_Init(void)", "配置CAN1位时序、正常模式、自动Bus-Off和自动重传。", "无", "无", "HAL_CAN_Init", "只完成外设初始化；过滤器、中断和启动由 CAN_ReceiveStart 完成。")
add_function_section(doc, "CAN_ReceiveStart()", "HAL_StatusTypeDef CAN_ReceiveStart(void)", "精确过滤0x201标准数据帧，启动CAN1并打开FIFO0消息中断。", "无", "HAL_OK或HAL_ERROR", "HAL_CAN_ConfigFilter、HAL_CAN_Start、HAL_CAN_ActivateNotification", "三个步骤任一步失败都会返回HAL_ERROR。")
add_function_section(doc, "HAL_CAN_RxFifo0MsgPendingCallback()", "void HAL_CAN_RxFifo0MsgPendingCallback(CAN_HandleTypeDef *can_handle)", "在中断上下文取帧、校验协议并更新共享转速。", "CAN句柄", "无", "HAL_CAN_GetRxMessage、HAL_GetTick", "禁止在这里调用LVGL和printf；DLC必须等于4且Byte3 bit7必须为1。")
add_function_section(doc, "MX_FREERTOS_Init()", "void MX_FREERTOS_Init(void)", "创建defaultTask、lvgl和myTask03，并打印任务创建结果。", "无", "无", "osThreadNew、xPortGetFreeHeapSize", "任何任务句柄为NULL都说明动态内存不足。")
add_function_section(doc, "StartLvglTask()", "void StartLvglTask(void *argument)", "初始化LCD/LVGL，创建仪表，轮询CAN并持续处理LVGL刷新。", "未使用的任务参数", "不返回", "LCD_Init、lv_init、LV_PortDisp_Init、Dashboard_Init/Update、lv_timer_handler", "只有此任务可以调用LVGL对象API；栈必须保持6144B。")
add_function_section(doc, "StartTask03()", "void StartTask03(void *argument)", "每200ms打印CAN在线状态、帧序号、转速、方向和AGE。", "未使用的任务参数", "不返回", "printf、uxTaskGetStackHighWaterMark、xPortGetFreeHeapSize", "运行期UART日志由该任务独占，避免printf并发。")
add_function_section(doc, "LV_PortDisp_Init()", "lv_display_t *LV_PortDisp_Init(void)", "创建480×320 RGB565显示设备并注册局部缓冲和刷新回调。", "无", "显示对象或NULL", "lv_display_create、set_color_format、set_flush_cb、set_buffers", "使用10行单缓冲和PARTIAL模式。")
add_function_section(doc, "LV_PortDisp_Flush()", "static void LV_PortDisp_Flush(lv_display_t *display, const lv_area_t *area, uint8_t *pixel_map)", "把LVGL渲染的矩形像素块通过FSMC写入ILI9486。", "显示对象、区域、像素指针", "无", "LCD_SetArea、LCD_WriteCmd/Data、lv_display_flush_ready", "必须在结尾调用flush_ready；pixel_map按uint16_t RGB565解释。")
add_function_section(doc, "Dashboard_Init()", "void Dashboard_Init(void)", "创建背景、标题、单圆弧、转速数字、单位、CAN状态和刻度。", "无", "无", "lv_arc_create、lv_label_create、各种style API", "只在LVGL初始化后调用一次；上电初始状态为CAN LOST。")
add_function_section(doc, "Dashboard_Update()", "void Dashboard_Update(uint16_t rpm_x10, uint8_t can_online)", "更新圆弧数值、中央一位小数、红区颜色和CAN状态。", "RPM×10、在线标志", "无", "lv_arc_set_value、lv_label_set_text_fmt、style color", "离线归零；在线值钳位4000；只能在LVGL任务调用。")
add_function_section(doc, "LCD_Init()", "void LCD_Init(void)", "复位ILI9486、写寄存器并打开背光。", "无", "无", "LCD_Reset、LCD_RegConfig、LCD_BGOn", "FSMC必须先初始化。")
add_function_section(doc, "LCD_SetArea()", "void LCD_SetArea(uint16_t x, uint16_t y, uint16_t w, uint16_t h)", "设置ILI9486列和页地址窗口。", "起点坐标、宽、高", "无", "LCD_WriteCmd、LCD_WriteData", "w和h必须大于0；终点计算为起点+尺寸-1。")
add_function_section(doc, "LCD_WriteCmd()/LCD_WriteData()", "void LCD_WriteCmd(uint16_t cmd)\nvoid LCD_WriteData(uint16_t data)", "通过两个FSMC映射地址分别写命令或数据。", "16位命令/数据", "无", "内存映射指针写", "地址偏移由A10和16位寻址共同决定。")
add_function_section(doc, "fputc()", "int fputc(int ch, FILE *file)", "把printf字符重定向到USART1。", "字符和FILE指针", "返回已发送字符", "HAL_UART_Transmit", "阻塞发送，避免多个任务同时printf。")

add_heading(doc, "12.3 共享变量", 2)
add_table(doc, ["变量", "类型", "写入者", "读取者", "意义"], [
    ("g_can_rpm_x10", "volatile uint16_t", "CAN中断", "LVGL/Task3", "转速绝对值，单位0.1RPM"),
    ("g_can_sequence", "volatile uint8_t", "CAN中断", "Task3", "F407发送序号"),
    ("g_can_reverse", "volatile uint8_t", "CAN中断", "Task3", "0正转、1反转"),
    ("g_can_data_valid", "volatile uint8_t", "CAN中断", "LVGL/Task3", "是否曾收到有效协议帧"),
    ("g_can_last_rx_tick", "volatile uint32_t", "CAN中断", "LVGL/Task3", "最近有效帧的毫秒时间"),
], [1.55, 1.25, 1.0, 1.05, 1.65], font_size=8.2)

add_heading(doc, "12.4 关键宏定义", 2)
add_table(doc, ["宏", "值", "作用"], [
    ("DASHBOARD_UPDATE_PERIOD_MS", "20U", "CAN数据检查周期"),
    ("DASHBOARD_CAN_TIMEOUT_MS", "500U", "CAN掉线判定"),
    ("DASHBOARD_RPM_MAX_X10", "4000U", "仪表最大400.0RPM"),
    ("DASHBOARD_RED_RPM_X10", "3200U", "320.0RPM进入红区"),
    ("LV_PORT_DISP_BUF_LINES", "10U", "LVGL缓冲高度"),
    ("LV_MEM_SIZE", "24×1024U", "LVGL内部内存池"),
    ("configTOTAL_HEAP_SIZE", "12288", "FreeRTOS动态堆"),
    ("LCD_W / LCD_H", "480 / 320", "横屏分辨率"),
    ("LCD_MADCTL_LANDSCAPE", "0xA8", "横屏和镜像方向"),
], [2.35, 1.35, 2.8], font_size=8.5)

# 13
add_heading(doc, "13. 编译、下载与运行验证", 1)
add_heading(doc, "13.1 Keil 编译", 2)
add_number(doc, "打开 MDK-ARM/42_lcd_hal.uvprojx。", 1)
add_number(doc, "按 F7 或 Rebuild，等待链接和 FromELF 生成HEX。", 2)
add_number(doc, "确认输出为 0 Error(s), 0 Warning(s)。", 3)
add_number(doc, "确认 Program Size 没有超过 STM32F103ZET6 的Flash和SRAM。", 4)
add_code(doc, "Program Size: Code=289836 RO-data=112272 RW-data=352 ZI-data=51544\n0 Error(s), 0 Warning(s)")

add_heading(doc, "13.2 下载与观察", 2)
add_number(doc, "连接ST-Link，选择正确的STM32F103ZET6目标和Flash算法。", 1)
add_number(doc, "按F8下载，然后按开发板复位键。", 2)
add_number(doc, "确认LCD出现圆形仪表、0～400刻度和CAN状态。", 3)
add_number(doc, "启动F407电机程序并确认串口持续收到CAN RX。", 4)
add_number(doc, "改变电机转速，观察中央数字和圆弧同步变化。", 5)

add_heading(doc, "13.3 正常串口日志", 2)
add_code(doc, "CAN START OK\nTASK CREATE default:OK lvgl:OK task3:OK HEAP:xxxx\nCAN monitor task started HEAP:xxxx STACK:xxx\nCAN RX SEQ:152 RPM:105.4 DIR:FWD AGE:45")
add_table(doc, ["字段", "解释"], [
    ("SEQ", "Byte2序号；连续变化说明F407持续发送"),
    ("RPM", "解码后的真实转速，保留一位小数"),
    ("DIR", "FWD正转、REV反转"),
    ("AGE", "距离最后有效帧的毫秒数；应小于500"),
    ("HEAP", "FreeRTOS当前剩余堆"),
    ("STACK", "Task3历史最小剩余栈，单位word"),
], [1.2, 5.3])

# 14
add_heading(doc, "14. 故障诊断与维护注意事项", 1)
add_heading(doc, "14.1 故障速查", 2)
add_table(doc, ["现象", "最可能原因", "检查方法/处理"], [
    ("屏幕全黑", "背光、复位、FSMC或LCD初始化失败", "测PB0、PG15；先运行红绿蓝纯色测试；核对NE4/A10/NWE"),
    ("画面左右镜像", "MADCTL方向值不匹配", "保持当前已验证0xA8；不要随意改0x36数据"),
    ("画面固定、串口停止", "LVGL任务栈不足或HardFault", "确认lvgl栈=1536×4、FreeRTOS堆=12288；在HardFault和栈钩子下断点"),
    ("有仪表但CAN LOST", "未收到0x201有效帧", "检查100kbps、CANH/L、共地、终端、F407是否运行"),
    ("串口只有CAN START OK", "任务未创建或调度器/任务故障", "检查TASK CREATE三项、HEAP、任务栈、osDelay"),
    ("SEQ不变化", "F407未持续发送或总线错误", "检查发送任务50ms周期、邮箱、HAL_CAN_GetError"),
    ("RPM为0但电机转", "编码器接线/计数器/CPR错误", "查看F407 ENC打印，检查TIM2 A/B相和1560 CPR"),
    ("RPM比例不对", "13线、30减速比或4倍频理解错误", "按实际编码器规格重新计算CPR"),
    ("RPM跳动", "编码器噪声或采样过短", "检查屏蔽/共地/滤波；调整F407输入滤波或低通系数"),
    ("偶发CAN LOST", "总线干扰、终端不对或发送周期阻塞", "断电测约60Ω；缩短支线；检查AGE和错误码"),
], [1.45, 2.05, 3.0], font_size=7.9)

add_heading(doc, "14.2 CubeMX 重新生成代码", 2)
add_callout(doc, "必须先同步 .ioc", "当前 .ioc 仍保存旧的 FreeRTOS 堆和任务栈。如果直接 Generate Code，可能覆盖 freertos.c 中的任务属性以及 FreeRTOSConfig.h 中的堆大小。建议在 CubeMX 中把 lvgl stack 改为1536 words、myTask03改为256 words、TOTAL_HEAP_SIZE改为12288，再生成。生成后重新运行验证脚本和Keil全量编译。", RED, "FDECEC")
add_body(doc, "自定义逻辑尽量位于 USER CODE BEGIN/END 内。dashboard.c、lv_port_disp.c 和 lcd.c 为自定义文件，通常不会被 CubeMX 重写；main.c、freertos.c、can.c、usart.c 和中断文件属于生成文件，需要特别注意 USER CODE 区域。")

add_heading(doc, "14.3 调试断点建议", 2)
add_table(doc, ["断点位置", "可确认的问题"], [
    ("CAN_ReceiveStart()每个HAL返回处", "过滤器、CAN启动或中断激活失败"),
    ("HAL_CAN_RxFifo0MsgPendingCallback()", "是否真正收到报文、ID/DLC/Byte3是否正确"),
    ("StartLvglTask()的Dashboard_Update", "CAN快照是否进入显示逻辑"),
    ("LV_PortDisp_Flush()", "LVGL是否产生刷新区域，area是否合理"),
    ("HardFault_Handler()", "非法访问或严重栈问题"),
    ("vApplicationStackOverflowHook()", "FreeRTOS检测到任务栈溢出"),
    ("vApplicationMallocFailedHook()", "FreeRTOS动态堆不足"),
], [2.35, 4.15])

add_heading(doc, "14.4 后续扩展建议", 2)
for item in [
    "在CAN协议中增加CRC或简单校验字节，提高数据完整性判断能力。",
    "把CAN错误码、Bus-Off状态和累计丢帧数显示在调试页面。",
    "增加峰值转速、平均转速和运行时间，但保持主页面只显示RPM。",
    "使用队列或双缓冲结构保存完整CAN快照；当共享数据字段继续增加时可避免跨字段瞬时不一致。",
    "若提高刷新速度，可评估FSMC时序、DMA或双显示缓冲，但每次优化必须先做稳定性测试。",
    "在F407加入发送失败计数和Bus-Off恢复策略。",
]:
    add_bullet(doc, item)

# 附录
add_heading(doc, "附录A. 关键代码片段", 1)
add_heading(doc, "A.1 CAN 到仪表盘", 2)
add_code(doc, "now = HAL_GetTick();\nrpm_x10 = g_can_rpm_x10;\nlast_rx_tick = g_can_last_rx_tick;\n\nif((g_can_data_valid != 0U) &&\n   ((now - last_rx_tick) <= 500U)) {\n    can_online = 1U;\n} else {\n    can_online = 0U;\n    rpm_x10 = 0U;\n}\n\nif((rpm_x10 != last_display_rpm_x10) ||\n   (can_online != last_can_online)) {\n    Dashboard_Update(rpm_x10, can_online);\n}")

add_heading(doc, "A.2 CAN 回调解码", 2)
add_code(doc, "if((rx_header.IDE == CAN_ID_STD) &&\n   (rx_header.RTR == CAN_RTR_DATA) &&\n   (rx_header.StdId == 0x201U) &&\n   (rx_header.DLC == 4U) &&\n   ((rx_data[3] & 0x80U) != 0U)) {\n    g_can_rpm_x10 = rx_data[0] | ((uint16_t)rx_data[1] << 8);\n    g_can_sequence = rx_data[2];\n    g_can_reverse = rx_data[3] & 0x01U;\n    g_can_last_rx_tick = HAL_GetTick();\n    g_can_data_valid = 1U;\n}")

add_heading(doc, "A.3 LVGL 刷新", 2)
add_code(doc, "LCD_SetArea(area->x1, area->y1,\n            area->x2 - area->x1 + 1,\n            area->y2 - area->y1 + 1);\nLCD_WriteCmd(0x2CU);\nwhile(pixel_count > 0U) {\n    LCD_WriteData(*pixels++);\n    pixel_count--;\n}\nlv_display_flush_ready(display);")

add_heading(doc, "附录B. 参数速查表", 1)
add_table(doc, ["类别", "参数", "当前值"], [
    ("MCU", "F103型号", "STM32F103ZET6"),
    ("时钟", "SYSCLK/APB1/APB2", "72/36/72MHz"),
    ("CAN", "波特率", "100kbps"),
    ("CAN", "ID / 类型 / DLC", "0x201 / 标准数据帧 / 4"),
    ("CAN", "超时", "500ms"),
    ("发送", "F407周期", "50ms"),
    ("显示", "ILI9486分辨率", "480×320"),
    ("显示", "像素格式", "RGB565，16bit"),
    ("显示", "MADCTL", "0xA8"),
    ("LVGL", "版本 / 内存池", "9.5.0-dev / 24KB"),
    ("LVGL", "缓冲", "480×10×2=9600B"),
    ("仪表", "量程 / 红区", "0～400RPM / 320RPM"),
    ("FreeRTOS", "总堆", "12288B"),
    ("FreeRTOS", "LVGL任务栈", "6144B"),
    ("串口", "USART1", "115200-8-N-1"),
    ("编码器", "CPR", "13×30×4=1560"),
    ("电机", "规格", "JGB37-520，12V，约320RPM"),
], [1.1, 2.45, 2.95], font_size=8.5)

add_callout(doc, "最终维护原则", "先保证 CAN 接收和串口连续，再验证 LCD 底层，最后运行 LVGL 仪表。任何涉及任务栈、堆、显示缓冲、FSMC时序和CAN位时序的修改，都必须重新全量编译并进行实物连续运行测试。", GREEN, "E8F5E9")

# 统一字体并设置段落属性
for paragraph in doc.paragraphs:
    for run in paragraph.runs:
        if run.font.name is None:
            set_run_font(run)

OUT.parent.mkdir(parents=True, exist_ok=True)
doc.save(OUT)
print(OUT)
