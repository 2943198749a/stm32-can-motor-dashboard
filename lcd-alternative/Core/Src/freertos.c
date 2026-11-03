/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * File Name          : freertos.c
  * Description        : Code for freertos applications
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */

/* Includes ------------------------------------------------------------------*/
#include "FreeRTOS.h"
#include "task.h"
#include "main.h"
#include "cmsis_os.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "lcd.h"
#include "lvgl.h"
#include "lv_port_disp.h"
#include <stdio.h>
#include "dashboard.h"
#include "can.h"
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
/* LVGL 任务每 20ms 检查一次共享 CAN 数据，界面实际只在数据变化时重绘。 */
#define DASHBOARD_UPDATE_PERIOD_MS  20U
/* 500ms 内没有新有效帧即认为 CAN 离线，仪表归零并显示 CAN LOST。 */
#define DASHBOARD_CAN_TIMEOUT_MS    500U

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
/* USER CODE BEGIN Variables */

/* USER CODE END Variables */
/* Definitions for defaultTask */
osThreadId_t defaultTaskHandle;
/* 默认任务仅保留 CubeMX 框架，低优先级、512 字节栈。 */
const osThreadAttr_t defaultTask_attributes = {
  .name = "defaultTask",
  .stack_size = 128 * 4,
  .priority = (osPriority_t) osPriorityLow,
};
/* Definitions for lvgl */
osThreadId_t lvglHandle;
/*
 * LVGL 软件渲染调用链较深，因此分配 1536 words = 6144 字节栈。
 * 之前 3072 字节会在第一次整屏绘制附近发生栈溢出/HardFault。
 */
const osThreadAttr_t lvgl_attributes = {
  .name = "lvgl",
  .stack_size = 1536 * 4,
  .priority = (osPriority_t) osPriorityNormal,
};
/* Definitions for myTask03 */
osThreadId_t myTask03Handle;
/* CAN 串口监视任务：Normal 优先级，1024 字节栈。 */
const osThreadAttr_t myTask03_attributes = {
  .name = "myTask03",
  .stack_size = 256 * 4,
  .priority = (osPriority_t) osPriorityNormal,
};

/* Private function prototypes -----------------------------------------------*/
/* USER CODE BEGIN FunctionPrototypes */

/* USER CODE END FunctionPrototypes */

void StartDefaultTask(void *argument);
void StartLvglTask(void *argument);
void StartTask03(void *argument);

void MX_FREERTOS_Init(void); /* (MISRA C 2004 rule 8.1) */

/* Hook prototypes */
void vApplicationStackOverflowHook(xTaskHandle xTask, signed char *pcTaskName);
void vApplicationMallocFailedHook(void);

/* USER CODE BEGIN 4 */
void vApplicationStackOverflowHook(xTaskHandle xTask, signed char *pcTaskName)
{
   /*
    * FreeRTOS 检测到任务栈溢出时进入此钩子。
    * 调试时可在此处下断点，并查看 pcTaskName 确认是哪个任务溢出。
    */
   (void)xTask;
   (void)pcTaskName;
   /* Run time stack overflow checking is performed if
   configCHECK_FOR_STACK_OVERFLOW is defined to 1 or 2. This hook function is
   called if a stack overflow is detected. */
}
/* USER CODE END 4 */

/* USER CODE BEGIN 5 */
void vApplicationMallocFailedHook(void)
{
   /* FreeRTOS 堆分配失败时进入此钩子，调试时应在此处下断点。 */
   /* vApplicationMallocFailedHook() will only be called if
   configUSE_MALLOC_FAILED_HOOK is set to 1 in FreeRTOSConfig.h. It is a hook
   function that will get called if a call to pvPortMalloc() fails.
   pvPortMalloc() is called internally by the kernel whenever a task, queue,
   timer or semaphore is created. It is also called by various parts of the
   demo application. If heap_1.c or heap_2.c are used, then the size of the
   heap available to pvPortMalloc() is defined by configTOTAL_HEAP_SIZE in
   FreeRTOSConfig.h, and the xPortGetFreeHeapSize() API function can be used
   to query the size of free heap space that remains (although it does not
   provide information on how the remaining heap might be fragmented). */
}
/* USER CODE END 5 */

