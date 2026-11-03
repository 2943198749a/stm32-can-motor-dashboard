from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.style import WD_STYLE_TYPE
from pathlib import Path


OUT = Path(r"D:\aiguigu\STM32F407\CAN_HAL\docs\STM32F407_CAN_LVGL_电机转速仪表盘实施手册.docx")

NAVY = "17365D"
BLUE = "2E74B5"
DARK_BLUE = "1F4D78"
LIGHT_BLUE = "E8EEF5"
LIGHT_GRAY = "F2F4F7"
MID_GRAY = "667085"
DARK = "17202A"
RED = "C62828"
GREEN = "18794E"
GOLD = "8A6500"
WHITE = "FFFFFF"
CODE_BG = "F6F8FA"
CODE_BORDER = "D0D7DE"


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


def set_table_geometry(table, widths_dxa, indent=120):
    total = sum(widths_dxa)
    table.autofit = False
    tbl_pr = table._tbl.tblPr
    tbl_w = tbl_pr.find(qn("w:tblW"))
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl_pr.append(tbl_w)
    tbl_w.set(qn("w:w"), str(total))
    tbl_w.set(qn("w:type"), "dxa")
    tbl_ind = tbl_pr.find(qn("w:tblInd"))
    if tbl_ind is None:
        tbl_ind = OxmlElement("w:tblInd")
        tbl_pr.append(tbl_ind)
    tbl_ind.set(qn("w:w"), str(indent))
    tbl_ind.set(qn("w:type"), "dxa")
    grid = table._tbl.tblGrid
    for child in list(grid):
        grid.remove(child)
    for w in widths_dxa:
        col = OxmlElement("w:gridCol")
        col.set(qn("w:w"), str(w))
        grid.append(col)
    for row in table.rows:
        for idx, cell in enumerate(row.cells):
            tc_pr = cell._tc.get_or_add_tcPr()
            tc_w = tc_pr.find(qn("w:tcW"))
            if tc_w is None:
                tc_w = OxmlElement("w:tcW")
                tc_pr.append(tc_w)
            tc_w.set(qn("w:w"), str(widths_dxa[idx]))
            tc_w.set(qn("w:type"), "dxa")
            set_cell_margins(cell)


def set_repeat_table_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def set_run_font(run, name="Microsoft YaHei", size=None, color=None, bold=None, italic=None):
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), name)
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), name)
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), name)
    if size is not None:
        run.font.size = Pt(size)
    if color is not None:
        run.font.color.rgb = RGBColor.from_string(color)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic


def add_field(paragraph, field_code):
    run = paragraph.add_run()
    fld_char = OxmlElement("w:fldChar")
    fld_char.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = field_code
    sep = OxmlElement("w:fldChar")
    sep.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = "1"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend([fld_char, instr, sep, text, end])


def add_title(doc, text, subtitle=None):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(88)
    p.paragraph_format.space_after = Pt(10)
    r = p.add_run(text)
    set_run_font(r, size=28, color=NAVY, bold=True)
    if subtitle:
        p2 = doc.add_paragraph()
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p2.paragraph_format.space_after = Pt(24)
        r2 = p2.add_run(subtitle)
        set_run_font(r2, size=14, color=DARK_BLUE)


def add_heading(doc, text, level=1):
    p = doc.add_paragraph(text, style=f"Heading {level}")
    p.paragraph_format.keep_with_next = True
    return p


def add_para(doc, text="", bold_lead=None, color=None, italic=False):
    p = doc.add_paragraph()
    if bold_lead and text.startswith(bold_lead):
        r1 = p.add_run(bold_lead)
        set_run_font(r1, bold=True, color=color or DARK)
        r2 = p.add_run(text[len(bold_lead):])
        set_run_font(r2, color=color or DARK, italic=italic)
    else:
        r = p.add_run(text)
        set_run_font(r, color=color or DARK, italic=italic)
    return p


def add_bullet(doc, text, level=0):
    style = "List Bullet" if level == 0 else "List Bullet 2"
    p = doc.add_paragraph(style=style)
    r = p.add_run(text)
    set_run_font(r, color=DARK)
    return p


def add_number(doc, text):
    p = doc.add_paragraph(style="List Number")
    r = p.add_run(text)
    set_run_font(r, color=DARK)
    return p


def add_code(doc, code, caption=None):
    if caption:
        pcap = doc.add_paragraph()
        pcap.paragraph_format.space_before = Pt(6)
        pcap.paragraph_format.space_after = Pt(3)
        r = pcap.add_run(caption)
        set_run_font(r, size=9.5, color=MID_GRAY, bold=True)
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    set_table_geometry(table, [9360], indent=120)
    cell = table.cell(0, 0)
    set_cell_shading(cell, CODE_BG)
    set_cell_margins(cell, top=100, start=140, bottom=100, end=140)
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.0
    r = p.add_run(code.strip("\n"))
    set_run_font(r, name="Consolas", size=8.3, color="1F2328")
    doc.add_paragraph().paragraph_format.space_after = Pt(1)
    return table


