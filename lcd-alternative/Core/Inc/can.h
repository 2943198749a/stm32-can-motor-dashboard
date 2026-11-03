/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file    can.h
  * @brief   This file contains all the function prototypes for
  *          the can.c file
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
/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __CAN_H__
#define __CAN_H__

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "main.h"

/* USER CODE BEGIN Includes */

/* USER CODE END Includes */

extern CAN_HandleTypeDef hcan;

/* USER CODE BEGIN Private defines */

/* USER CODE END Private defines */

void MX_CAN_Init(void);

/* USER CODE BEGIN Prototypes */
/** @brief 启动 0x201 帧过滤和 CAN FIFO0 接收中断。 */
HAL_StatusTypeDef CAN_ReceiveStart(void);

/** 最近一次有效转速，单位 0.1 RPM。 */
extern volatile uint16_t g_can_rpm_x10;

/** F407 发送帧的 8 位序号。 */
extern volatile uint8_t g_can_sequence;

/** 电机方向：0=正转，1=反转。 */
extern volatile uint8_t g_can_reverse;

/** 有效数据标志：0=尚未收到有效帧，1=曾收到有效帧。 */
extern volatile uint8_t g_can_data_valid;

/** 最近一次有效 CAN 帧到达时的 HAL 毫秒节拍。 */
extern volatile uint32_t g_can_last_rx_tick;

/* USER CODE END Prototypes */

#ifdef __cplusplus
}
#endif

#endif /* __CAN_H__ */

