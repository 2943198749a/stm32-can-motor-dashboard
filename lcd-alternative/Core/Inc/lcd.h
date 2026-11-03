/*
 * @Author: wushengran
 * @Date: 2024-06-17 14:25:00
 * @Description: 
 * 
 * Copyright (c) 2024 by atguigu, All Rights Reserved. 
 */
#ifndef __LCD_H
#define __LCD_H

#include "fsmc.h"
#include <math.h>

/*
 * FSMC Bank1 NOR/SRAM4 基地址为 0x6C000000。
 * LCD 的 RS/DC 接在 FSMC 地址线 A10；由于 16 位总线地址会左移 1 位，
 * 数据地址偏移为 1<<(10+1)=1<<11。写基地址表示命令，写偏移地址表示数据。
 */
#define SRAM_BANK1_4 0x6C000000
#define LCD_ADDR_CMD (uint16_t *)SRAM_BANK1_4
#define LCD_ADDR_DATA (uint16_t *)(SRAM_BANK1_4 + (1 << 11))
// #define LCD_ADDR_DATA (uint16_t *)(0x6cfffffe)

/* ILI9486 横屏逻辑分辨率。 */
#define LCD_W 480
#define LCD_H 320

/* MADCTL(0x36) 控制扫描方向；0xA8 是本硬件验证正确的横屏/镜像组合。 */
#define LCD_CMD_MADCTL          0x36U
#define LCD_MADCTL_LANDSCAPE    0xA8U

/* 常见颜色 */
#define WHITE 0xFFFF
#define BLACK 0x0000
#define BLUE 0x001F
#define BRED 0XF81F
#define GRED 0XFFE0
#define GBLUE 0X07FF
#define RED 0xF800
#define MAGENTA 0xF81F
#define GREEN 0x07E0
#define CYAN 0x7FFF
#define YELLOW 0xFFE0
#define BROWN 0XBC40 // 棕色
#define BRRED 0XFC07 // 棕红色
#define GRAY 0X8430  // 灰色

/** @brief 复位 ILI9486、写入寄存器配置并打开背光。 */
void LCD_Init(void);

/** @brief 通过 PG15 产生 ILI9486 硬件复位时序。 */
void LCD_Reset(void);

/** @brief PB0 输出高电平，打开 LCD 背光。 */
void LCD_BGOn(void);
/** @brief PB0 输出低电平，关闭 LCD 背光。 */
void LCD_BGOff(void);

/** @brief 写入伽马、电源、像素格式、休眠退出等 ILI9486 寄存器。 */
void LCD_RegConfig(void);

/** @brief 通过 FSMC 命令地址向 ILI9486 写一个命令。 */
void LCD_WriteCmd(uint16_t cmd);

/** @brief 通过 FSMC 数据地址向 ILI9486 写一个 16 位数据。 */
void LCD_WriteData(uint16_t data);

/** @brief 从 ILI9486 数据地址读取一个 16 位数据。 */
uint16_t LCD_ReadData(void);

// 2. 具体的命令操作

/** @brief 读取 ILI9486 三字节显示控制器 ID。 */
uint32_t LCD_ReadID(void);

/** @brief 设置已经验证的 480×320 横屏扫描方向。 */
void LCD_SetLandscape(void);

/** @brief 用指定 RGB565 颜色填充矩形，并自动裁剪到屏幕边界。 */
void LCD_FillRect(uint16_t x,
                  uint16_t y,
                  uint16_t w,
                  uint16_t h,
                  uint16_t color);



/** @brief 用指定 RGB565 颜色填充整个 480×320 屏幕。 */
void LCD_ClearAll(uint16_t color);
/** @brief 设置下一次 Memory Write 使用的列/行窗口。 */
void LCD_SetArea(uint16_t x, uint16_t y, uint16_t w, uint16_t h);

void LCD_WriteAsciiChar(uint16_t x, uint16_t y, uint16_t height, uint8_t c, uint16_t fColor, uint16_t bColor);

void LCD_WriteAsciiString(uint16_t x, uint16_t y, uint16_t height, uint8_t * str, uint16_t fColor, uint16_t bColor);

void LCD_WriteChineseChar(uint16_t x, uint16_t y, uint16_t height, uint8_t index, uint16_t fColor, uint16_t bColor);

void LCD_DisplayAtguiguLogo(uint16_t x, uint16_t y);

void LCD_DrawPoint(uint16_t x, uint16_t y, uint16_t w, uint16_t color);

void LCD_DrawLine(uint16_t x1, uint16_t y1, uint16_t x2, uint16_t y2, uint16_t w, uint16_t color);

void LCD_DrawRectangle(uint16_t x1, uint16_t y1, uint16_t x2, uint16_t y2, uint16_t w, uint16_t color);

void LCD_DrawCircle(uint16_t xCenter, uint16_t yCenter, uint16_t r, uint16_t w, uint16_t color);
void LCD_DrawCircle_Pro(uint16_t xCenter, uint16_t yCenter, uint16_t r, uint16_t w, uint16_t color);

void LCD_DrawFilledCircle(uint16_t xCenter, uint16_t yCenter, uint16_t r, uint16_t w, uint16_t bColor, uint16_t fColor);
void LCD_DrawFilledCircle_Pro(uint16_t xCenter, uint16_t yCenter, uint16_t r, uint16_t w, uint16_t bColor, uint16_t fColor);
#endif