def add_note(doc, label, text, kind="info"):
    colors = {
        "info": (LIGHT_BLUE, DARK_BLUE),
        "warn": ("FFF4E5", GOLD),
        "danger": ("FDECEC", RED),
        "ok": ("EAF7F0", GREEN),
    }
    fill, ink = colors[kind]
    table = doc.add_table(rows=1, cols=1)
    set_table_geometry(table, [9360], indent=120)
    cell = table.cell(0, 0)
    set_cell_shading(cell, fill)
    set_cell_margins(cell, top=120, start=160, bottom=120, end=160)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    r1 = p.add_run(label + "  ")
    set_run_font(r1, size=10.5, color=ink, bold=True)
    r2 = p.add_run(text)
    set_run_font(r2, size=10.5, color=DARK)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)


def add_table(doc, headers, rows, widths):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    table.style = "Table Grid"
    hdr = table.rows[0]
    set_repeat_table_header(hdr)
    for i, text in enumerate(headers):
        cell = hdr.cells[i]
        set_cell_shading(cell, LIGHT_BLUE)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        p = cell.paragraphs[0]
        r = p.add_run(str(text))
        set_run_font(r, size=9.5, color=NAVY, bold=True)
    for row_data in rows:
        cells = table.add_row().cells
        for i, text in enumerate(row_data):
            cells[i].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            p = cells[i].paragraphs[0]
            r = p.add_run(str(text))
            set_run_font(r, size=9.3, color=DARK)
    set_table_geometry(table, widths, indent=120)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return table


doc = Document()
sec = doc.sections[0]
sec.page_width = Inches(8.5)
sec.page_height = Inches(11)
sec.top_margin = Inches(1)
sec.bottom_margin = Inches(1)
sec.left_margin = Inches(1)
sec.right_margin = Inches(1)
sec.header_distance = Inches(0.492)
sec.footer_distance = Inches(0.492)

# Compact reference guide token map.
styles = doc.styles
normal = styles["Normal"]
normal.font.name = "Microsoft YaHei"
normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
normal.font.size = Pt(10.5)
normal.paragraph_format.space_before = Pt(0)
normal.paragraph_format.space_after = Pt(6)
normal.paragraph_format.line_spacing = 1.18

for name, size, color, before, after in (
    ("Heading 1", 16, BLUE, 18, 10),
    ("Heading 2", 13, BLUE, 14, 7),
    ("Heading 3", 11.5, DARK_BLUE, 10, 5),
):
    st = styles[name]
    st.font.name = "Microsoft YaHei"
    st._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    st.font.size = Pt(size)
    st.font.color.rgb = RGBColor.from_string(color)
    st.font.bold = True
    st.paragraph_format.space_before = Pt(before)
    st.paragraph_format.space_after = Pt(after)
    st.paragraph_format.keep_with_next = True

for list_name in ("List Bullet", "List Bullet 2", "List Number"):
    st = styles[list_name]
    st.font.name = "Microsoft YaHei"
    st._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    st.font.size = Pt(10.5)
    st.paragraph_format.left_indent = Inches(0.375 if list_name != "List Bullet 2" else 0.625)
    st.paragraph_format.first_line_indent = Inches(-0.188)
    st.paragraph_format.space_after = Pt(4)
    st.paragraph_format.line_spacing = 1.18

# Running header/footer.
hp = sec.header.paragraphs[0]
hp.alignment = WD_ALIGN_PARAGRAPH.LEFT
hr = hp.add_run("STM32 电机转速 CAN + LVGL 实施手册")
set_run_font(hr, size=8.5, color=MID_GRAY)
fp = sec.footer.paragraphs[0]
fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
fr = fp.add_run("第 ")
set_run_font(fr, size=8.5, color=MID_GRAY)
add_field(fp, "PAGE")
fr2 = fp.add_run(" 页")
set_run_font(fr2, size=8.5, color=MID_GRAY)

# Cover.
add_title(doc, "STM32F407 CAN + LVGL\n电机转速仪表盘实施手册",
          "JGB37-520（13 线编码器、1:30）｜F407 发送端 + F103/ILI9486 显示端")
add_para(doc, "适用工程")
add_table(doc, ["角色", "工程路径", "核心职责"], [
    ["发送端", r"D:\aiguigu\STM32F407\LED1", "TIM2 编码器测速、TIM1 电机 PWM、CAN1 发送"],
    ["显示端", r"D:\aiguigu\STM32F407\CAN_HAL", "CAN1 中断接收、LVGL 9.5、ILI9486 FSMC 显示"],
], [1500, 4560, 3300])
add_note(doc, "最终参数", "编码器 13 线 × 减速比 30 × AB 四倍频 = 1560 counts/输出轴一圈；额定 320 RPM 时，每 50 ms 约产生 416 个计数。", "ok")

doc.add_page_break()

