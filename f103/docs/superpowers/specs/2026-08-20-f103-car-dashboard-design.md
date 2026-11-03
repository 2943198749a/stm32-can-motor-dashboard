# STM32F103 FreeRTOS + LVGL 汽车转速仪表盘重建设计

日期：2026-08-20  
状态：设计已由用户确认，等待书面规格复核

## 1. 目标

在一个全新的 STM32CubeMX/Keil 工程中，用 STM32F103ZET6 接收 STM32F407 通过 CAN 发送的 JGB37-520 电机实时转速，并在 ILI9486 LCD 上使用 LVGL 9.5 显示横屏汽车转速仪表盘。

新工程必须使用 FreeRTOS（CMSIS-RTOS v2），复用本机 `42_lcd_hal` 工程中已经在同一硬件上验证过的 LCD 驱动，并以该工程的 FSMC 配置为基准在新 CubeMX 工程中重新生成 FSMC，不继续修改旧 `CAN_HAL` 工程。

新工程目录和名称：

```text
D:\aiguigu\STM32F407\F103_CAR_DASHBOARD
F103_CAR_DASHBOARD
```

## 2. 硬件基线

- MCU：STM32F103ZET6，LQFP144，512 KB Flash，64 KB SRAM。
- LCD：ILI9486，8080/FSMC 16 位并行接口。
- LCD 分辨率：物理 320×480；仪表盘使用横屏 480×320。
- LCD FSMC：Bank1 NOR/SRAM4（NE4）。
- LCD RS：FSMC A10 / PG0。
- LCD CS：FSMC NE4 / PG12。
- LCD RESET：PG15。
- LCD 背光：PB0。
- CAN1：PB8 RX、PB9 TX，100 kbit/s。
- 调试串口：USART1，PA9 TX、PA10 RX，115200 8N1。
- 调试器：Serial Wire，PA13/PA14。

CAN 必须通过两端收发器连接，CANH 对 CANH、CANL 对 CANL、两板共地。总线两端各使用 120 Ω 终端电阻；断电后 CANH 与 CANL 间测量值应约为 60 Ω。

## 3. 时钟与系统时基

- HSE：8 MHz。
- PLL：×9。
- SYSCLK/HCLK：72 MHz。
- APB1：36 MHz。
- APB2：72 MHz。
- FreeRTOS 使用 SysTick 调度，tick 频率 1000 Hz。
- HAL Timebase 使用 TIM4，避免 HAL 与 FreeRTOS 同时占用 SysTick。
- LVGL 使用 `lv_tick_set_cb(HAL_GetTick)`，其时间来自 TIM4 HAL tick。

## 4. CubeMX 外设配置

### 4.1 FSMC

启用 NOR/SRAM4（NE4），参数：

```text
Memory Type: SRAM
Data Width: 16 bits
Address/Data Mux: Disable
Burst Access: Disable
Write Operation: Enable
Extended Mode: Disable
Asynchronous Wait: Disable
Write Burst: Disable
Access Mode: A
```

引脚：

```text
PG0  FSMC_A10
PG12 FSMC_NE4
PD4  FSMC_NOE
PD5  FSMC_NWE

PD14 D0   PD15 D1   PD0 D2   PD1 D3
PE7  D4   PE8  D5   PE9 D6   PE10 D7
PE11 D8   PE12 D9   PE13 D10 PE14 D11
PE15 D12  PD8  D13  PD9 D14  PD10 D15
```

第一阶段沿用 `42_lcd_hal` 的保守时序：AddressSetup 15、AddressHold 15、DataSetup 71、BusTurnAround 15。显示稳定后，才单独测试更快时序；每次只改一个参数。

LCD 命令和数据地址：

```c
#define LCD_ADDR_CMD  ((volatile uint16_t *)0x6C000000UL)
#define LCD_ADDR_DATA ((volatile uint16_t *)0x6C000800UL)
```

### 4.2 GPIO