/**
  * @brief  FreeRTOS initialization
  * @param  None
  * @retval None
  */
void MX_FREERTOS_Init(void) {
  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* USER CODE BEGIN RTOS_MUTEX */
  /* add mutexes, ... */
  /* USER CODE END RTOS_MUTEX */

  /* USER CODE BEGIN RTOS_SEMAPHORES */
  /* add semaphores, ... */
  /* USER CODE END RTOS_SEMAPHORES */

  /* USER CODE BEGIN RTOS_TIMERS */
  /* start timers, add new ones, ... */
  /* USER CODE END RTOS_TIMERS */

  /* USER CODE BEGIN RTOS_QUEUES */
  /* add queues, ... */
  /* USER CODE END RTOS_QUEUES */

  /* Create the thread(s) */
  /* 依次创建默认任务、LVGL 任务和 CAN 串口监视任务。 */
  /* creation of defaultTask */
  defaultTaskHandle = osThreadNew(StartDefaultTask, NULL, &defaultTask_attributes);

  /* creation of lvgl */
  lvglHandle = osThreadNew(StartLvglTask, NULL, &lvgl_attributes);

  /* creation of myTask03 */
  myTask03Handle = osThreadNew(StartTask03, NULL, &myTask03_attributes);

  /* USER CODE BEGIN RTOS_THREADS */
  /* 调度器启动前输出任务创建结果；任一句柄为 NULL 都表示堆空间不足。 */
  printf("TASK CREATE default:%s lvgl:%s task3:%s HEAP:%lu\r\n",
         (defaultTaskHandle != NULL) ? "OK" : "FAIL",
         (lvglHandle != NULL) ? "OK" : "FAIL",
         (myTask03Handle != NULL) ? "OK" : "FAIL",
         (unsigned long)xPortGetFreeHeapSize());
  /* USER CODE END RTOS_THREADS */

  /* USER CODE BEGIN RTOS_EVENTS */
  /* add events, ... */
  /* USER CODE END RTOS_EVENTS */

}

/* USER CODE BEGIN Header_StartDefaultTask */
/**
  * @brief  Function implementing the defaultTask thread.
  * @param  argument: Not used
  * @retval None
  */
/* USER CODE END Header_StartDefaultTask */
void StartDefaultTask(void *argument)
{
  /* USER CODE BEGIN StartDefaultTask */
  (void)argument;

  /*
   * 该任务目前不承担业务，只周期性阻塞，让出 CPU。
   * 保留它是为了兼容 CubeMX 生成结构和后续扩展。
   */
  /* Infinite loop */
  for(;;)
  {
    osDelay(1);
  }
  /* USER CODE END StartDefaultTask */
}