add_heading(doc, "1. 系统目标与数据链", 1)
add_para(doc, "系统由两个 MCU 和一条 CAN 总线组成。F407 负责采集编码器、计算减速箱输出轴 RPM 并周期发送；F103 只负责接收最新 RPM，并在 LVGL 汽车风格仪表盘上显示。")
add_code(doc, """JGB37-520 编码器 A/B
        ↓
STM32F407 TIM2 Encoder Mode
        ↓ 每 50 ms
计算输出轴 RPM（1560 counts/rev）
        ↓
CAN 标准帧 ID 0x201 / 100 kbit/s
        ↓
STM32F103 CAN FIFO0 中断
        ↓
主循环读取最新 RPM
        ↓
LVGL 指针 + 数字 RPM
        ↓
ILI9486 / FSMC / 480×320""", "系统数据流")

add_heading(doc, "2. 已确认的工程配置", 1)
add_table(doc, ["项目", "F407 发送端", "F103 显示端"], [
    ["MCU", "STM32F407VET6，168 MHz", "STM32F103ZET6，72 MHz"],
    ["操作系统", "FreeRTOS / CMSIS-RTOS2，1 ms tick", "裸机主循环"],
    ["编码器", "TIM2，PA15/CH1 + PB3/CH2", "不适用"],
    ["电机 PWM", "TIM1_CH1/CH2，PE9/PE11", "不适用"],
    ["CAN", "CAN1，PD0 RX / PD1 TX", "CAN1，PB8 RX / PB9 TX"],
    ["CAN 波特率", "当前 100 kbit/s", "当前 100 kbit/s"],
    ["显示", "无", "ILI9486，FSMC Bank4，480×320"],
], [1800, 3780, 3780])

add_heading(doc, "3. 编码器与转速计算", 1)
add_heading(doc, "3.1 每圈计数", 2)
add_code(doc, """编码器线数           = 13
减速比               = 30
AB 正交程序倍频       = 4

输出轴每圈计数 = 13 × 30 × 4 = 1560 counts/rev""")
add_heading(doc, "3.2 RPM 公式", 2)
add_code(doc, """RPM = delta_count × 60000
      / sample_period_ms
      / counts_per_output_rev

固定 50 ms、1560 counts/rev 时：
RPM = delta_count × 60000 / 50 / 1560
    = delta_count × 0.7692308""")
add_table(doc, ["输出轴转速", "每 50 ms 理论计数"], [
    ["0 RPM", "0"], ["50 RPM", "约 65"], ["100 RPM", "约 130"],
    ["150 RPM", "约 195"], ["200 RPM", "约 260"], ["250 RPM", "约 325"],
    ["300 RPM", "约 390"], ["320 RPM", "约 416"], ["400 RPM", "约 520"],
], [3600, 5760])
add_note(doc, "判断依据", "320 RPM 时若计数约 104，像是 1 倍频；约 208，像是 2 倍频；TIM2 TI12 正常四倍频应接近 416。", "info")

add_heading(doc, "4. F407 发送端修改", 1)
add_heading(doc, "4.1 修改 Core/Inc/dianji.h", 2)
add_code(doc, r'''#ifndef __DIANJI_H
#define __DIANJI_H

#include "main.h"

#define DIANJI_ENCODER_LINES       (13.0f)
#define DIANJI_GEAR_RATIO          (30.0f)
#define DIANJI_ENCODER_MULTIPLIER  (4.0f)

#define DIANJI_ENCODER_CPR         \
    (DIANJI_ENCODER_LINES *        \
     DIANJI_GEAR_RATIO *           \
     DIANJI_ENCODER_MULTIPLIER)

#define DIANJI_ENCODER_SIGN        (1)

void Dianji_Init(void);
void Dianji_SetDuty(int16_t duty);
void Dianji_Update(uint32_t period_ms);

int32_t Dianji_GetDeltaCount(void);
int32_t Dianji_GetTotalCount(void);
float Dianji_GetRPM(void);

#endif''')

add_heading(doc, "4.2 修改 Core/Src/dianji.c 的 Dianji_Update", 2)
add_code(doc, r'''void Dianji_Update(uint32_t period_ms)
{
    int32_t delta;
    float raw_rpm;

    if(period_ms == 0U)
    {
        return;
    }

    delta = (int32_t)__HAL_TIM_GET_COUNTER(&htim2);
    __HAL_TIM_SET_COUNTER(&htim2, 0U);

    delta *= DIANJI_ENCODER_SIGN;

    dianji_delta_count = delta;
    dianji_total_count += delta;

    raw_rpm = ((float)delta * 60000.0f) /
              (DIANJI_ENCODER_CPR * (float)period_ms);

    /* 一阶低通：兼顾响应速度与仪表盘稳定性。 */
    dianji_rpm += 0.25f * (raw_rpm - dianji_rpm);

    if((dianji_rpm > -0.15f) &&
       (dianji_rpm < 0.15f))
    {
        dianji_rpm = 0.0f;
    }
}''')

