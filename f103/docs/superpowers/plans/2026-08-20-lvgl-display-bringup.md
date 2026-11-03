# LVGL 9.5 Display Bring-Up Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在保留 `defaultTask`、`lvgl` 和 `myTask03` 的 STM32F103ZET6 FreeRTOS 工程中，让 LVGL 9.5 通过已经验证的 ILI9486/FSMC 驱动显示横屏 `LVGL OK` 测试画面。

**Architecture:** `StartLvglTask()` 独占 LCD 与全部 LVGL API；`myTask03` 保留但不得调用 LCD/LVGL。LVGL 使用 RGB565、partial buffer 和同步 FSMC flush，SysTick 调度 FreeRTOS，TIM4 提供 HAL/LVGL tick。

**Tech Stack:** STM32F103ZET6、STM32Cube HAL F1、FreeRTOS CMSIS-RTOS v2、Keil ARMCC 5、LVGL 9.5.0、ILI9486/FSMC 16-bit。

**Spec:** `D:/aiguigu/STM32F407/CAN_HAL/docs/superpowers/specs/2026-08-20-f103-car-dashboard-design.md`

## Global Constraints

- 保留 `myTask03`；它只能执行自己的非显示业务和 `osDelay()`。
- `StartLvglTask()` 是唯一允许调用 LCD/LVGL API 的任务。
- 保持 `LCD_MADCTL_LANDSCAPE = 0xA8U`、`LCD_W = 480U`、`LCD_H = 320U`。
- 保持现有稳定 FSMC 时序，不在本阶段优化速度。
- 不加入 LVGL demos、examples、PC/Linux 驱动或旧 CAN_HAL 的 port 文件。
- 第一张画面只验证 LVGL display port；不加入 CAN 和汽车仪表盘。

---

### Task 1: 放置干净的 LVGL 9.5 源码与配置

**Files:**
- Copy: `D:/aiguigu/STM32F407/CAN_HAL/lvgl/src` -> `D:/aiguigu/STM32F407/42_lcd_hal/lvgl/src`
- Copy: `D:/aiguigu/STM32F407/CAN_HAL/lvgl/lvgl.h` -> `D:/aiguigu/STM32F407/42_lcd_hal/lvgl/lvgl.h`
- Copy: `D:/aiguigu/STM32F407/CAN_HAL/lvgl/lvgl_private.h` -> `D:/aiguigu/STM32F407/42_lcd_hal/lvgl/lvgl_private.h`
- Copy: `D:/aiguigu/STM32F407/CAN_HAL/lvgl/lv_version.h` -> `D:/aiguigu/STM32F407/42_lcd_hal/lvgl/lv_version.h`
- Copy then modify: `D:/aiguigu/STM32F407/CAN_HAL/lvgl/lv_conf.h` -> `D:/aiguigu/STM32F407/42_lcd_hal/lvgl/lv_conf.h`

**Interfaces:**
- Consumes: 已验证的 LVGL 9.5.0 官方源码副本。
- Produces: 可由 Keil 编译的 `lvgl.h`、`lv_conf.h` 和 `src/**/*.c`。

- [ ] **Step 1: 确认版本源**

检查源 `lv_version.h` 必须包含：

```c
#define LVGL_VERSION_MAJOR 9
#define LVGL_VERSION_MINOR 5
#define LVGL_VERSION_PATCH 0
```

- [ ] **Step 2: 复制最小库内容**

只复制 `src` 和四个根文件，不复制 `demos`、`examples`、`porting`、旧 `lv_port_lcd_stm32.*`。

- [ ] **Step 3: 配置 `lv_conf.h`**

确认或修改为：

```c
#define LV_COLOR_DEPTH 16
#define LV_USE_OS LV_OS_NONE
#define LV_MEM_SIZE (24 * 1024U)
#define LV_USE_LOG 0
#define LV_USE_LABEL 1
#define LV_USE_LINE 1
#define LV_USE_SCALE 1
#define LV_FONT_MONTSERRAT_20 1
#define LV_FONT_MONTSERRAT_40 1
#define LV_BUILD_EXAMPLES 0
#define LV_BUILD_DEMOS 0
```

- [ ] **Step 4: 验证目录**

确认存在：

```text
lvgl/lvgl.h
lvgl/lv_conf.h
lvgl/lv_version.h
lvgl/src/lv_init.c
lvgl/src/core/lv_obj.c
lvgl/src/display/lv_display.c
```

### Task 2: 将 LVGL 源码加入 Keil

**Files:**
- Modify: `D:/aiguigu/STM32F407/42_lcd_hal/MDK-ARM/42_lcd_hal.uvprojx`

**Interfaces:**
- Consumes: Task 1 的 `lvgl/src/**/*.c`。
- Produces: Keil 可编译的 LVGL 静态模块。

- [ ] **Step 1: 添加 Include Path**

在 Options for Target -> C/C++ -> Include Paths 添加：

```text
../lvgl
../lvgl/src
```

- [ ] **Step 2: 添加源码**

在 Keil 创建 `LVGL` 分组，将 `lvgl/src` 下的 `.c` 文件按子目录加入。不要加入 `demos`、`examples`，也不要加入任何 `.cpp` 文件。

- [ ] **Step 3: 首次库编译**

执行 Rebuild。预期：不再出现 `lvgl.h: No such file`、`lv_conf.h: No such file` 或重复符号；当前阶段可暂不调用 `lv_init()`。

### Task 3: 创建 STM32 显示端口

**Files:**
- Create: `D:/aiguigu/STM32F407/42_lcd_hal/Core/Inc/lv_port_disp.h`
- Create: `D:/aiguigu/STM32F407/42_lcd_hal/Core/Src/lv_port_disp.c`

