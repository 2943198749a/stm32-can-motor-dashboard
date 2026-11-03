#include "dashboard.h"

/* 仪表盘量程使用 RPM×10，既能保留 0.1 RPM 精度，又避免浮点运算。 */
#define DASHBOARD_RPM_MAX_X10       4000U
/* 320.0 RPM 以上进入红色警示区。 */
#define DASHBOARD_RED_RPM_X10       3200U
/* LVGL 圆弧控件本身使用整数 RPM 作为取值范围。 */
#define DASHBOARD_ARC_MAX_RPM       400

/* 下面三个对象只允许在 LVGL 任务中访问，避免 LVGL 跨任务并发。 */
static lv_obj_t *dashboard_arc;
static lv_obj_t *dashboard_rpm_label;
static lv_obj_t *dashboard_status_label;

/**
 * @brief 在表盘指定位置创建一个静态刻度数字。
 * @param text  刻度文本，例如“100”。
 * @param x     标签左上角的横坐标。
 * @param y     标签左上角的纵坐标。
 * @param color 24 位 RGB 颜色，例如 0xB8C2CC。
 * @note 该函数只在 Dashboard_Init() 初始化阶段调用。
 */
static void Dashboard_CreateMark(const char *text,
                                 lv_coord_t x,
                                 lv_coord_t y,
                                 uint32_t color)
{
    lv_obj_t *label;

    label = lv_label_create(lv_screen_active());
    lv_label_set_text(label, text);
    lv_obj_set_style_text_color(
        label,
        lv_color_hex(color),
        LV_PART_MAIN);
    lv_obj_set_style_text_font(
        label,
        &lv_font_montserrat_14,
        LV_PART_MAIN);
    lv_obj_set_pos(label, x, y);
}

void Dashboard_Init(void)
{
    lv_obj_t *screen;
    lv_obj_t *title_label;
    lv_obj_t *unit_label;

    /* 取得 LVGL 当前活动屏幕，后续所有对象都挂在这个根对象下。 */
    screen = lv_screen_active();

    /* 设置深色不透明背景，模拟汽车仪表盘。 */
    lv_obj_set_style_bg_color(
        screen,
        lv_color_hex(0x05080CU),
        LV_PART_MAIN);
    lv_obj_set_style_bg_opa(
        screen,
        LV_OPA_COVER,
        LV_PART_MAIN);

    /* 顶部标题。 */
    title_label = lv_label_create(screen);
    lv_label_set_text(title_label, "MOTOR TACHOMETER");
    lv_obj_set_style_text_color(
        title_label,
        lv_color_hex(0x73879AU),
        LV_PART_MAIN);
    lv_obj_align(title_label, LV_ALIGN_TOP_MID, 0, 13);

    /*
     * 创建唯一的动态圆弧对象：
     * LV_PART_MAIN      表示灰色底弧；
     * LV_PART_INDICATOR 表示随转速变化的彩色指示弧。
     * 使用一个对象同时完成两层显示，可减少 LVGL 对象和绘制开销。
     */
    dashboard_arc = lv_arc_create(screen);
    lv_obj_set_size(dashboard_arc, 272, 272);
    lv_obj_align(dashboard_arc, LV_ALIGN_CENTER, 0, 8);
    /* 从 135° 开始绘制 270°，底部留出开口，形成汽车仪表效果。 */
    lv_arc_set_rotation(dashboard_arc, 135);
    lv_arc_set_bg_angles(dashboard_arc, 0, 270);
    lv_arc_set_range(dashboard_arc, 0, DASHBOARD_ARC_MAX_RPM);
    lv_arc_set_value(dashboard_arc, 0);

    lv_obj_set_style_arc_color(
        dashboard_arc,
        lv_color_hex(0x26323DU),
        LV_PART_MAIN);
    lv_obj_set_style_arc_width(
        dashboard_arc,
        18,
        LV_PART_MAIN);
    lv_obj_set_style_arc_color(
        dashboard_arc,
        lv_color_hex(0x00D7FFU),
        LV_PART_INDICATOR);
    lv_obj_set_style_arc_width(
        dashboard_arc,
        14,
        LV_PART_INDICATOR);
    /* 隐藏 Arc 默认旋钮，并禁止触摸拖动。 */
    lv_obj_set_style_opa(
        dashboard_arc,
        LV_OPA_TRANSP,
        LV_PART_KNOB);
    lv_obj_remove_flag(
        dashboard_arc,
        LV_OBJ_FLAG_CLICKABLE);

    /* 中央实时转速数字，显示一位小数。 */
    dashboard_rpm_label = lv_label_create(screen);
    lv_label_set_text(dashboard_rpm_label, "0.0");
    lv_obj_set_style_text_color(
        dashboard_rpm_label,
        lv_color_hex(0xFFFFFFU),
        LV_PART_MAIN);
    lv_obj_set_style_text_font(
        dashboard_rpm_label,
        &lv_font_montserrat_40,
        LV_PART_MAIN);
    lv_obj_align(dashboard_rpm_label, LV_ALIGN_CENTER, 0, -12);

    /* 转速单位。 */
    unit_label = lv_label_create(screen);
    lv_label_set_text(unit_label, "RPM");
    lv_obj_set_style_text_color(
        unit_label,
        lv_color_hex(0x9AA7B3U),
        LV_PART_MAIN);
    lv_obj_set_style_text_font(
        unit_label,
        &lv_font_montserrat_20,
        LV_PART_MAIN);
    lv_obj_align(unit_label, LV_ALIGN_CENTER, 0, 30);

    /* CAN 链路状态：绿色 CAN OK 或红色 CAN LOST。 */
    dashboard_status_label = lv_label_create(screen);
    lv_label_set_text(dashboard_status_label, "CAN LOST");
    lv_obj_set_style_text_color(
        dashboard_status_label,
        lv_color_hex(0xFF4040U),
        LV_PART_MAIN);
    lv_obj_align(dashboard_status_label, LV_ALIGN_BOTTOM_MID, 0, -13);

    /* 五个主刻度；400 RPM 使用红色提醒接近量程上限。 */
    Dashboard_CreateMark("0",   145, 246, 0xB8C2CCU);
    Dashboard_CreateMark("100", 90,  142, 0xB8C2CCU);
    Dashboard_CreateMark("200", 224, 48,  0xB8C2CCU);
    Dashboard_CreateMark("300", 355, 142, 0xB8C2CCU);
    Dashboard_CreateMark("400", 330, 246, 0xFF5050U);

    /* 上电时尚未收到 CAN 数据，先显示 0.0 RPM / CAN LOST。 */
    Dashboard_Update(0U, 0U);
}