add_heading(doc, "4.3 在 Core/Inc/can.h 添加接口", 2)
add_code(doc, r'''/* USER CODE BEGIN Private defines */
#define MOTOR_SPEED_CAN_ID  0x201U
/* USER CODE END Private defines */

/* USER CODE BEGIN Prototypes */
HAL_StatusTypeDef CAN_MotorSpeedStart(void);
HAL_StatusTypeDef CAN_SendMotorSpeed(float rpm);
/* USER CODE END Prototypes */''')

add_heading(doc, "4.4 在 Core/Src/can.c 添加发送函数", 2)
add_code(doc, r'''/* USER CODE BEGIN 1 */

static uint8_t motor_speed_sequence = 0U;

HAL_StatusTypeDef CAN_MotorSpeedStart(void)
{
    motor_speed_sequence = 0U;
    return HAL_CAN_Start(&hcan1);
}

HAL_StatusTypeDef CAN_SendMotorSpeed(float rpm)
{
    CAN_TxHeaderTypeDef tx_header;
    uint32_t tx_mailbox;
    uint8_t data[4];
    uint16_t rpm_x10;
    uint8_t reverse;

    if(rpm < 0.0f)
    {
        reverse = 1U;
        rpm = -rpm;
    }
    else
    {
        reverse = 0U;
    }

    if(rpm > 6553.5f)
    {
        rpm = 6553.5f;
    }

    rpm_x10 = (uint16_t)(rpm * 10.0f + 0.5f);

    data[0] = (uint8_t)(rpm_x10 & 0xFFU);
    data[1] = (uint8_t)((rpm_x10 >> 8) & 0xFFU);
    data[2] = motor_speed_sequence++;
    data[3] = 0x80U;                 /* bit7：数据有效 */

    if(reverse != 0U)
    {
        data[3] |= 0x01U;            /* bit0：反转 */
    }

    tx_header.StdId = MOTOR_SPEED_CAN_ID;
    tx_header.ExtId = 0U;
    tx_header.IDE = CAN_ID_STD;
    tx_header.RTR = CAN_RTR_DATA;
    tx_header.DLC = 4U;
    tx_header.TransmitGlobalTime = DISABLE;

    if(HAL_CAN_GetTxMailboxesFreeLevel(&hcan1) == 0U)
    {
        return HAL_BUSY;
    }

    return HAL_CAN_AddTxMessage(&hcan1,
                                &tx_header,
                                data,
                                &tx_mailbox);
}

/* USER CODE END 1 */''')

add_heading(doc, "4.5 修改 Core/Src/freertos.c", 2)
add_para(doc, "在 USER CODE Includes 中加入：")
add_code(doc, '#include "can.h"')
add_para(doc, "用下面代码替换空的 StartTask04：")
add_code(doc, r'''void StartTask04(void *argument)
{
  /* USER CODE BEGIN StartTask04 */

  TickType_t last_wake_tick;
  float rpm;

  Dianji_Init();

  if(CAN_MotorSpeedStart() != HAL_OK)
  {
      Error_Handler();
  }

  last_wake_tick = xTaskGetTickCount();

  for(;;)
  {
      vTaskDelayUntil(&last_wake_tick,
                      pdMS_TO_TICKS(50U));

      Dianji_Update(50U);
      rpm = Dianji_GetRPM();

      /* 邮箱满时丢弃旧帧，不阻塞实时任务。 */
      (void)CAN_SendMotorSpeed(rpm);
  }

  /* USER CODE END StartTask04 */
}''')
add_note(doc, "安全行为", "Dianji_Init() 最后调用 Dianji_SetDuty(0)，系统启动不会自动让电机转动。确认驱动桥和电源正确后，再从较小占空比开始测试。", "warn")

add_heading(doc, "5. CAN 协议与时序", 1)
add_heading(doc, "5.1 报文定义", 2)
add_table(doc, ["字段", "值/含义"], [
    ["标准 ID", "0x201"], ["DLC", "4"],
    ["Byte 0", "RPM × 10 低字节"], ["Byte 1", "RPM × 10 高字节"],
    ["Byte 2", "循环序号"], ["Byte 3 bit7", "1 = 数据有效"],
    ["Byte 3 bit0", "1 = 反转，0 = 正转"], ["发送周期", "50 ms（20 Hz）"],
], [2600, 6760])
add_para(doc, "320.0 RPM 的编码示例：")
add_code(doc, """rpm_x10 = 3200 = 0x0C80
CAN ID  = 0x201
DLC     = 4
data[0] = 0x80
data[1] = 0x0C
data[2] = sequence
data[3] = 0x80（正转且有效）""")