**Interfaces:**
- Consumes: `LCD_SetArea(uint16_t,uint16_t,uint16_t,uint16_t)`、`LCD_WriteCmd(uint16_t)`、`LCD_WriteData(uint16_t)`。
- Produces: `lv_display_t *LV_PortDisp_Init(void)`。

- [ ] **Step 1: 创建头文件**

```c
#ifndef LV_PORT_DISP_H
#define LV_PORT_DISP_H

#include "lvgl.h"

lv_display_t *LV_PortDisp_Init(void);

#endif
```

- [ ] **Step 2: 创建实现**

```c
#include "lv_port_disp.h"
#include "lcd.h"

#define LV_PORT_HOR_RES    480U
#define LV_PORT_VER_RES    320U
#define LV_PORT_BUF_LINES  10U

static uint16_t display_buffer[
    LV_PORT_HOR_RES * LV_PORT_BUF_LINES
];

static void display_flush_cb(lv_display_t *display,
                             const lv_area_t *area,
                             uint8_t *pixel_map)
{
    uint16_t width;
    uint16_t height;
    uint16_t *pixels;
    uint32_t pixel_count;

    width = (uint16_t)(area->x2 - area->x1 + 1);
    height = (uint16_t)(area->y2 - area->y1 + 1);
    pixels = (uint16_t *)pixel_map;
    pixel_count = (uint32_t)width * (uint32_t)height;

    LCD_SetArea((uint16_t)area->x1,
                (uint16_t)area->y1,
                width,
                height);
    LCD_WriteCmd(0x2CU);

    while(pixel_count > 0U)
    {
        LCD_WriteData(*pixels);
        pixels++;
        pixel_count--;
    }

    lv_display_flush_ready(display);
}

lv_display_t *LV_PortDisp_Init(void)
{
    lv_display_t *display;

    display = lv_display_create(LV_PORT_HOR_RES,
                                LV_PORT_VER_RES);
    if(display == NULL)
    {
        return NULL;
    }

    lv_display_set_color_format(display,
                                LV_COLOR_FORMAT_RGB565);
    lv_display_set_flush_cb(display,
                            display_flush_cb);
    lv_display_set_buffers(display,
                           display_buffer,
                           NULL,
                           sizeof(display_buffer),
                           LV_DISPLAY_RENDER_MODE_PARTIAL);

    return display;
}
```

- [ ] **Step 3: 加入 Keil 并验证端口编译**

把 `lv_port_disp.c` 加入 Application/User 分组，Rebuild。预期：0 error、0 warning。

### Task 4: 在保留 Task3 的情况下显示 `LVGL OK`

**Files:**
- Modify: `D:/aiguigu/STM32F407/42_lcd_hal/Core/Src/freertos.c`

**Interfaces:**
- Consumes: `LCD_Init()`、`LCD_SetLandscape()`、`LV_PortDisp_Init()`。
- Produces: 唯一 LVGL owner `StartLvglTask()`。

- [ ] **Step 1: 添加头文件**

在 `USER CODE BEGIN Includes` 中添加：

```c
#include "lcd.h"
#include "lvgl.h"
#include "lv_port_disp.h"
#include <stdio.h>
```

- [ ] **Step 2: 替换 `StartLvglTask()` 用户代码**

```c
void StartLvglTask(void *argument)
{
    lv_obj_t *label;

    LCD_Init();
    LCD_SetLandscape();

    lv_init();
    lv_tick_set_cb(HAL_GetTick);

    if(LV_PortDisp_Init() == NULL)
    {
        printf("LVGL display create failed\r\n");
        for(;;) { osDelay(1000U); }
    }

    lv_obj_set_style_bg_color(lv_screen_active(),
                              lv_color_hex(0x05070A),
                              0);
    lv_obj_set_style_bg_opa(lv_screen_active(),
                            LV_OPA_COVER,
                            0);

    label = lv_label_create(lv_screen_active());
    lv_label_set_text(label, "LVGL OK");
    lv_obj_set_style_text_color(label,
                                lv_color_hex(0xFFFFFF),
                                0);
    lv_obj_set_style_text_font(label,
                               &lv_font_montserrat_20,
                               0);
    lv_obj_center(label);

    printf("LVGL display ready\r\n");

    for(;;)
    {
        lv_timer_handler();
        osDelay(5U);
    }
}
```

- [ ] **Step 3: 保持 `StartTask03()` 不访问显示**

```c
void StartTask03(void *argument)
{
    for(;;)
    {
        osDelay(1000U);
    }
}
```

- [ ] **Step 4: 构建并下载**

预期 Keil：0 error、0 warning。预期 LCD：480×320 深黑背景，中央白色 `LVGL OK`，方向不镜像。预期 SSCOM：`LVGL display ready`。

### Task 5: 运行时资源验证

**Files:**
- Modify for temporary diagnostics: `D:/aiguigu/STM32F407/42_lcd_hal/Core/Src/freertos.c`

**Interfaces:**
- Consumes: FreeRTOS heap、LvglTask 栈。
- Produces: LVGL 接入前的稳定性证据。

- [ ] **Step 1: 读取剩余资源**

在 `StartLvglTask()` 初始化完成后临时打印：

```c
printf("Free heap:%lu\r\n",
       (unsigned long)xPortGetFreeHeapSize());
printf("LVGL stack words:%lu\r\n",
       (unsigned long)uxTaskGetStackHighWaterMark(NULL));
```

- [ ] **Step 2: 验收**

连续运行 10 分钟；画面不闪烁、不花屏、不 HardFault；FreeRTOS heap 大于 512 bytes；LvglTask High Water Mark 大于 128 words。通过后再进入仪表盘模拟数据阶段。