- PB0：GPIO 输出，LCD 背光，上电初始低。
- PG15：GPIO 输出，LCD 复位，上电初始高。
- 两者均为推挽输出、无上下拉、高速。

### 4.3 CAN1

CAN 时钟为 36 MHz：

```text
Mode: Normal
Prescaler: 20
SJW: 1 TQ
BS1: 13 TQ
BS2: 4 TQ
Baud rate: 100 kbit/s
Automatic Bus-Off: Enable
Automatic Retransmission: Enable
Receive FIFO Locked: Disable
Transmit FIFO Priority: Enable
```

CAN1 重映射至 PB8/PB9。启用 `USB_LP_CAN1_RX0_IRQn`，抢占优先级 5、子优先级 0。由于 ISR 会调用 FreeRTOS 队列 API，该中断不得使用数值小于 `configLIBRARY_MAX_SYSCALL_INTERRUPT_PRIORITY` 的优先级。

### 4.4 FreeRTOS

- API：CMSIS-RTOS v2。
- 内存：动态分配，heap_4。
- `configTOTAL_HEAP_SIZE`：8192 bytes。
- `configCHECK_FOR_STACK_OVERFLOW`：2。
- `configUSE_MALLOC_FAILED_HOOK`：1。
- 不创建不必要的任务、定时器、信号量或互斥锁。

## 5. 工程模块

```text
Core/       CubeMX 生成的 HAL、外设、main、FreeRTOS 文件
BSP/        裁剪后的现成 lcd.c/lcd.h
LVGL/       精简 LVGL 9.5、lv_conf.h、显示 port
App/        dashboard、motor_can_rx
MDK-ARM/    Keil 工程
```

职责边界：

- CubeMX/HAL 负责 GPIO、FSMC、CAN、USART、TIM4 和 FreeRTOS 初始化。
- LCD 驱动负责 ILI9486 复位、寄存器初始化、窗口设置、命令和像素写入。
- LVGL port 只负责把 LVGL RGB565 刷新区域写入现成 LCD 驱动。
- Dashboard 只负责创建和更新仪表盘对象。
- Motor CAN 模块只负责接收和解析 CAN 0x201 数据。
- 只有 LvglTask 可以调用 LVGL 和 LCD API。

## 6. 现成 LCD 驱动复用规则

来源：

```text
D:\aiguigu\STM32F407\42_lcd_hal\Core\Src\lcd.c
D:\aiguigu\STM32F407\42_lcd_hal\Core\Inc\lcd.h
```

`42_lcd_hal\Core\Src\fsmc.c` 仅用于核对引脚、Bank、总线宽度、地址和已验证时序；新工程的 `fsmc.c/h` 必须由新工程自己的 CubeMX 生成，不能直接复制旧工程的生成文件。

保留并复用已经验证的 ILI9486 寄存器序列和这些基础接口：

```c
LCD_Init
LCD_Reset
LCD_BGOn
LCD_BGOff
LCD_RegConfig
LCD_WriteCmd
LCD_WriteData
LCD_ReadData
LCD_SetArea
LCD_ClearAll
```

删除由 LVGL 替代的 ASCII/中文/图片/点线圆等旧绘图接口及字模资源。`MX_FSMC_Init()` 由 CubeMX 的 `main()` 调用，裁剪后的 `LCD_Init()` 不再重复调用它。

增加 `LCD_SetRotation()`。先按原驱动的 `MADCTL=0x08` 验证纵屏，再用 `0x28` 测试 480×320 横屏，并用四色角标判断镜像、旋转和坐标范围。

## 7. LVGL 配置

- 版本：LVGL 9.5。
- 不加入 demos、examples、PC/Linux 驱动、GLTF、FFmpeg、VG-Lite 等无关模块。
- RGB565，颜色深度 16。
- LVGL 内存池初值 20 KB。
- Draw buffer：480×10×2 = 9600 bytes，partial render。
- `LV_USE_OS = LV_OS_NONE`；因为全部 LVGL API 均由单个 LvglTask 调用。
- 仅启用 label、line、scale、animation、Montserrat 20 和 40 等仪表盘必需功能。

