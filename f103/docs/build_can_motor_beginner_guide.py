from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "STM32双板CAN电机测速与LVGL显示问题排查入门教程.docx"

BLUE = "2E74B5"
DARK_BLUE = "1F4D78"
INK = "0B2545"
MUTED = "667085"
LIGHT_BLUE = "E8EEF5"
LIGHT_GRAY = "F2F4F7"
NOTE_FILL = "F4F6F9"
WARN_FILL = "FFF4CE"
RISK = "9B1C1C"
GREEN = "1F6B45"
WHITE = "FFFFFF"


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
    for m, v in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{m}"))
        if node is None:
            node = OxmlElement(f"w:{m}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(v))
        node.set(qn("w:type"), "dxa")


def set_table_borders(table, color="B8C2CC", size="6"):
    tbl_pr = table._tbl.tblPr
    borders = tbl_pr.first_child_found_in("w:tblBorders")
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = qn(f"w:{edge}")
        node = borders.find(tag)
        if node is None:
            node = OxmlElement(f"w:{edge}")
            borders.append(node)
        node.set(qn("w:val"), "single")
        node.set(qn("w:sz"), size)
        node.set(qn("w:color"), color)


def set_table_geometry(table, widths_inches, indent_dxa=120):
    widths_dxa = [int(round(v * 1440)) for v in widths_inches]
    total = sum(widths_dxa)
    table.autofit = False
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    tbl_pr = table._tbl.tblPr

    tbl_w = tbl_pr.first_child_found_in("w:tblW")
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl_pr.append(tbl_w)
    tbl_w.set(qn("w:w"), str(total))
    tbl_w.set(qn("w:type"), "dxa")

    tbl_ind = tbl_pr.first_child_found_in("w:tblInd")
    if tbl_ind is None:
        tbl_ind = OxmlElement("w:tblInd")
        tbl_pr.append(tbl_ind)
    tbl_ind.set(qn("w:w"), str(indent_dxa))
    tbl_ind.set(qn("w:type"), "dxa")

    grid = table._tbl.tblGrid
    for child in list(grid):
        grid.remove(child)
    for width in widths_dxa:
        col = OxmlElement("w:gridCol")
        col.set(qn("w:w"), str(width))
        grid.append(col)

    for row in table.rows:
        for idx, cell in enumerate(row.cells):
            width = widths_dxa[min(idx, len(widths_dxa) - 1)]
            tc_pr = cell._tc.get_or_add_tcPr()
            tc_w = tc_pr.first_child_found_in("w:tcW")
            if tc_w is None:
                tc_w = OxmlElement("w:tcW")
                tc_pr.append(tc_w)
            tc_w.set(qn("w:w"), str(width))
            tc_w.set(qn("w:type"), "dxa")
            cell.width = Inches(width / 1440)
            set_cell_margins(cell)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def set_repeat_table_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def prevent_row_split(row):
    tr_pr = row._tr.get_or_add_trPr()
    cant_split = OxmlElement("w:cantSplit")
    cant_split.set(qn("w:val"), "true")
    tr_pr.append(cant_split)


def set_run_font(run, size=None, bold=None, color=None, name="Calibri", east_asia="Microsoft YaHei"):
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), name)
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), name)
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), east_asia)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if color is not None:
        run.font.color.rgb = RGBColor.from_string(color)


def set_paragraph_keep(paragraph, keep_next=False, keep_lines=True):
    p_pr = paragraph._p.get_or_add_pPr()
    if keep_next:
        node = OxmlElement("w:keepNext")
        p_pr.append(node)
    if keep_lines:
        node = OxmlElement("w:keepLines")
        p_pr.append(node)


def set_paragraph_shading(paragraph, fill, border=None):
    p_pr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    p_pr.append(shd)
    if border:
        p_bdr = OxmlElement("w:pBdr")
        left = OxmlElement("w:left")
        left.set(qn("w:val"), "single")
        left.set(qn("w:sz"), "18")
        left.set(qn("w:space"), "8")
        left.set(qn("w:color"), border)
        p_bdr.append(left)
        p_pr.append(p_bdr)


def add_page_field(paragraph):
    run = paragraph.add_run()
    fld_char1 = OxmlElement("w:fldChar")
    fld_char1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld_char2 = OxmlElement("w:fldChar")
    fld_char2.set(qn("w:fldCharType"), "end")
    run._r.extend([fld_char1, instr, fld_char2])
    set_run_font(run, size=9, color=MUTED)