/**
 * @brief 用最新 CAN 转速刷新汽车仪表盘。
 * @param rpm_x10    转速扩大 10 倍后的整数，例如 1054 表示 105.4 RPM。
 * @param can_online 1 表示 500ms 内收到过有效帧；0 表示链路超时。
 * @note 必须由 LVGL 所属任务调用，不能在 CAN 中断回调中直接调用。
 */
void Dashboard_Update(uint16_t rpm_x10, uint8_t can_online)
{
    uint16_t rpm_integer;
    uint16_t rpm_decimal;
    int32_t arc_value;

    /*
     * CAN 离线时强制归零；在线但超过 400.0 RPM 时做上限钳位，
     * 防止圆弧数值越界，同时仍能用红色表示超量程状态。
     */
    if((can_online == 0U) ||
       (rpm_x10 > DASHBOARD_RPM_MAX_X10))
    {
        if(can_online == 0U)
        {
            rpm_x10 = 0U;
        }
        else
        {
            rpm_x10 = DASHBOARD_RPM_MAX_X10;
        }
    }

    /* 拆分整数和小数，避免在 Cortex-M3 上使用开销较大的浮点 printf。 */
    rpm_integer = rpm_x10 / 10U;
    rpm_decimal = rpm_x10 % 10U;
    /* 加 5 后除以 10，实现从 0.1 RPM 到整数 RPM 的四舍五入。 */
    arc_value = (int32_t)((rpm_x10 + 5U) / 10U);

    lv_arc_set_value(dashboard_arc, arc_value);
    lv_label_set_text_fmt(
        dashboard_rpm_label,
        "%u.%u",
        (unsigned int)rpm_integer,
        (unsigned int)rpm_decimal);

    /* 根据 CAN 在线状态和红区阈值切换文字及圆弧颜色。 */
    if(can_online == 0U)
    {
        lv_label_set_text(dashboard_status_label, "CAN LOST");
        lv_obj_set_style_text_color(
            dashboard_status_label,
            lv_color_hex(0xFF4040U),
            LV_PART_MAIN);
        lv_obj_set_style_arc_color(
            dashboard_arc,
            lv_color_hex(0x59636DU),
            LV_PART_INDICATOR);
    }
    else
    {
        lv_label_set_text(dashboard_status_label, "CAN OK");
        lv_obj_set_style_text_color(
            dashboard_status_label,
            lv_color_hex(0x39E58CU),
            LV_PART_MAIN);

        if(rpm_x10 >= DASHBOARD_RED_RPM_X10)
        {
            lv_obj_set_style_arc_color(
                dashboard_arc,
                lv_color_hex(0xFF3030U),
                LV_PART_INDICATOR);
        }
        else
        {
            lv_obj_set_style_arc_color(
                dashboard_arc,
                lv_color_hex(0x00D7FFU),
                LV_PART_INDICATOR);
        }
    }
}