add_heading(doc, "5.2 推荐 CAN 位时序", 2)
add_table(doc, ["端点", "CAN 时钟", "Prescaler", "BS1", "BS2", "SJW", "波特率/采样点"], [
    ["F407", "42 MHz", "21", "15 TQ", "4 TQ", "1 TQ", "100 kbit/s，80%"],
    ["F103", "36 MHz", "20", "13 TQ", "4 TQ", "1 TQ", "100 kbit/s，77.8%"],
], [1150, 1250, 1150, 1150, 1150, 1050, 2460])
add_note(doc, "当前状态", "两个工程当前都是 100 kbit/s，因此基本波特率匹配；但现有 BS1=3、BS2=6 的采样点约 40%，建议在 CubeMX 中按表调整。", "warn")

add_heading(doc, "6. F103 接收端模块", 1)
add_heading(doc, "6.1 新建 Core/Inc/motor_can_rx.h", 2)
add_code(doc, r'''#ifndef MOTOR_CAN_RX_H
#define MOTOR_CAN_RX_H

#include "main.h"
#include <stdbool.h>
#include <stdint.h>

#define MOTOR_CAN_ID          0x201U
#define MOTOR_CAN_TIMEOUT_MS  500U

typedef struct
{
    float rpm;
    bool reverse;
    bool valid;
    uint8_t sequence;
    uint32_t last_receive_tick;
} MotorCanData_t;

void MotorCanRx_Init(void);
MotorCanData_t MotorCanRx_GetData(void);

#endif''')

add_heading(doc, "6.2 新建 Core/Src/motor_can_rx.c", 2)
add_code(doc, r'''#include "motor_can_rx.h"
#include "can.h"

static volatile uint16_t motor_rpm_x10;
static volatile uint8_t motor_sequence;
static volatile uint8_t motor_status;
static volatile uint32_t motor_last_receive_tick;
static volatile uint8_t motor_has_received;

void MotorCanRx_Init(void)
{
    CAN_FilterTypeDef filter = {0};

    filter.FilterIdHigh = (uint16_t)(MOTOR_CAN_ID << 5);
    filter.FilterIdLow = 0x0000U;
    filter.FilterMaskIdHigh = 0xFFE0U;
    filter.FilterMaskIdLow = 0x0006U;
    filter.FilterFIFOAssignment = CAN_RX_FIFO0;
    filter.FilterBank = 0U;
    filter.FilterMode = CAN_FILTERMODE_IDMASK;
    filter.FilterScale = CAN_FILTERSCALE_32BIT;
    filter.FilterActivation = ENABLE;
    filter.SlaveStartFilterBank = 14U;

    if(HAL_CAN_ConfigFilter(&hcan, &filter) != HAL_OK)
        Error_Handler();

    if(HAL_CAN_Start(&hcan) != HAL_OK)
        Error_Handler();

    if(HAL_CAN_ActivateNotification(
           &hcan, CAN_IT_RX_FIFO0_MSG_PENDING) != HAL_OK)
        Error_Handler();
}

void HAL_CAN_RxFifo0MsgPendingCallback(CAN_HandleTypeDef *can_handle)
{
    CAN_RxHeaderTypeDef header;
    uint8_t data[8];

    if(can_handle->Instance != CAN1)
        return;

    while(HAL_CAN_GetRxFifoFillLevel(
              can_handle, CAN_RX_FIFO0) != 0U)
    {
        if(HAL_CAN_GetRxMessage(can_handle,
                               CAN_RX_FIFO0,
                               &header,
                               data) != HAL_OK)
            break;

        if((header.IDE == CAN_ID_STD) &&
           (header.RTR == CAN_RTR_DATA) &&
           (header.StdId == MOTOR_CAN_ID) &&
           (header.DLC >= 4U))
        {
            motor_rpm_x10 =
                (uint16_t)data[0] |
                ((uint16_t)data[1] << 8);
            motor_sequence = data[2];
            motor_status = data[3];
            motor_last_receive_tick = HAL_GetTick();
            motor_has_received = 1U;
        }
    }
}

MotorCanData_t MotorCanRx_GetData(void)
{
    MotorCanData_t result;
    uint16_t rpm_x10;
    uint8_t sequence;
    uint8_t status;
    uint8_t has_received;
    uint32_t receive_tick;
    uint32_t primask;

    primask = __get_PRIMASK();
    __disable_irq();

    rpm_x10 = motor_rpm_x10;
    sequence = motor_sequence;
    status = motor_status;
    has_received = motor_has_received;
    receive_tick = motor_last_receive_tick;

    if(primask == 0U)
        __enable_irq();

    result.rpm = (float)rpm_x10 / 10.0f;
    result.sequence = sequence;
    result.reverse = ((status & 0x01U) != 0U);
    result.last_receive_tick = receive_tick;
    result.valid =
        (has_received != 0U) &&
        ((status & 0x80U) != 0U) &&
        ((HAL_GetTick() - receive_tick) <= MOTOR_CAN_TIMEOUT_MS);

    return result;
}''')
add_note(doc, "中断边界", "HAL_CAN_RxFifo0MsgPendingCallback() 只保存数据，绝对不要在 CAN ISR 内调用 lv_label_set_text、CarTachometer_SetRpm 或其他 LVGL API。", "danger")