def configure_styles(doc):
    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Calibri"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Calibri")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    normal.font.size = Pt(11)
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.25

    for name, size, color, before, after in (
        ("Heading 1", 16, BLUE, 18, 10),
        ("Heading 2", 13, BLUE, 14, 7),
        ("Heading 3", 12, DARK_BLUE, 10, 5),
    ):
        style = styles[name]
        style.font.name = "Calibri"
        style._element.rPr.rFonts.set(qn("w:ascii"), "Calibri")
        style._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor.from_string(color)
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.paragraph_format.keep_with_next = True

    for name in ("List Bullet", "List Number"):
        style = styles[name]
        style.font.name = "Calibri"
        style._element.rPr.rFonts.set(qn("w:ascii"), "Calibri")
        style._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
        style.font.size = Pt(11)
        style.paragraph_format.left_indent = Inches(0.375)
        style.paragraph_format.first_line_indent = Inches(-0.188)
        style.paragraph_format.space_after = Pt(4)
        style.paragraph_format.line_spacing = 1.25

    if "Code Block" not in styles:
        code = styles.add_style("Code Block", WD_STYLE_TYPE.PARAGRAPH)
    else:
        code = styles["Code Block"]
    code.font.name = "Consolas"
    code._element.rPr.rFonts.set(qn("w:ascii"), "Consolas")
    code._element.rPr.rFonts.set(qn("w:hAnsi"), "Consolas")
    code._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    code.font.size = Pt(9)
    code.paragraph_format.left_indent = Inches(0.15)
    code.paragraph_format.right_indent = Inches(0.15)
    code.paragraph_format.space_before = Pt(4)
    code.paragraph_format.space_after = Pt(7)
    code.paragraph_format.line_spacing = 1.05


def add_body(doc, text, bold_prefix=None):
    p = doc.add_paragraph()
    if bold_prefix and text.startswith(bold_prefix):
        r1 = p.add_run(bold_prefix)
        set_run_font(r1, bold=True, color=INK)
        r2 = p.add_run(text[len(bold_prefix):])
        set_run_font(r2)
    else:
        r = p.add_run(text)
        set_run_font(r)
    return p


def add_bullet(doc, text, level=0):
    p = doc.add_paragraph(style="List Bullet" if level == 0 else "List Bullet 2")
    r = p.add_run(text)
    set_run_font(r)
    return p


def add_number(doc, text):
    p = doc.add_paragraph(style="List Number")
    r = p.add_run(text)
    set_run_font(r)
    return p


def add_numbered_list(doc, items):
    """Create a visually stable list that restarts at 1 in Word and LibreOffice."""
    for index, text in enumerate(items, start=1):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.34)
        p.paragraph_format.first_line_indent = Inches(-0.22)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.25
        r = p.add_run(f"{index}.  {text}")
        set_run_font(r)


def add_code(doc, code):
    p = doc.add_paragraph(style="Code Block")
    p.paragraph_format.keep_together = True
    set_paragraph_shading(p, "F7F8FA", border="AAB7C4")
    for idx, line in enumerate(code.strip("\n").splitlines()):
        if idx:
            p.add_run().add_break()
        r = p.add_run(line)
        set_run_font(r, size=9, name="Consolas", east_asia="Microsoft YaHei")
    return p


def add_callout(doc, label, text, kind="note"):
    fill = NOTE_FILL if kind == "note" else WARN_FILL
    border = BLUE if kind == "note" else "C28B00"
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.12)
    p.paragraph_format.right_indent = Inches(0.08)
    p.paragraph_format.space_before = Pt(5)
    p.paragraph_format.space_after = Pt(8)
    set_paragraph_shading(p, fill, border)
    r1 = p.add_run(f"{label}  ")
    set_run_font(r1, bold=True, color=DARK_BLUE if kind == "note" else "7A5A00")
    r2 = p.add_run(text)
    set_run_font(r2)
    return p


def add_table(doc, headers, rows, widths, header_fill=LIGHT_BLUE):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    for idx, header in enumerate(headers):
        cell = table.rows[0].cells[idx]
        set_cell_shading(cell, header_fill)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(header)
        set_run_font(r, size=10, bold=True, color=INK)
    set_repeat_table_header(table.rows[0])
    for row_data in rows:
        cells = table.add_row().cells
        for idx, value in enumerate(row_data):
            p = cells[idx].paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(str(value))
            set_run_font(r, size=10)
    for row in table.rows:
        prevent_row_split(row)
    set_table_geometry(table, widths)
    set_table_borders(table)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    return table


def setup_header_footer(section, first=False):
    section.different_first_page_header_footer = True
    header = section.header
    p = header.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r = p.add_run("STM32 双板 CAN 电机测速与 LVGL 显示 · 初学者排查指南")
    set_run_font(r, size=9, color=MUTED)
    p.paragraph_format.space_after = Pt(0)
    p_pr = p._p.get_or_add_pPr()
    p_bdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "4")
    bottom.set(qn("w:color"), "D7DBE2")
    p_bdr.append(bottom)
    p_pr.append(p_bdr)

    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = p.add_run("第 ")
    set_run_font(r, size=9, color=MUTED)
    add_page_field(p)
    r = p.add_run(" 页")
    set_run_font(r, size=9, color=MUTED)


def add_heading(doc, level, text):
    p = doc.add_paragraph(text, style=f"Heading {level}")
    set_paragraph_keep(p, keep_next=True)
    for r in p.runs:
        set_run_font(r, size={1: 16, 2: 13, 3: 12}[level], bold=True,
                     color={1: BLUE, 2: BLUE, 3: DARK_BLUE}[level])
    return p


def add_page_break(doc):
    p = doc.add_paragraph()
    p.add_run().add_break(WD_BREAK.PAGE)


