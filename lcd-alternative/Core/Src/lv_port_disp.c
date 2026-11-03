#include "lv_port_disp.h"

#include "lcd.h"

/* LVGL 逻辑分辨率与 ILI9486 横屏分辨率保持一致。 */
#define LV_PORT_DISP_HOR_RES       LCD_W
#define LV_PORT_DISP_VER_RES       LCD_H
/*
 * 局部刷新缓冲区一次保存 10 行 RGB565 像素：
 * 480×10×2 = 9600 字节。采用单缓冲可节省 STM32F103 的 SRAM。
 */
#define LV_PORT_DISP_BUF_LINES     10U

static uint16_t lv_port_disp_buf[LV_PORT_DISP_HOR_RES *
                                 LV_PORT_DISP_BUF_LINES];

/**
 * @brief LVGL 显示刷新回调，把 RGB565 像素块写入 ILI9486。
 * @param display   发起刷新的 LVGL 显示对象。
 * @param area      本次需要更新的矩形区域，坐标包含边界。
 * @param pixel_map LVGL 已渲染好的 RGB565 像素数据首地址。
 * @note 当前使用 FSMC 轮询写入；写完后必须调用 lv_display_flush_ready()。
 */
static void LV_PortDisp_Flush(lv_display_t *display,
                              const lv_area_t *area,
                              uint8_t *pixel_map)
{
    uint32_t pixel_count;
    uint16_t *pixels;

    /* x2/y2 为包含式终点，所以宽高都要加 1。 */
    pixel_count =
        (uint32_t)(area->x2 - area->x1 + 1) *
        (uint32_t)(area->y2 - area->y1 + 1);

    /* 工程颜色格式为 RGB565，每个像素占 16 位。 */
    pixels = (uint16_t *)pixel_map;

    /* 设置 ILI9486 写入窗口，并发送 Memory Write(0x2C) 命令。 */
    LCD_SetArea((uint16_t)area->x1,
                (uint16_t)area->y1,
                (uint16_t)(area->x2 - area->x1 + 1),
                (uint16_t)(area->y2 - area->y1 + 1));
    LCD_WriteCmd(0x2CU);

    /* FSMC 映射为存储器访问，连续写数据地址即可发送全部像素。 */
    while(pixel_count > 0U)
    {
        LCD_WriteData(*pixels);
        pixels++;
        pixel_count--;
    }

    /* 通知 LVGL：缓冲区已可重新用于下一块区域的渲染。 */
    lv_display_flush_ready(display);
}

/**
 * @brief 创建并配置 LVGL 显示设备。
 * @return 成功返回显示对象指针；内存不足时返回 NULL。
 */
lv_display_t *LV_PortDisp_Init(void)
{
    lv_display_t *display;

    /* 创建 480×320 的逻辑显示设备。 */
    display = lv_display_create(LV_PORT_DISP_HOR_RES,
                                LV_PORT_DISP_VER_RES);
    if(display == NULL)
    {
        return NULL;
    }

    /* ILI9486 已配置为 16bit/pixel，因此 LVGL 使用 RGB565。 */
    lv_display_set_color_format(display,
                                LV_COLOR_FORMAT_RGB565);
    lv_display_set_flush_cb(display,
                            LV_PortDisp_Flush);
    /* PARTIAL 模式配合 10 行单缓冲，避免申请完整帧缓冲。 */
    lv_display_set_buffers(display,
                           lv_port_disp_buf,
                           NULL,
                           sizeof(lv_port_disp_buf),
                           LV_DISPLAY_RENDER_MODE_PARTIAL);

    return display;
}
