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

#include "mpu.h"
#include "BEEP.h"
#include <stdio.h>
#include "dianji.h"
#include "usart.h"
#include "can.h"

/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
/* USER CODE BEGIN Variables */

/* USER CODE END Variables */
/* Definitions for defaultTask */
osThreadId_t defaultTaskHandle;
const osThreadAttr_t defaultTask_attributes = {
  .name = "defaultTask",
  .stack_size = 128 * 4,
  .priority = (osPriority_t) osPriorityNormal,
};
/* Definitions for LED1_TASK2 */
osThreadId_t LED1_TASK2Handle;
const osThreadAttr_t LED1_TASK2_attributes = {
  .name = "LED1_TASK2",
  .stack_size = 128 * 4,
  .priority = (osPriority_t) osPriorityLow,
};
/* Definitions for FENGMING_TASK3 */
osThreadId_t FENGMING_TASK3Handle;
const osThreadAttr_t FENGMING_TASK3_attributes = {
  .name = "FENGMING_TASK3",
  .stack_size = 128 * 4,
  .priority = (osPriority_t) osPriorityLow,
};
/* Definitions for DIANJI_TASK4 */
osThreadId_t DIANJI_TASK4Handle;
const osThreadAttr_t DIANJI_TASK4_attributes = {
  .name = "DIANJI_TASK4",
  .stack_size = 128 * 4,
  .priority = (osPriority_t) osPriorityAboveNormal,
};

/* Private function prototypes -----------------------------------------------*/
/* USER CODE BEGIN FunctionPrototypes */
 
/* USER CODE END FunctionPrototypes */

void StartDefaultTask(void *argument);
void StartTask02(void *argument);
void StartTask03(void *argument);
void StartTask04(void *argument);

void MX_FREERTOS_Init(void); /* (MISRA C 2004 rule 8.1) */

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
  /* creation of defaultTask */
  defaultTaskHandle = osThreadNew(StartDefaultTask, NULL, &defaultTask_attributes);

  /* creation of LED1_TASK2 */
  LED1_TASK2Handle = osThreadNew(StartTask02, NULL, &LED1_TASK2_attributes);

  /* creation of FENGMING_TASK3 */
  FENGMING_TASK3Handle = osThreadNew(StartTask03, NULL, &FENGMING_TASK3_attributes);

  /* creation of DIANJI_TASK4 */
  DIANJI_TASK4Handle = osThreadNew(StartTask04, NULL, &DIANJI_TASK4_attributes);

  /* USER CODE BEGIN RTOS_THREADS */
  /* add threads, ... */
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
  /* Infinite loop */
 //beep_on_time(3, 100);
 // int16_t ax,ay,az,gx,gy,gz;
  for(;;)
  {
  // mpu_get_data(&ax,&ay,&az,&gx,&gy,&gz);
    // printf("AX:%d AY:%d AZ:%d | GX:%d GY:%d GZ:%d \r\n",ax,ay,az,gx,gy,gz);

      vTaskDelay(2000); // 每半秒打印一次，串口不会刷屏
    osDelay(1);
  }
  /* USER CODE END StartDefaultTask */
}

/* USER CODE BEGIN Header_StartTask02 */
/**
* @brief Function implementing the LED1_TASK2 thread.
* @param argument: Not used
* @retval None
*/
/* USER CODE END Header_StartTask02 */
void StartTask02(void *argument)
{
  /* USER CODE BEGIN StartTask02 */
  /* Infinite loop */
  for(;;)
  {
    HAL_GPIO_WritePin(LED1_GPIO_Port, LED1_Pin, GPIO_PIN_RESET);
    vTaskDelay(500);
    HAL_GPIO_WritePin(LED1_GPIO_Port, LED1_Pin, GPIO_PIN_SET);
    vTaskDelay(500);
    osDelay(1);
  }
  /* USER CODE END StartTask02 */
}

/* USER CODE BEGIN Header_StartTask03 */
/**
* @brief Function implementing the FENGMING_TASK3 thread.
* @param argument: Not used
* @retval None
*/
/* USER CODE END Header_StartTask03 */
void StartTask03(void *argument)
{
  /* USER CODE BEGIN StartTask03 */
  /* Infinite loop */
  for(;;)
  {
    // if(HAL_GPIO_ReadPin(KEY1_GPIO_Port, KEY1_Pin) == GPIO_PIN_RESET)
    // {
    //   beep_on_time(2, 100);
    //   vTaskDelay(500);
    // }

    osDelay(1);
  }
  /* USER CODE END StartTask03 */
}

/* USER CODE BEGIN Header_StartTask04 */
/**
* @brief Function implementing the DIANJI_TASK4 thread.
* @param argument: Not used
* @retval None
*/
/* USER CODE END Header_StartTask04 */
void StartTask04(void *argument)
{
    TickType_t last_wake_tick;
    float rpm;
    int32_t delta_count;
    int32_t rpm_integer;
    uint8_t print_divider = 0;

    Dianji_Init();

    /* 先使用30%占空比，电机必须悬空测试 */
    Dianji_SetDuty(800);

    if(CAN_MotorSpeedStart() != HAL_OK)
    {
        Error_Handler();
    }

    last_wake_tick = xTaskGetTickCount();

    for(;;)
    {
        vTaskDelayUntil(&last_wake_tick,
                        pdMS_TO_TICKS(50U));

        /* 每50ms读取一次编码器并计算RPM */
        Dianji_Update(50U);

        delta_count = Dianji_GetDeltaCount();
        rpm = Dianji_GetRPM();

        /*
         * 不直接使用 printf("%.1f")，
         * 避免 Keil 没有启用浮点 printf。
         */
        if(rpm >= 0.0f)
        {
            rpm_integer = (int32_t)(rpm + 0.5f);
        }
        else
        {
            rpm_integer = (int32_t)(rpm - 0.5f);
        }

        /*
         * 每4次打印一次：
         * 4 × 50ms = 200ms
         */
        print_divider++;

        if(print_divider >= 4U)
        {
            print_divider = 0U;

            printf("ENC:%ld RPM:%ld\r\n",
                   (long)delta_count,
                   (long)rpm_integer);
        }

        /* 把转速发送给F103 */
        HAL_StatusTypeDef can_result;

can_result = CAN_SendMotorSpeed(rpm);

if(can_result == HAL_BUSY)
{
    printf("CAN BUSY\r\n");
}
else if(can_result != HAL_OK)
{
    printf("CAN ERROR:%lu\r\n",
           (unsigned long)HAL_CAN_GetError(&hcan1));
}
    }

  /* USER CODE END StartTask04 */
}

/* Private application code --------------------------------------------------*/
/* USER CODE BEGIN Application */

/* USER CODE END Application */