def build():
    doc = Document()
    configure_styles(doc)

    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    section.header_distance = Inches(0.492)
    section.footer_distance = Inches(0.492)
    setup_header_footer(section)

    # Editorial cover header pattern.
    for _ in range(5):
        doc.add_paragraph().paragraph_format.space_after = Pt(8)
    kicker = doc.add_paragraph()
    kicker.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = kicker.add_run("嵌入式项目实战教程")
    set_run_font(r, size=11, bold=True, color=BLUE)
    kicker.paragraph_format.space_after = Pt(16)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_after = Pt(10)
    r = title.add_run("STM32 双板 CAN 电机测速\n与 LVGL 显示问题排查")
    set_run_font(r, size=27, bold=True, color=INK)

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.paragraph_format.space_after = Pt(28)
    r = subtitle.add_run("从“为什么不工作”到“如何一步步验证”的初学者指南")
    set_run_font(r, size=14, color=DARK_BLUE)

    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = meta.add_run("适用工程：STM32F407VET6 发送端 + STM32F103ZET6 接收显示端")
    set_run_font(r, size=10.5, bold=True, color=MUTED)
    meta.paragraph_format.space_after = Pt(7)
    meta2 = doc.add_paragraph()
    meta2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = meta2.add_run("CAN 100 kbit/s · 编码器测速 · FreeRTOS · FSMC · ILI9486 · LVGL 9.5")
    set_run_font(r, size=10, color=MUTED)
    meta2.paragraph_format.space_after = Pt(42)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.left_indent = Inches(0.55)
    p.paragraph_format.right_indent = Inches(0.55)
    r = p.add_run("学习目标：能独立判断问题属于硬件、电气参数、外设配置、通信协议、实时任务还是显示驱动，并用可观察证据逐层缩小范围。")
    set_run_font(r, size=11, color=INK)
    set_paragraph_shading(p, NOTE_FILL, border=BLUE)

    add_page_break(doc)

    add_heading(doc, 1, "1. 先看懂整个系统")
    add_body(doc, "这个项目由两块单片机分工完成。最重要的调试思想是：不要一上来同时怀疑所有模块，而是沿着数据流逐段验证。只要能够确认数据在哪一段还正确，就能把故障范围缩小到下一段。")

    add_table(doc,
              ["阶段", "负责模块", "你要观察什么"],
              [
                  ("1. 电机执行", "F407：TIM1 PWM", "电机能否按设定方向和占空比运行"),
                  ("2. 速度采集", "F407：TIM2 编码器", "50 ms内的脉冲增量和计算出的 RPM"),
                  ("3. 数据发送", "F407：CAN1", "0x201 报文是否每 50 ms发送"),
                  ("4. 数据接收", "F103：CAN1 FIFO0 中断", "ID、DLC、4 字节数据是否正确"),
                  ("5. 状态判断", "F103：500 ms超时", "在线、掉线、恢复是否符合预期"),
                  ("6. 图形显示", "F103：FSMC + LVGL", "方向、颜色、刻度、指针是否正确"),
              ], [1.05, 2.05, 3.40])

    add_heading(doc, 2, "1.1 本工程中两块 MCU 的职责")
    add_body(doc, "STM32F407VET6 运行在 168 MHz，使用 FreeRTOS 管理任务。电机任务通过 TIM1 的两个 PWM 通道驱动直流减速电机，TIM2 使用编码器接口读取 A/B 相脉冲，然后把计算出的转速封装成 CAN 报文。")
    add_body(doc, "STM32F103ZET6 运行在 72 MHz，通过 CAN1 接收指定 ID 的报文。接收回调只做读取与解析，不直接操作 LVGL；主循环每 50 ms取得一份一致的数据快照，再更新仪表盘。")

    add_heading(doc, 2, "1.2 初学者必须建立的排查顺序")
    add_numbered_list(doc, (
        "先验证供电、共地、CANH/CANL 和终端电阻，硬件不通时改代码没有意义。",
        "再验证两端波特率和位时序，确认双方对“一个比特多长”的理解一致。",
        "然后用串口日志观察 F407 的编码器值、RPM 和 CAN 发送返回值。",
        "接着在 F103 接收中断中观察 ID、DLC 和数据字节。",
        "最后才排查 LVGL 对象、颜色格式、横竖屏和刷新回调。",
    ))
    add_callout(doc, "核心原则", "一次只改变一个变量，并为每一步设置可观察结果。不要同时修改 CAN 参数、协议和显示代码，否则即使恢复正常，也不知道真正原因。")

    add_heading(doc, 1, "2. 问题一：双板 CAN 无法通信或偶发丢帧")

    add_heading(doc, 2, "2.1 先理解 CAN 为什么需要收发器和终端电阻")
    add_body(doc, "STM32 的 CAN 外设输出的是逻辑信号，不能直接把两块 MCU 的 TX/RX 引脚相连。每块板都需要 CAN 收发器，把逻辑电平转换成 CANH/CANL 差分信号。两端还必须共地，否则收发器的共模电压可能超出范围。")
    add_bullet(doc, "连接方式：板 A 的 CANH 接板 B 的 CANH，CANL 接 CANL，两板 GND 相连。")
    add_bullet(doc, "总线两端各接一个 120 Ω终端电阻。断电后测量 CANH 与 CANL，两个 120 Ω并联应约为 60 Ω。")
    add_bullet(doc, "如果测得约 120 Ω，通常表示只接了一个终端；如果接近 0 Ω，可能短路；阻值很大则可能没有终端或线路断开。")
    add_callout(doc, "安全提醒", "测量终端电阻必须在系统断电后进行。带电测电阻会受到电路影响，也可能损坏万用表或硬件。", kind="warn")

    add_heading(doc, 2, "2.2 两端波特率必须相同，但寄存器参数可以不同")
    add_body(doc, "CAN 波特率由 CAN 外设时钟、预分频和一个比特包含的时间片数量共同决定。公式是：")
    add_code(doc, "CAN 波特率 = CAN 时钟 / Prescaler / (1 + BS1 + BS2)\n其中 1 表示同步段 Sync_Seg。")
    add_body(doc, "F407 的 APB1/CAN 时钟是 42 MHz，参数为 Prescaler=21、BS1=15、BS2=4：")
    add_code(doc, "42 MHz / 21 / (1 + 15 + 4) = 100 000 bit/s")
    add_body(doc, "F103 的 CAN 时钟是 36 MHz，参数为 Prescaler=20、BS1=13、BS2=4：")
    add_code(doc, "36 MHz / 20 / (1 + 13 + 4) = 100 000 bit/s")
    add_callout(doc, "为什么参数不同也能通信？", "两块 MCU 的 CAN 时钟不同，所以预分频和时间段不必完全一致；只要最终波特率一致，采样点合理，就可以通信。本工程两端最终都是 100 kbit/s。")

    add_heading(doc, 2, "2.3 先把协议写成人能看懂的表")
    add_table(doc,
              ["字段", "值/位置", "含义"],
              [
                  ("帧类型", "标准数据帧", "IDE=STD，RTR=DATA"),
                  ("CAN ID", "0x201", "电机转速专用报文"),
                  ("DLC", "4", "有效载荷为 4 字节"),
                  ("Byte0", "RPM×10 低字节", "小端序"),
                  ("Byte1", "RPM×10 高字节", "与 Byte0 组合成 uint16_t"),
                  ("Byte2", "sequence", "每发送一帧自增，可辅助发现丢帧"),
                  ("Byte3 bit7", "valid", "1 表示数据有效"),
                  ("Byte3 bit0", "reverse", "1 表示反转"),
              ], [1.25, 2.0, 3.25])

    add_heading(doc, 2, "2.4 F407 发送端是怎样工作的")
    add_body(doc, "FreeRTOS 电机任务使用 vTaskDelayUntil 每 50 ms唤醒一次。与普通延时相比，绝对周期延时不会把每次执行代码所耗费的时间不断累加，因此发送间隔更稳定。")
    add_code(doc, "vTaskDelayUntil(&last_wake_tick, pdMS_TO_TICKS(50U));\nDianji_Update(50U);\nrpm = Dianji_GetRPM();\ncan_result = CAN_SendMotorSpeed(rpm);")
    add_body(doc, "发送函数先判断正反转，把转速绝对值乘以 10 后四舍五入到 uint16_t，再填入 4 字节报文。发送前检查是否存在空闲邮箱；没有邮箱时返回 HAL_BUSY，而不是在任务中无限等待。")
    add_code(doc, "data[0] = rpm_x10 & 0xFF;\ndata[1] = (rpm_x10 >> 8) & 0xFF;\ndata[2] = motor_speed_sequence++;\ndata[3] = 0x80 | (reverse ? 0x01 : 0x00);")

    add_heading(doc, 2, "2.5 F103 接收端为什么使用精确过滤")
    add_body(doc, "过滤器的作用是在硬件层丢弃不关心的报文，减少 CPU 中断次数。本工程把标准 ID 左移 5 位写入 32 位过滤寄存器，并用掩码只允许 0x201 进入 FIFO0。")
    add_code(doc, "filter.FilterIdHigh     = (uint16_t)(0x201U << 5);\nfilter.FilterMaskIdHigh   = 0xFFE0U;\nfilter.FilterFIFOAssignment = CAN_RX_FIFO0;\nfilter.FilterMode         = CAN_FILTERMODE_IDMASK;")
    add_body(doc, "即使硬件过滤已经生效，接收回调仍再次检查 IDE、RTR、StdId 和 DLC。这是防御式编程：过滤配置将来改变时，业务解析仍不会误把其他帧当成转速数据。")

    add_heading(doc, 2, "2.6 为什么要做 500 ms掉线判断")
    add_body(doc, "正常报文每 50 ms到达一次。若超过 500 ms没有新帧，相当于连续丢失约 10 个周期，应认为链路失效。接收中断记录 HAL_GetTick()，主循环比较当前时间和最后接收时间。使用无符号减法还能自然处理 tick 计数回绕。")
    add_code(doc, "valid = has_received && status_valid &&\n        ((HAL_GetTick() - last_receive_tick) <= 500U);")

    add_heading(doc, 2, "2.7 CAN 故障的逐步排查流程")
    add_numbered_list(doc, (
        "断电检查 CANH、CANL、GND 和终端电阻，CANH-CANL 应约为 60 Ω。",
        "仅启动 F407，串口打印编码器增量、RPM 和 CAN_SendMotorSpeed 的返回值。若持续 HAL_BUSY，检查总线是否没有 ACK。",
        "核算两端 CAN 外设时钟、Prescaler、BS1、BS2 和 SJW，确认最终均为 100 kbit/s。",
        "临时把 F103 过滤器放宽，确认能否收到任意报文；能收到后再恢复 0x201 精确过滤。",
        "在 F103 回调中记录 StdId、DLC、Byte0~Byte3；不要在高频中断中大量 printf，可把数据保存后由主循环打印。",
        "拔掉 CANH 或 CANL，确认 500 ms后出现 CAN LOST；恢复接线后应自动回到在线状态。",
    ))

    # The heading stays with the table and lets Word move both to the next
    # page naturally without creating a blank page.
    add_heading(doc, 3, "2.8 CAN 常见现象速查")
    add_table(doc,
              ["现象", "优先怀疑", "验证方法"],
              [
                  ("一直 HAL_BUSY", "没有空闲邮箱/总线无 ACK", "检查另一节点是否上电、波特率、收发器和终端"),
                  ("F407 发送 OK，F103 无中断", "过滤器、GPIO 复用、NVIC", "临时放宽过滤并检查 CAN RX 引脚映射"),
                  ("偶尔 CAN LOST", "接线干扰、周期阻塞、采样点", "看序号跳变和接收时间戳，缩短高优先级阻塞"),
                  ("数值很大或乱跳", "字节序/DLC/缩放错误", "手工用 Byte0、Byte1 还原 rpm_x10"),
                  ("方向相反", "reverse 位或编码器符号", "对照 Byte3 bit0 与实际旋转方向"),
              ], [1.45, 2.0, 3.05])

    add_callout(doc, "当前工程的可靠性边界", "F407 与 F103 的 AutoBusOff、AutoWakeUp 已开启，但 AutoRetransmission 当前关闭。若应用要求更强抗干扰能力，可评估开启自动重发；修改后要重新测试总线拥塞、错误恢复和实时性。", kind="warn")

    add_heading(doc, 1, "3. 问题二：编码器测速值跳动，仪表指针抖动")

    add_heading(doc, 2, "3.1 编码器到底测到的是什么")
    add_body(doc, "增量式编码器输出 A、B 两相信号。TIM2 的 Encoder Interface 会根据两相信号的先后关系判断方向，并对边沿计数。程序每 50 ms读取一次计数器，这个增量不是 RPM，而是这 50 ms内走过的脉冲数。")
    add_body(doc, "本工程参数为：编码器每圈 13 线、减速比 30、四倍频计数，因此输出轴每转一圈的计数 CPR 为：")
    add_code(doc, "CPR = 13 × 30 × 4 = 1560 count/revolution")
    add_body(doc, "如果 50 ms内读取到 delta 个计数，则：")
    add_code(doc, "RPM = delta × 60000 / (CPR × period_ms)\n    = delta × 60000 / (1560 × 50)")
    add_body(doc, "例如 50 ms内得到 260 个计数：RPM = 260×60000/(1560×50) = 200 RPM。这个手算例子非常适合验证程序公式。")

    add_heading(doc, 2, "3.2 为什么测速会抖动")
    add_bullet(doc, "采样窗口短：低速时每个周期只有少量脉冲，差 1 个脉冲就会造成明显比例误差。")
    add_bullet(doc, "电机机械振动、齿轮间隙和负载变化会造成真实速度波动。")
    add_bullet(doc, "编码器线缆干扰或输入悬空会产生额外边沿；TIM2 输入滤波设置不当也会影响计数。")
    add_bullet(doc, "任务周期不稳定会让同样的脉冲数对应不同时间，导致 RPM 计算偏差。")
    add_bullet(doc, "整数显示和指针直接跟随原始值，会把小波动放大成明显视觉抖动。")

    add_heading(doc, 2, "3.3 本工程采用的三个解决办法")
    add_heading(doc, 3, "办法 A：固定 50 ms采样周期")
    add_body(doc, "使用 vTaskDelayUntil 保持周期基准，不让任务执行耗时累积到下一次延时中。调试时可以翻转一个 GPIO，用示波器测量任务周期是否稳定。")

    add_heading(doc, 3, "办法 B：一阶低通滤波")
    add_body(doc, "程序没有直接把 raw_rpm 作为结果，而是让当前值每次只向新值移动 25%。公式为：")
    add_code(doc, "filtered = filtered + 0.25 × (raw - filtered)")
    add_body(doc, "α=0.25 是响应速度与平滑程度的折中。α 越小越平滑，但跟随变慢；α 越大响应更快，但抖动更明显。初学者调参时建议按 0.15、0.25、0.40 三档比较，不要连续随意改动。")

    add_heading(doc, 3, "办法 C：零速死区")
    add_body(doc, "电机停止后可能还会出现极小的正负数。本工程把 -0.15～0.15 RPM 直接归零，防止仪表盘在零点附近来回晃动。")
    add_code(doc, "if((rpm > -0.15f) && (rpm < 0.15f))\n{\n    rpm = 0.0f;\n}")

    add_heading(doc, 2, "3.4 编码器问题的排查流程")
    add_numbered_list(doc, (
        "先让电机低占空比空载运行，串口同时打印 delta_count 和 raw RPM。",
        "手动转动电机轴，确认正转计数为正、反转为负；若方向相反，交换 A/B 相或修改编码器符号。",
        "固定转速下观察 delta_count。如果出现远大于相邻值的尖峰，检查线缆、接地和 TIM 输入滤波。",
        "用手算公式验证一个采样周期，排除 CPR、减速比、四倍频和时间单位写错。",
        "确认原始值基本正确后再开启低通滤波；不要用滤波掩盖错误计数。",
        "最后观察 LCD 指针。如果数字稳定而指针抖，问题属于 LVGL 更新/动画，不再属于编码器。",
    ))

    add_table(doc,
              ["现象", "原因", "处理"],
              [
                  ("RPM 恰好差 2/4 倍", "四倍频或 CPR 定义不一致", "核对编码器模式和 DIANJI_ENCODER_MULTIPLIER"),
                  ("RPM 恰好差 30 倍", "把电机轴与减速箱输出轴混淆", "确认 13 线是电机轴参数，计算时包含 30:1 减速比"),
                  ("正转显示负数", "A/B 相方向或符号相反", "交换 A/B 或调整 DIANJI_ENCODER_SIGN"),
                  ("低速跳动明显", "窗口内脉冲太少", "适当延长采样周期或加强滤波，但接受响应变慢"),
                  ("停止后不归零", "噪声/机械惯性", "增加合理死区，先确认没有持续误计数"),
              ], [1.55, 2.15, 2.80])

    add_heading(doc, 1, "4. 问题三：ILI9486/LVGL 方向、颜色或刷新异常")

    add_heading(doc, 2, "4.1 先分清三层：总线、LCD 控制器、LVGL")
    add_body(doc, "显示问题经常难排查，是因为它同时包含三层。FSMC 负责把数据写到外部地址；ILI9486 负责解释命令和像素；LVGL 负责生成需要刷新的像素区域。必须先证明底层 LCD 能显示纯色，再接入 LVGL。")
    add_table(doc,
              ["层级", "职责", "典型故障"],
              [
                  ("FSMC", "16 位并行读写、地址映射、时序", "白屏、花屏、随机像素、写入不稳定"),
                  ("ILI9486", "复位、初始化、方向、窗口、像素格式", "方向错误、镜像、颜色交换、坐标错位"),
                  ("LVGL port", "缓冲、flush_cb、区域刷新、完成通知", "只刷一次、局部残影、卡死、越界"),
                  ("仪表盘业务", "刻度、文字、动画、在线状态", "指针不动、数值不更新、状态显示错误"),
              ], [1.20, 2.60, 2.70])

    add_heading(doc, 2, "4.2 为什么命令地址和数据地址不同")
    add_body(doc, "ILI9486 的 RS/DC 引脚用于区分“命令”和“数据”。本工程把 RS 接到 FSMC_A10。因为 FSMC 使用 16 位总线，CPU 地址需要再左移 1 位，所以数据地址偏移是 1<<(10+1)=0x800。")
    add_code(doc, "LCD_CMD_ADDR  = 0x6C000000\nLCD_DATA_ADDR = 0x6C000000 + 0x800\n              = 0x6C000800")
    add_callout(doc, "典型错误", "如果仍按 8 位总线计算成 0x400，命令和数据可能被 LCD 错误解释，常见表现是白屏、寄存器配置无效或画面混乱。")

    add_heading(doc, 2, "4.3 横竖屏和颜色为什么会错")
    add_body(doc, "ILI9486 的 MADCTL（0x36）控制行列交换、扫描方向和 RGB/BGR 顺序。本工程写入 0x28 得到 480×320横屏并选择 BGR。不同 LCD 模组的面板连接可能不同，因此不能只凭经验抄一个值，必须用四色角标验证左上、右上、左下、右下。")
    add_bullet(doc, "画面旋转 90°：通常检查 MADCTL 的 MV 位和 LVGL 分辨率是否一致。")
    add_bullet(doc, "左右或上下镜像：检查 MX/MY 位。")
    add_bullet(doc, "红色变蓝色：检查 MADCTL 的 BGR 位以及 LV_COLOR_FORMAT_RGB565。")
    add_bullet(doc, "坐标越界或部分不显示：检查横屏后宽高是否为 480×320，而不是 320×480。")

    add_heading(doc, 2, "4.4 为什么使用 480×10 的分块缓冲")
    add_body(doc, "整屏 RGB565 缓冲需要 480×320×2=307200 字节，而 STM32F103ZET6 只有约 64 KB SRAM，无法放下。工程只保存 10 行：")
    add_code(doc, "480 × 10 × 2 = 9600 bytes")
    add_body(doc, "LVGL 逐块渲染，flush_cb 每次接收一个区域和对应像素指针，设置 LCD 窗口后逐像素写入，最后必须调用 lv_display_flush_ready() 告诉 LVGL 这块数据已经发送完成。")
    add_code(doc, "pixel_count = width * height;\nILI9486_SetWindow(x1, y1, x2, y2);\nwhile(pixel_count--) { LCD_DATA_REG = *pixels++; }\nlv_display_flush_ready(display);")
    add_callout(doc, "如果忘记 flush_ready", "LVGL 会认为上一轮刷新仍未结束，常见现象是首帧显示后不再更新，或者界面像“卡死”一样。", kind="warn")

    add_heading(doc, 2, "4.5 显示异常的正确排查顺序")
    add_numbered_list(doc, (
        "不运行 LVGL，先用 LCD 底层驱动依次全屏显示红、绿、蓝、白、黑。纯色不正确时只查 FSMC 和 ILI9486。",
        "显示四个角的不同颜色或短文字，确认 480×320方向、镜像和坐标范围。",
        "接入 LVGL 后先只显示深色背景和一个“LVGL OK”标签，不要立刻加入仪表盘。",
        "检查 flush_cb 的区域宽高、pixel_count 和 pixel_map 类型，RGB565 应按 uint16_t 读取。",
        "确认每次刷新结束都调用 lv_display_flush_ready。",
        "基础画面稳定后再创建刻度盘、数字、状态标签和动画；一次增加一个组件。",
    ))

    # Start the display symptom table on a clean page for stable pagination in
    # both Microsoft Word and LibreOffice.
    add_page_break(doc)
    add_table(doc,
              ["现象", "最可能位置", "首先检查"],
              [
                  ("完全白屏", "复位/背光/FSMC/初始化", "PG15 复位、PB0 背光、NE4、命令地址"),
                  ("颜色红蓝互换", "RGB/BGR", "MADCTL BGR 位和 RGB565 格式"),
                  ("画面旋转或镜像", "MADCTL/分辨率", "0x36 配置与 480×320是否匹配"),
                  ("只显示一部分", "窗口坐标/宽高", "x1、y1、x2、y2和像素数量"),
                  ("首帧后卡住", "LVGL flush 完成", "是否调用 lv_display_flush_ready"),
                  ("花屏或不稳定", "FSMC 时序/线路", "DataSetupTime、总线宽度、排线与供电"),
              ], [1.45, 2.0, 3.05])

    add_heading(doc, 1, "5. 并发数据为什么要做临界区保护")
    add_body(doc, "CAN 接收回调在中断上下文中修改 rpm、sequence、status 和 last_receive_tick，主循环同时读取这些变量。volatile 只能保证每次都从内存读取，不能保证多个字段在同一时刻保持一致。")
    add_body(doc, "例如主循环先读到新 RPM，随后发生中断，又读到下一帧的 sequence，就会得到一份“拼接数据”。工程在复制共享变量时短暂关闭中断，复制完成后立即恢复。")
    add_code(doc, "primask = __get_PRIMASK();\n__disable_irq();\n\nrpm_x10    = motor_rpm_x10;\nsequence    = motor_sequence;\nstatus      = motor_status;\nreceive_tick = motor_last_receive_tick;\n\nif(primask == 0U) { __enable_irq(); }")
    add_callout(doc, "为什么保存 PRIMASK？", "调用函数前中断可能本来就是关闭的。如果无条件 __enable_irq()，会错误改变上层状态。保存并恢复原状态更安全。")
    add_body(doc, "临界区必须尽量短：只复制几个变量，不在其中 printf、延时、写 LCD 或执行浮点复杂计算。这样可以减少中断响应延迟。")

    add_heading(doc, 1, "6. 一套可以反复使用的系统调试方法")
    add_heading(doc, 2, "6.1 用“输入—处理—输出”检查每个模块")
    add_table(doc,
              ["模块", "输入", "处理", "输出/证据"],
              [
                  ("编码器", "A/B 相边沿", "TIM2 正交计数", "delta_count 正负与大小"),
                  ("测速", "delta_count、50 ms", "CPR 换算 + 低通", "RPM 串口日志"),
                  ("CAN 发送", "RPM、方向", "0x201/4 字节封装", "HAL_OK/HAL_BUSY/错误码"),
                  ("CAN 接收", "FIFO0 报文", "过滤、校验、解析", "ID/DLC/数据/时间戳"),
                  ("在线判断", "last_tick", "500 ms比较", "WAIT/ONLINE/LOST"),
                  ("LVGL", "目标 RPM", "对象更新 + 120 ms动画", "数字和指针同步变化"),
              ], [1.20, 1.75, 2.10, 1.45])

    add_heading(doc, 2, "6.2 每次调试都记录四件事")
    add_bullet(doc, "现象：准确描述“什么时候、以什么频率、出现什么错误”，不要只写“不工作”。")
    add_bullet(doc, "假设：一次只提出一个最可能原因，例如“F103 过滤器没有放行 0x201”。")
    add_bullet(doc, "实验：设计最小验证，例如临时放宽过滤器，而不是重写整个 CAN 模块。")
    add_bullet(doc, "结论：记录实验结果以及下一步。失败实验同样有价值，因为它排除了一个方向。")

    add_heading(doc, 2, "6.3 推荐的串口日志")
    add_code(doc, "F407: ENC:260 RAW:201.4 FILT:199.8 CAN:OK SEQ:37\nF103: ID:201 DLC:4 RPM:199.8 SEQ:37 VALID:1 AGE:12ms\nUI  : ONLINE TARGET:200 DISPLAY:197")
    add_body(doc, "日志应能把同一帧从发送端追踪到接收端。调试完成后降低打印频率，避免 printf 阻塞改变任务周期；中断里不要大量打印。")

    add_heading(doc, 1, "7. 最终验收清单")
    add_heading(doc, 2, "7.1 F407 电机与测速端")
    for text in (
        "TIM1 两路 PWM 能控制电机停止、正转和反转，占空比限制在安全范围。",
        "TIM2 编码器正反方向正确，50 ms增量与实际转速数量级一致。",
        "RPM 手算结果与程序一致，低通滤波后稳定且响应速度可接受。",
        "电机任务周期约为 50 ms，长时间运行没有明显漂移。",
        "CAN 发送正常时返回 HAL_OK，异常时能够观察 HAL_BUSY 或错误码。",
    ):
        add_bullet(doc, text)

    add_heading(doc, 2, "7.2 CAN 链路")
    for text in (
        "两端均为 100 kbit/s，CANH/CANL 接线正确、共地，断电测得约 60 Ω。",
        "F103 只接收标准数据帧 0x201，DLC 至少为 4。",
        "Byte0/Byte1 还原的 RPM×10 与 F407 日志一致。",
        "sequence 连续递增；如有跳号，能够进一步分析是否丢帧。",
        "断线 500 ms后显示 LOST，恢复连接后自动 ONLINE。",
    ):
        add_bullet(doc, text)

    add_heading(doc, 2, "7.3 F103 显示端")
    for text in (
        "ILI9486 红、绿、蓝、白、黑纯色显示正确。",
        "480×320横屏无镜像，四角坐标正确，红蓝颜色不交换。",
        "LVGL 分块缓冲占用 9600 字节，刷新区域没有越界。",
        "数字转速与 CAN 数据一致，指针平滑且 0～400 RPM范围正确。",
        "连续运行至少 30 分钟，无花屏、HardFault、明显卡顿或通信假掉线。",
    ):
        add_bullet(doc, text)

    add_heading(doc, 1, "8. 面试时怎样讲这次问题解决过程")
    add_body(doc, "建议使用“问题—定位—措施—结果”四步法，不要只背技术名词。下面是一段可以直接练习的回答：")
    add_callout(doc, "示例回答", "双板联调时主要遇到 CAN 无法稳定接收、编码器速度跳动和 LCD 显示方向/颜色异常。首先我按物理层、位时序、协议和应用层分层排查，统一两端 100 kbit/s配置，检查收发器、共地及终端电阻，并通过 ID 0x201 过滤、序号和 500 ms超时机制验证链路。然后用固定 50 ms周期读取编码器，根据 CPR 计算 RPM，并加入一阶低通滤波和零速死区。最后先验证 LCD 纯色和四角坐标，再检查 FSMC 地址、MADCTL、RGB565 和 LVGL flush 流程。最终实现了从电机控制、测速、CAN 传输到仪表盘显示的稳定数据链路。")

    add_heading(doc, 1, "附录 A：工程文件与学习入口")
    add_table(doc,
              ["工程文件", "作用", "阅读重点"],
              [
                  ("LED1/Core/Src/dianji.c", "F407 电机驱动与测速", "PWM、编码器计数、RPM 和低通滤波"),
                  ("LED1/Core/Src/freertos.c", "F407 周期任务", "vTaskDelayUntil、50 ms采样和 CAN 发送"),
                  ("LED1/Core/Src/can.c", "F407 CAN 发送", "0x201 协议封装、邮箱检测"),
                  ("CAN_HAL/Core/Src/motor_can_rx.c", "F103 CAN 接收", "过滤器、FIFO0 中断、临界区、超时"),
                  ("CAN_HAL/Core/Src/car_tachometer.c", "LVGL 仪表盘", "刻度、数字、在线状态、动画"),
                  ("CAN_HAL/lvgl/porting/lv_port_lcd_stm32.c", "LCD/LVGL 端口", "FSMC 地址、ILI9486、RGB565、flush"),
              ], [2.65, 1.55, 2.30])

    add_callout(doc, "学习完成标准", "你不需要背下所有寄存器。只要能解释数据流、写出波特率与 RPM 公式、按固定顺序验证硬件和软件，并能通过日志证明问题在哪一层，就已经具备独立排查此类嵌入式问题的基本能力。")

    add_heading(doc, 1, "附录 B：初学者复盘问题")
    add_numbered_list(doc, (
        "为什么 F407 与 F103 的 Prescaler、BS1 不同，却都能得到 100 kbit/s？",
        "为什么两个 120 Ω终端电阻并联后测量值约为 60 Ω？",
        "为什么 volatile 不能替代临界区？",
        "为什么一阶低通滤波会让显示更稳定，但也会增加响应延迟？",
        "为什么 480×320整屏缓冲不适合 STM32F103，而 480×10 可以？",
        "如果数字 RPM 正确但指针不动，问题更可能在哪一层？",
    ))

    # Core document properties.
    props = doc.core_properties
    props.title = "STM32 双板 CAN 电机测速与 LVGL 显示问题排查入门教程"
    props.subject = "STM32F407 与 STM32F103 双板 CAN、编码器测速和 LVGL 显示调试"
    props.author = "Codex"
    props.keywords = "STM32, CAN, FreeRTOS, Encoder, FSMC, ILI9486, LVGL, Debugging"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    build()
