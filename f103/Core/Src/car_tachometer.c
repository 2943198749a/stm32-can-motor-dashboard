#include "car_tachometer.h"

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
}