Flush 回调流程：

```text
LVGL area + RGB565 pixel_map
-> LCD_SetArea
-> LCD_WriteCmd(0x2C)
-> 逐像素 LCD_WriteData
-> lv_display_flush_ready
```

## 8. FreeRTOS 数据流

### 8.1 LvglTask

- 优先级：Normal。
- 栈：3072 bytes 起步，调试阶段检查 High Water Mark。
- 依次初始化 LCD、LVGL display、Dashboard 和 CAN 接收通知。
- 每次循环清空 motorCanQueue，只采用最新有效帧。
- 调用 `lv_timer_handler()`，再 `osDelay(5)`。
- 500 ms 无有效 CAN 帧时显示 CAN LOST，并将目标转速设为 0。

### 8.2 DefaultTask

- 只 `osDelay(1000)`，不访问 LCD、LVGL 或 CAN 业务。
- 调试阶段可打印任务存活信息，正式版本可保持空闲。

### 8.3 motorCanQueue

- CMSIS-RTOS v2 message queue。
- 深度：8。
- 元素：`MotorCanFrame_t`。
- ISR 中 `osMessageQueuePut(..., timeout=0)`，队列满则丢弃当前帧并增加诊断计数，绝不在 ISR 等待。

## 9. CAN 协议

F407 每 50 ms 发送：

```text
Standard ID: 0x201
DLC: 4
Byte0: RPM×10 low byte
Byte1: RPM×10 high byte
Byte2: sequence
Byte3 bit7: valid
Byte3 bit0: reverse
```

F103 仅接受标准数据帧 ID 0x201。CAN ISR 只读取、验证、解析并投递队列，不调用 LVGL、不延时、不大量打印。

## 10. 仪表盘

- 横屏 480×320。
- 量程：0–400 RPM。
- 主刻度：50 RPM；小刻度：10 RPM。
- 红区：320–400 RPM。
- 深色背景、红色指针、白色数字、RPM 单位。
- 状态：CAN WAIT、CAN OK、CAN LOST。
- 转速变化使用约 120 ms 动画平滑显示。
- 正式接 CAN 前，先用 0→400→0 的模拟转速验证 UI。

## 11. 实施阶段与验收

1. CubeMX + FreeRTOS + USART：两个任务持续运行，0 error、0 warning。
2. 现成 LCD 驱动：红绿蓝白黑全屏测试正确，刷屏时 RTOS 仍调度。
3. 横屏：480×320 四角颜色位置正确，无镜像和越界。
4. LVGL port：显示 `LVGL OK` 和四色角标，刷新持续、颜色正确。
5. 模拟仪表盘：0–400–0 平滑运行 10 分钟，无残影、死机和内存异常。
6. CAN 联调：0x201 实时 RPM 与 F407 串口一致；断线 500 ms 显示 LOST，恢复后自动 OK。
7. 最终连续运行至少 30 分钟，无花屏、栈溢出或队列阻塞。

## 12. 故障处理

- HAL 初始化失败：串口输出明确错误编号，再进入受控错误状态。
- 启用 stack overflow hook，打印任务名后停机。
- 启用 malloc failed hook，打印错误后停机。
- CAN 开启 ABOM 和自动重发；业务层用 500 ms 超时显示离线。
- ISR 不使用阻塞调用，不调用 LVGL，不执行 HAL_Delay。
- 调试时一次只改变一个变量：LCD 引脚、MADCTL、FSMC 时序、颜色格式分别验证。

## 13. 非目标

第一版不加入触摸屏、SD 卡、USB、MPU6050、蜂鸣器、按键、外部 SRAM、FreeRTOS 软件定时器、多任务 LVGL、LCD DMA 或双缓冲。只有在基础版本稳定并有明确需求后再增加。