add_heading(doc, "6.3 开启 F103 CAN FIFO0 中断", 2)
add_number(doc, "在 CubeMX 的 CAN → NVIC Settings 中勾选 USB low priority or CAN RX0 interrupt。")
add_number(doc, "重新生成后检查 stm32f1xx_it.c 是否包含 can.h。")
add_number(doc, "确认中断函数调用 HAL_CAN_IRQHandler(&hcan)。")
add_code(doc, r'''void USB_LP_CAN1_RX0_IRQHandler(void)
{
    HAL_CAN_IRQHandler(&hcan);
}''')

add_heading(doc, "7. LVGL 汽车风格转速表", 1)
add_para(doc, "仪表盘量程采用 0～400 RPM，320～400 RPM 为红区。显示端只接收已经换算完成的 RPM，不再关心编码器线数与减速比。")
add_table(doc, ["视觉元素", "配置"], [
    ["量程", "0～400 RPM"], ["主刻度", "每 50 RPM"], ["小刻度", "每 10 RPM"],
    ["红区", "320～400 RPM"], ["背景", "深黑"], ["普通刻度", "白/灰"],
    ["指针", "红色，120 ms ease-out 动画"], ["断线提示", "超过 500 ms 无帧显示 CAN LOST，指针回零"],
], [2600, 6760])
add_para(doc, "lv_conf.h 至少启用：")
add_code(doc, r'''#define LV_COLOR_DEPTH          16
#define LV_USE_LABEL            1
#define LV_USE_LINE             1
#define LV_USE_SCALE            1
#define LV_FONT_MONTSERRAT_20   1
#define LV_FONT_MONTSERRAT_40   1''')
add_heading(doc, "7.1 仪表盘头文件 car_tachometer.h", 2)
add_code(doc, r'''#ifndef CAR_TACHOMETER_H
#define CAR_TACHOMETER_H

#include "lvgl.h"
#include <stdbool.h>
#include <stdint.h>

void CarTachometer_Create(lv_obj_t *parent);
void CarTachometer_SetRpm(uint16_t rpm);
void CarTachometer_SetOnline(bool online);

#endif''')