/* USER CODE BEGIN Header_StartLvglTask */
/**
* @brief Function implementing the lvgl thread.
* @param argument: Not used
* @retval None
*/
/* USER CODE END Header_StartLvglTask */
void StartLvglTask(void *argument)
{
  /* USER CODE BEGIN StartLvglTask */
  lv_display_t *display;
  uint16_t rpm_x10;
  uint16_t last_display_rpm_x10;
  uint8_t can_online;
  uint8_t last_can_online;
  uint32_t last_rx_tick;
  uint32_t dashboard_update_tick;
  uint32_t now;

  (void)argument;

  /*
   * LCD 和 LVGL 都在同一个任务中初始化并访问。
   * 这样可保证 LVGL 对象不会被多个任务同时修改。
   */
  LCD_Init();
  LCD_SetLandscape();
  LCD_ClearAll(BLACK);

  /* 初始化 LVGL 核心，并让 LVGL 直接读取 HAL 的毫秒节拍。 */
  lv_init();
  lv_tick_set_cb(HAL_GetTick);

  /* 注册 480×320 RGB565 的 ILI9486 显示端口。 */
  display = LV_PortDisp_Init();
  if(display == NULL)
  {
    /* LVGL 内存不足时停在此处，便于调试器定位。 */
    for(;;)
    {
      osDelay(1000U);
    }
  }

  /* 创建汽车转速表界面。 */
  Dashboard_Init();

  /* 使用不可能出现的初值，确保第一次轮询一定刷新 CAN 状态。 */
  last_display_rpm_x10 = 0xFFFFU;
  last_can_online = 0xFFU;
  dashboard_update_tick = HAL_GetTick();

  /* Infinite loop */
  for(;;)
  {
    now = HAL_GetTick();

    /* 每 20ms 获取一次 CAN 数据快照。 */
    if((now - dashboard_update_tick) >=
       DASHBOARD_UPDATE_PERIOD_MS)
    {
      dashboard_update_tick = now;

      /* Cortex-M3 对对齐的 16/32 位变量读取是原子的。 */
      rpm_x10 = g_can_rpm_x10;
      last_rx_tick = g_can_last_rx_tick;

      /* 同时满足“收过有效帧”和“最近一帧不超过 500ms”才算在线。 */
      if((g_can_data_valid != 0U) &&
         ((now - last_rx_tick) <=
          DASHBOARD_CAN_TIMEOUT_MS))
      {
        can_online = 1U;
      }
      else
      {
        can_online = 0U;
        rpm_x10 = 0U;
      }

      /*
       * 只有数值或链路状态变化才修改 LVGL 对象，
       * 防止相同画面被反复无意义重绘，降低 FSMC 和 CPU 负载。
       */
      if((rpm_x10 != last_display_rpm_x10) ||
         (can_online != last_can_online))
      {
        Dashboard_Update(rpm_x10, can_online);
        last_display_rpm_x10 = rpm_x10;
        last_can_online = can_online;
      }
    }

    /* 执行 LVGL 定时器、布局、绘制和显示刷新回调。 */
    (void)lv_timer_handler();

    osDelay(5U);
  }
  /* USER CODE END StartLvglTask */
}

/* USER CODE BEGIN Header_StartTask03 */
/**
* @brief Function implementing the myTask03 thread.
* @param argument: Not used
* @retval None
*/
/* USER CODE END Header_StartTask03 */
void StartTask03(void *argument)
{
  /* USER CODE BEGIN StartTask03 */
  uint16_t rpm_x10;
  uint16_t rpm_integer;
  uint16_t rpm_decimal;
  uint8_t sequence;
  uint8_t reverse;
  uint8_t valid;
  uint32_t last_tick;
  uint32_t message_age;

  (void)argument;

  /* 延迟 1 秒，让 LVGL 先完成第一次整屏刷新。 */
  osDelay(1000U);

  printf("CAN monitor task started HEAP:%lu STACK:%lu\r\n",
         (unsigned long)xPortGetFreeHeapSize(),
         (unsigned long)uxTaskGetStackHighWaterMark(NULL));

  /* Infinite loop */
  for(;;)
  {
    rpm_x10 = g_can_rpm_x10;
    sequence = g_can_sequence;
    reverse = g_can_reverse;
    valid = g_can_data_valid;
    last_tick = g_can_last_rx_tick;

    message_age = HAL_GetTick() - last_tick;

    /* 与仪表盘使用相同的 500ms 在线判断。 */
    if((valid != 0U) &&
       (message_age <= 500U))
    {
      /*
       * 不使用浮点 printf：例如 rpm_x10=375，拆分为 37 和 5，
       * 再以“37.5”的形式输出，可减少代码体积和运行开销。
       */
      rpm_integer = rpm_x10 / 10U;
      rpm_decimal = rpm_x10 % 10U;

      printf(
          "CAN RX SEQ:%u RPM:%u.%u DIR:%s AGE:%lu\r\n",
          (unsigned int)sequence,
          (unsigned int)rpm_integer,
          (unsigned int)rpm_decimal,
          (reverse != 0U) ? "REV" : "FWD",
          (unsigned long)message_age);
    }
    else
    {
      /* 尚未收到有效帧，或最后一帧已经超过 500ms。 */
      printf(
          "CAN LOST VALID:%u AGE:%lu\r\n",
          (unsigned int)valid,
          (unsigned long)message_age);
    }

    /* 每 200ms 打印一次，避免阻塞式串口输出占用过多 CPU。 */
    osDelay(200U);
  }
  /* USER CODE END StartTask03 */
}

/* Private application code --------------------------------------------------*/
/* USER CODE BEGIN Application */

/* USER CODE END Application */

