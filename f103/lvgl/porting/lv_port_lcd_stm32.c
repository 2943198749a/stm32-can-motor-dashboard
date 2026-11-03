/**
 * @file lv_port_lcd_stm32_template.c
 *
 * Example implementation of the LVGL LCD display drivers on the STM32 platform
 */

/*Copy this file as "lv_port_disp.c" and set this value to "1" to enable content*/
#include "lv_port_lcd_stm32.h"
#include "main.h"

#include <stdint.h>

/*
 * ILI9486 ??????? 320 x 480?
 * ????????????,?? LVGL ???? 480 x 320?
 */
#define LCD_HOR_RES                 480
#define LCD_VER_RES                 320

/*
 * ??? LVGL ?? 10 ??
 *
 * RGB565 ???? 2 ??:
 * 480 * 10 * 2 = 9600 ??
 *
 * STM32F103ZE SRAM ??,?????????
 */
#define LCD_DRAW_BUF_LINES          10
#define LCD_DRAW_BUF_PIXELS         (LCD_HOR_RES * LCD_DRAW_BUF_LINES)

/*
 * FSMC Bank4 ????? 0x6C000000?
 *
 * LCD RS/DC ??? FSMC_A10?
 * FSMC ?? 16 ??????,CPU ???????,??:
 *
 * ???? = 0x6C000000
 * ???? = 0x6C000000 + (1 << (10 + 1))
 *          = 0x6C000800
 */
#define LCD_FSMC_BANK4_BASE         0x6C000000UL
#define LCD_FSMC_RS_OFFSET          0x00000800UL

#define LCD_CMD_ADDR                LCD_FSMC_BANK4_BASE
#define LCD_DATA_ADDR               (LCD_FSMC_BANK4_BASE + LCD_FSMC_RS_OFFSET)

#define LCD_CMD_REG                 (*((__IO uint16_t *)LCD_CMD_ADDR))
#define LCD_DATA_REG                (*((__IO uint16_t *)LCD_DATA_ADDR))

/*
 * ILI9486 ????
 */
#define ILI9486_CMD_SOFT_RESET      0x01U
#define ILI9486_CMD_SLEEP_OUT       0x11U
#define ILI9486_CMD_DISPLAY_OFF     0x28U
#define ILI9486_CMD_DISPLAY_ON      0x29U
#define ILI9486_CMD_COLUMN_ADDR     0x2AU
#define ILI9486_CMD_PAGE_ADDR       0x2BU
#define ILI9486_CMD_MEMORY_WRITE    0x2CU
#define ILI9486_CMD_MEMORY_ACCESS   0x36U
#define ILI9486_CMD_PIXEL_FORMAT    0x3AU

/*
 * LVGL v9 ? lv_color_t ???????? RGB565 ??,
 * ???????? uint16_t?
 */
static uint16_t lcd_draw_buf[LCD_DRAW_BUF_PIXELS];

static lv_display_t *lcd_display;

/* ??? 8 ???,FSMC ?????? 16 ???? */
static inline void lcd_write_command(uint8_t command)
{
    LCD_CMD_REG = command;
}

/* ??? 8 ???,FSMC ?????? 16 ???? */
static inline void lcd_write_data8(uint8_t data)
{
    LCD_DATA_REG = data;
}

/* ???????????? */
static void lcd_write_parameters(const uint8_t *data, uint32_t length)
{
    uint32_t i;

    for(i = 0; i < length; i++) {
        lcd_write_data8(data[i]);
    }
}

/* ?????????? */
static void lcd_write_register(uint8_t command,
                               const uint8_t *parameters,
                               uint32_t parameter_count)
{
    lcd_write_command(command);

    if((parameters != NULL) && (parameter_count != 0U)) {
        lcd_write_parameters(parameters, parameter_count);
    }
}

/* LCD ????:PB0 ????? */
static void ili9486_hardware_reset(void)
{
    /* PG15 ? LCD RESET */
    HAL_GPIO_WritePin(GPIOG, GPIO_PIN_15, GPIO_PIN_RESET);
    HAL_Delay(100);

    HAL_GPIO_WritePin(GPIOG, GPIO_PIN_15, GPIO_PIN_SET);
    HAL_Delay(100);
}