add_heading(doc, "7.2 仪表盘核心实现", 2)
add_code(doc, r'''#include "car_tachometer.h"

#define TACH_MIN_RPM       0
#define TACH_MAX_RPM       400
#define TACH_RED_RPM       320
#define TACH_ANGLE_RANGE   270
#define TACH_ROTATION      135

static lv_obj_t *scale;
static lv_obj_t *needle;
static lv_obj_t *rpm_label;
static lv_obj_t *status_label;
static int32_t displayed_rpm;
static int32_t target_rpm;
static bool online_state;

static void rpm_anim_exec(void *var, int32_t value)
{
    LV_UNUSED(var);
    displayed_rpm = value;
    lv_scale_set_line_needle_value(scale, needle, 108, value);
    lv_label_set_text_fmt(rpm_label, "%ld", (long)value);
}

void CarTachometer_Create(lv_obj_t *parent)
{
    lv_obj_t *root;
    lv_obj_t *unit;

    root = lv_obj_create(parent);
    lv_obj_remove_style_all(root);
    lv_obj_set_size(root, LV_PCT(100), LV_PCT(100));
    lv_obj_set_style_bg_color(root,
                              lv_color_hex(0x05070A), 0);
    lv_obj_set_style_bg_opa(root, LV_OPA_COVER, 0);

    scale = lv_scale_create(root);
    lv_scale_set_mode(scale, LV_SCALE_MODE_ROUND_INNER);
    lv_obj_set_size(scale, 300, 300);
    lv_obj_align(scale, LV_ALIGN_CENTER, 0, 10);
    lv_scale_set_range(scale, TACH_MIN_RPM, TACH_MAX_RPM);
    lv_scale_set_angle_range(scale, TACH_ANGLE_RANGE);
    lv_scale_set_rotation(scale, TACH_ROTATION);
    lv_scale_set_total_tick_count(scale, 41);
    lv_scale_set_major_tick_every(scale, 5);

    lv_obj_set_style_length(scale, 8, LV_PART_ITEMS);
    lv_obj_set_style_line_width(scale, 2, LV_PART_ITEMS);
    lv_obj_set_style_line_color(scale,
                                lv_color_hex(0x8A949F),
                                LV_PART_ITEMS);

    lv_obj_set_style_length(scale, 17, LV_PART_INDICATOR);
    lv_obj_set_style_line_width(scale, 4, LV_PART_INDICATOR);
    lv_obj_set_style_line_color(scale,
                                lv_color_hex(0xF5F7FA),
                                LV_PART_INDICATOR);
    lv_obj_set_style_text_color(scale,
                                lv_color_hex(0xF5F7FA),
                                LV_PART_INDICATOR);
    lv_obj_set_style_text_font(scale,
                               &lv_font_montserrat_20,
                               LV_PART_INDICATOR);

    needle = lv_line_create(scale);
    lv_obj_set_style_line_width(needle, 5, 0);
    lv_obj_set_style_line_color(needle,
                                lv_color_hex(0xFF2D2D), 0);
    lv_obj_set_style_line_rounded(needle, true, 0);
    lv_scale_set_line_needle_value(scale, needle, 108, 0);

    rpm_label = lv_label_create(root);
    lv_label_set_text(rpm_label, "0");
    lv_obj_set_style_text_color(rpm_label,
                                lv_color_hex(0xFFFFFF), 0);
    lv_obj_set_style_text_font(rpm_label,
                               &lv_font_montserrat_40, 0);
    lv_obj_align(rpm_label, LV_ALIGN_CENTER, 0, 48);

    unit = lv_label_create(root);
    lv_label_set_text(unit, "RPM");
    lv_obj_set_style_text_color(unit,
                                lv_color_hex(0x8A949F), 0);
    lv_obj_align_to(unit, rpm_label,
                    LV_ALIGN_OUT_BOTTOM_MID, 0, 0);

    status_label = lv_label_create(root);
    lv_label_set_text(status_label, "CAN WAIT");
    lv_obj_align(status_label,
                 LV_ALIGN_BOTTOM_RIGHT, -10, -8);

    displayed_rpm = 0;
    target_rpm = 0;
    online_state = false;
}

void CarTachometer_SetRpm(uint16_t rpm)
{
    lv_anim_t anim;

    if(rpm > TACH_MAX_RPM)
        rpm = TACH_MAX_RPM;

    if((int32_t)rpm == target_rpm)
        return;

    target_rpm = rpm;
    lv_anim_delete(NULL, rpm_anim_exec);
    lv_anim_init(&anim);
    lv_anim_set_var(&anim, NULL);
    lv_anim_set_exec_cb(&anim, rpm_anim_exec);
    lv_anim_set_values(&anim, displayed_rpm, target_rpm);
    lv_anim_set_duration(&anim, 120);
    lv_anim_set_path_cb(&anim, lv_anim_path_ease_out);
    lv_anim_start(&anim);
}

void CarTachometer_SetOnline(bool online)
{
    if(online_state == online)
        return;

    online_state = online;

    if(online)
    {
        lv_label_set_text(status_label, "CAN ONLINE");
        lv_obj_set_style_text_color(status_label,
                                    lv_color_hex(0x36D17C), 0);
    }
    else
    {
        lv_label_set_text(status_label, "CAN LOST");
        lv_obj_set_style_text_color(status_label,
                                    lv_color_hex(0xFF3B30), 0);
        CarTachometer_SetRpm(0U);
    }
}''')
add_note(doc, "红区实现", "可在基本仪表盘成功显示后，再用 lv_scale_add_section() 给 320～400 RPM 的主弧、刻度和标签统一应用红色样式。先验证数据链和基本指针，能减少同时排查的问题数量。", "info")

add_heading(doc, "8. F103 main.c 接入", 1)
add_para(doc, "Includes 用户区加入：")
add_code(doc, r'''#include "lvgl.h"
#include "lv_port_lcd_stm32.h"
#include "car_tachometer.h"
#include "motor_can_rx.h"''')
add_para(doc, "外设初始化后、进入主循环前：")
add_code(doc, r'''lv_init();
lv_tick_set_cb(HAL_GetTick);
lv_port_disp_init();

CarTachometer_Create(lv_screen_active());
MotorCanRx_Init();''')
add_para(doc, "主循环：")
add_code(doc, r'''static uint32_t dashboard_tick;

while(1)
{
    MotorCanData_t data;

    if((HAL_GetTick() - dashboard_tick) >= 50U)
    {
        dashboard_tick = HAL_GetTick();
        data = MotorCanRx_GetData();

        if(data.valid)
        {
            CarTachometer_SetOnline(true);
            CarTachometer_SetRpm(
                (uint16_t)(data.rpm + 0.5f));
        }
        else
        {
            CarTachometer_SetOnline(false);
        }
    }

    lv_timer_handler();
    HAL_Delay(5);
}''')
add_note(doc, "删除旧测试", "正式接收时不要再运行原 main.c 中的 CAN_SendMsg()/CAN_ReceiveMsg() 三帧测试，也不要在 MotorCanRx_Init() 之外重复 HAL_CAN_Start(&hcan)。", "warn")

