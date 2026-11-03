/**
 * @file lv_ili9486.c
 *
 */

/*********************
 *      INCLUDES
 *********************/
#include "lv_ili9486.h"

#if LV_USE_ILI9486 

/*********************
 *      DEFINES
 *********************/

#define CMD_FRMCTR1     0xB1    /* Frame Rate Control (In Normal Mode/Full Colors) */
#define CMD_FRMCTR2     0xB2    /* Frame Rate Control (In Idle Mode/8 colors) */
#define CMD_FRMCTR3     0xB3    /* Frame Rate control (In Partial Mode/Full Colors) */
#define CMD_INVCTR      0xB4    /* Display Inversion Control */
#define CMD_DFUNCTR     0xB6    /* Display Function Control */
#define CMD_PWCTR1      0xC0    /* Power Control 1 */
#define CMD_PWCTR2      0xC1    /* Power Control 2 */
#define CMD_VMCTR1      0xC5    /* VCOM Control 1 */
#define CMD_VMCTR2      0xC7    /* VCOM Control 2 */
#define CMD_PWCTRA      0xCB    /* Power Control A */
#define CMD_PWCTRB      0xCF    /* Power Control B */
#define CMD_GMCTRP1     0xE0    /* Positive Gamma Correction */
#define CMD_GMCTRN1     0xE1    /* Negative Gamma Correction */
#define CMD_DTCTRA      0xE8    /* Driver timing control A */
#define CMD_DTCTRB      0xEA    /* Driver timing control B */
#define CMD_PONSEQ      0xED    /* Power On Sequence */
#define CMD_RDINDEX     0xD9    /* ili9486 */
#define CMD_IDXRD       0xDD    /* ILI9486 only, indexed control register read */
#define CMD_ENA3G       0xF2    /* Enable 3 Gamma control */
#define CMD_IFCTR       0xF6    /* Interface Control */
#define CMD_PRCTR       0xF7    /* Pump ratio control */

/**********************
 *      TYPEDEFS
 **********************/

/**********************
 *  STATIC PROTOTYPES
 **********************/

/**********************
 *  STATIC CONSTANTS
 **********************/

/* init commands based on LovyanGFX ILI9486 driver */
static const uint8_t t_init_cmd_list[] = {
    0x01, 0x80, 120,               // 软件复位，延时120ms
    0x11, 0x80, 120,               // 退出睡眠模式，延时120ms
    0x3A, 0x01, 0x55,              // 设置像素格式为RGB565 16位色深
    0xC0, 0x02, 0x0C, 0x02,        // 电源控制1，调整VGH/VGL电压
    0xC1, 0x01, 0x42,              // 电源控制2
    0xC5, 0x01, 0x3F,              // VCOM控制
    0x36, 0x01, 0x48,              // 内存访问控制，适配480x320横屏/竖屏扫描方向
    0x29, 0x80, 100,               // 开启显示，延时100ms
    0x00                           // 指令序列结束标记
};

/**********************
 *  STATIC VARIABLES
 **********************/

/**********************
 *      MACROS
 **********************/

/**********************
 *   GLOBAL FUNCTIONS
 **********************/

lv_display_t * lv_ili9486_create(uint32_t hor_res, uint32_t ver_res, lv_lcd_flag_t flags,
                                 lv_ili9486_send_cmd_cb_t send_cmd_cb, lv_ili9486_send_color_cb_t send_color_cb)
{
    lv_display_t * disp = lv_lcd_generic_mipi_create(hor_res, ver_res, flags, send_cmd_cb, send_color_cb);
    lv_lcd_generic_mipi_send_cmd_list(disp, init_cmd_list);
    return disp;
}

void lv_ili9486_set_gap(lv_display_t * disp, uint16_t x, uint16_t y)
{
    lv_lcd_generic_mipi_set_gap(disp, x, y);
}

void lv_ili9486_set_invert(lv_display_t * disp, bool invert)
{
    lv_lcd_generic_mipi_set_invert(disp, invert);
}

void lv_ili9486_set_gamma_curve(lv_display_t * disp, uint8_t gamma)
{
    lv_lcd_generic_mipi_set_gamma_curve(disp, gamma);
}

void lv_ili9486_send_cmd_list(lv_display_t * disp, const uint8_t * cmd_list)
{
    lv_lcd_generic_mipi_send_cmd_list(disp, cmd_list);
}

/**********************
 *   STATIC FUNCTIONS
 **********************/

#endif /*LV_USE_ILI9486*/