/* ??? ILI9486 ??? */
static void ili9486_init(void)
{
    static const uint8_t positive_gamma[] = {
        0x0F, 0x1F, 0x1C, 0x0C, 0x0F,
        0x08, 0x48, 0x98, 0x37, 0x0A,
        0x13, 0x04, 0x11, 0x0D, 0x00
    };

    static const uint8_t negative_gamma[] = {
        0x0F, 0x32, 0x2E, 0x0B, 0x0D,
        0x05, 0x47, 0x75, 0x37, 0x06,
        0x10, 0x03, 0x24, 0x20, 0x00
    };

    static const uint8_t power_control_1[] = {
        0x0D, 0x0D
    };

    static const uint8_t power_control_2[] = {
        0x43, 0x00
    };

    static const uint8_t vcom_control[] = {
        0x00, 0x48
    };

    static const uint8_t display_function_control[] = {
        0x00, 0x22, 0x3B
    };

    static const uint8_t adjust_control_3[] = {
        0xA9, 0x51, 0x2C, 0x82
    };

    uint8_t value;

    ili9486_hardware_reset();

    /* ???? */
    lcd_write_command(ILI9486_CMD_SOFT_RESET);
    HAL_Delay(10);

    /*
     * Positive Gamma Control
     */
    lcd_write_register(0xE0,
                       positive_gamma,
                       sizeof(positive_gamma));

    /*
     * Negative Gamma Control
     */
    lcd_write_register(0xE1,
                       negative_gamma,
                       sizeof(negative_gamma));

    /*
     * Power Control 1
     */
    lcd_write_register(0xC0,
                       power_control_1,
                       sizeof(power_control_1));

    /*
     * Power Control 2
     */
    lcd_write_register(0xC1,
                       power_control_2,
                       sizeof(power_control_2));

    /*
     * Power Control 3
     */
    value = 0x00;
    lcd_write_register(0xC2, &value, 1);

    /*
     * VCOM Control
     */
    lcd_write_register(0xC5,
                       vcom_control,
                       sizeof(vcom_control));

    /*
     * Memory Access Control:
     *
     * 0x20 = MV,?? X/Y,?????
     * 0x08 = BGR,????? ILI9486 ??
     *
     * ????? 0x28?
     */
    value = 0x28;
    lcd_write_register(ILI9486_CMD_MEMORY_ACCESS, &value, 1);

    /*
     * RGB565,16 ???
     */
    value = 0x55;
    lcd_write_register(ILI9486_CMD_PIXEL_FORMAT, &value, 1);

    /*
     * Interface Mode Control
     */
    value = 0x00;
    lcd_write_register(0xB0, &value, 1);

    /*
     * Frame Rate Control
     */
    value = 0xA0;
    lcd_write_register(0xB1, &value, 1);

    /*
     * Display Inversion Control
     */
    value = 0x02;
    lcd_write_register(0xB4, &value, 1);

    /*
     * Display Function Control
     */
    lcd_write_register(0xB6,
                       display_function_control,
                       sizeof(display_function_control));

    /*
     * Adjust Control 3
     */
    lcd_write_register(0xF7,
                       adjust_control_3,
                       sizeof(adjust_control_3));

    /*
     * ??????
     */
    lcd_write_command(ILI9486_CMD_SLEEP_OUT);
    HAL_Delay(120);

    /*
     * ????
     */
    lcd_write_command(ILI9486_CMD_DISPLAY_ON);
    HAL_Delay(20);
}

/* ?? ILI9486 ??????????? */
static void ili9486_set_window(uint16_t x1,
                              uint16_t y1,
                              uint16_t x2,
                              uint16_t y2)
{
    lcd_write_command(ILI9486_CMD_COLUMN_ADDR);
    lcd_write_data8((uint8_t)(x1 >> 8));
    lcd_write_data8((uint8_t)(x1 & 0xFFU));
    lcd_write_data8((uint8_t)(x2 >> 8));
    lcd_write_data8((uint8_t)(x2 & 0xFFU));

    lcd_write_command(ILI9486_CMD_PAGE_ADDR);
    lcd_write_data8((uint8_t)(y1 >> 8));
    lcd_write_data8((uint8_t)(y1 & 0xFFU));
    lcd_write_data8((uint8_t)(y2 >> 8));
    lcd_write_data8((uint8_t)(y2 & 0xFFU));

    lcd_write_command(ILI9486_CMD_MEMORY_WRITE);
}

/*
 * LVGL ???????
 *
 * ??????:??????????????? LCD,
 * ???????? lv_display_flush_ready()?
 */
static void ili9486_flush_cb(lv_display_t *display,
                             const lv_area_t *area,
                             uint8_t *pixel_map)
{
    uint32_t pixel_count;
    uint16_t *pixels;

    pixel_count =
        (uint32_t)(area->x2 - area->x1 + 1) *
        (uint32_t)(area->y2 - area->y1 + 1);

    pixels = (uint16_t *)pixel_map;

    ili9486_set_window((uint16_t)area->x1,
                       (uint16_t)area->y1,
                       (uint16_t)area->x2,
                       (uint16_t)area->y2);

    while(pixel_count != 0U) {
        LCD_DATA_REG = *pixels;

        pixels++;
        pixel_count--;
    }

    lv_display_flush_ready(display);
}

void lv_port_disp_init(void)
{
    /* PB0 ? LCD ?? */
    HAL_GPIO_WritePin(GPIOB, GPIO_PIN_0, GPIO_PIN_SET);

    ili9486_init();

    lcd_display = lv_display_create(LCD_HOR_RES,
                                    LCD_VER_RES);

    if(lcd_display == NULL)
    {
        Error_Handler();
    }

    lv_display_set_color_format(
        lcd_display,
        LV_COLOR_FORMAT_RGB565);

    lv_display_set_flush_cb(
        lcd_display,
        ili9486_flush_cb);

    lv_display_set_buffers(
        lcd_display,
        lcd_draw_buf,
        NULL,
        sizeof(lcd_draw_buf),
        LV_DISPLAY_RENDER_MODE_PARTIAL);
}