add_heading(doc, "9. 电气连接", 1)
add_heading(doc, "9.1 编码器", 2)
add_table(doc, ["JGB37-520 线", "F407 连接"], [
    ["电机 M+ / M-", "连接电机驱动桥输出，不直接连接 MCU"],
    ["编码器 VCC", "按编码器额定电压供电"],
    ["编码器 GND", "与 F407、电机驱动逻辑地共地"],
    ["编码器 A", "PA15 / TIM2_CH1"],
    ["编码器 B", "PB3 / TIM2_CH2"],
], [3200, 6160])
add_heading(doc, "9.2 CAN 总线", 2)
add_code(doc, """F407 PD1/CAN1_TX → CAN 收发器 TXD
F407 PD0/CAN1_RX ← CAN 收发器 RXD

F103 PB9/CAN1_TX → CAN 收发器 TXD
F103 PB8/CAN1_RX ← CAN 收发器 RXD

两端 CANH 相连
两端 CANL 相连
两块 MCU 必须共地
总线物理两端各 120 Ω；断电测 CANH-CANL 约 60 Ω""")
add_note(doc, "禁止直连", "STM32 CAN_TX/CAN_RX 是控制器逻辑信号，不能直接当作 CANH/CANL。两端都需要 SN65HVD230、TJA1050 等 CAN 收发器。3.3 V MCU 优先选择 3.3 V 收发器。", "danger")

add_heading(doc, "10. 编码器标定", 1)
add_number(doc, "停止电机，调用 __HAL_TIM_SET_COUNTER(&htim2, 0U)。")
add_number(doc, "在减速箱输出轴做标记，让输出轴准确旋转一整圈。")
add_number(doc, "读取 TIM2 计数的绝对值，连续测三次。")
add_number(doc, "正常 TI12 四倍频应接近 1560；若稳定为其他值，用实测值修正 DIANJI_ENCODER_CPR。")
add_code(doc, r'''int32_t one_rev_count;

__HAL_TIM_SET_COUNTER(&htim2, 0U);
/* 此处手动让输出轴准确转一圈 */
one_rev_count = (int32_t)__HAL_TIM_GET_COUNTER(&htim2);

if(one_rev_count < 0)
    one_rev_count = -one_rev_count;

printf("one_rev_count=%ld\r\n", (long)one_rev_count);''')

add_heading(doc, "11. 分阶段验证清单", 1)
for item in [
    "F407 仅启动 TIM2 编码器，手动转动输出轴，确认计数方向和一圈约 1560。",
    "启动电机低占空比，确认每 50 ms 的 delta 与实际转速同向变化。",
    "F407 串口打印 count 和 rpm_x10；320 RPM 时 count 应约 416。",
    "连接 CAN 分析仪，确认 ID 0x201、DLC 4、周期约 50 ms。",
    "F103 暂不更新 LVGL，只通过串口打印接收的 rpm_x10。",
    "确认 CAN 数据稳定后，再调用 CarTachometer_SetRpm()。",
    "最后测试拔掉 CAN：500 ms 后应显示 CAN LOST，指针平滑回零。",
]:
    add_bullet(doc, item)

add_heading(doc, "12. 故障排查", 1)
add_table(doc, ["现象", "优先检查"], [
    ["F407 RPM 始终为 0", "Dianji_Init 是否调用；A/B 是否有波形；PA15/PB3 是否接反或悬空"],
    ["停止时 RPM 乱跳", "编码器地线、上拉、TIM2 输入滤波、电机噪声、编码器线走线"],
    ["320 RPM 显示约 1280", "CPR 小了约 4 倍；检查是否把 13 当成四倍频后的计数"],
    ["CAN 没有帧", "HAL_CAN_Start、收发器、共地、CANH/CANL、120 Ω、波特率"],
    ["F407 CAN 邮箱总是满", "总线没有 ACK；接收端未上电、位时序不匹配或收发器故障"],
    ["F103 能收但 LVGL 不动", "主循环是否持续 lv_timer_handler；不要在 CAN ISR 内更新 LVGL"],
    ["LVGL 指针抖动", "保留 0.25 一阶滤波和 120 ms 指针动画；检查原始 delta 是否稳定"],
    ["红蓝颜色相反", "ILI9486 MADCTL 的 BGR 位，而不是编码器/CAN 问题"],
], [3000, 6360])

add_heading(doc, "13. 最终验收标准", 1)
for item in [
    "电机停止 1 秒后显示 0 RPM。",
    "低速到高速变化时，数字和指针连续、无明显反向跳动。",
    "额定电压空载时显示值接近电机真实转速，且原始每 50 ms 计数约 416。",
    "CAN 报文保持 20 Hz，ID/DLC/字节序与文档一致。",
    "正反转均显示正的速度绝对值，方向状态位正确。",
    "拔掉 CAN 后 500 ms 内进入 CAN LOST，重新连接后自动恢复。",
    "电机工作时无明显 CAN 丢帧、F407 任务阻塞或 F103 HardFault。",
]:
    add_bullet(doc, item)

add_note(doc, "实施建议", "先把基本转速数据链跑通，再添加红区、渐变、阴影等视觉装饰。调试时一次只验证一个边界：编码器 → RPM → CAN → F103 → LVGL。", "ok")

OUT.parent.mkdir(parents=True, exist_ok=True)
doc.save(OUT)
print(OUT)
