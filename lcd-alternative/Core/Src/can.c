/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file    can.c
  * @brief   This file provides code for the configuration
  *          of the CAN instances.
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
#include "can.h"

/* USER CODE BEGIN 0 */
#include <string.h>

/*
 * CAN 中断与 FreeRTOS 任务共享的数据快照。
 * 使用 volatile 防止编译器把任务中的读取优化为寄存器缓存。
 * rpm_x10 的单位是 0.1 RPM，例如 1054 代表 105.4 RPM。
 */
volatile uint16_t g_can_rpm_x10 = 0U;
/* F407 每发送一帧加 1 的序号，用于观察丢帧。 */
volatile uint8_t g_can_sequence = 0U;
/* 方向标志：0=正转，1=反转。当前 LCD 只显示转速，串口保留方向。 */
volatile uint8_t g_can_reverse = 0U;
/* 收到至少一帧协议正确且有效标志为 1 的数据后置 1。 */
volatile uint8_t g_can_data_valid = 0U;
/* 最近一次有效帧到达时的 HAL 毫秒节拍，用于 500ms 超时判断。 */
volatile uint32_t g_can_last_rx_tick = 0U;
/* USER CODE END 0 */

CAN_HandleTypeDef hcan;

/* CAN init function */
void MX_CAN_Init(void)
{

  /* USER CODE BEGIN CAN_Init 0 */

  /* USER CODE END CAN_Init 0 */

  /* USER CODE BEGIN CAN_Init 1 */
  /*
   * CAN 时钟来自 APB1：36MHz。
   * 位时间 = 1(Sync) + 13(BS1) + 4(BS2) = 18TQ；
   * 波特率 = 36MHz / 20 / 18 = 100kbps。
   */
  /* USER CODE END CAN_Init 1 */
  hcan.Instance = CAN1;
  hcan.Init.Prescaler = 20;
  hcan.Init.Mode = CAN_MODE_NORMAL;
  hcan.Init.SyncJumpWidth = CAN_SJW_1TQ;
  hcan.Init.TimeSeg1 = CAN_BS1_13TQ;
  hcan.Init.TimeSeg2 = CAN_BS2_4TQ;
  hcan.Init.TimeTriggeredMode = DISABLE;
  hcan.Init.AutoBusOff = ENABLE;
  hcan.Init.AutoWakeUp = DISABLE;
  hcan.Init.AutoRetransmission = ENABLE;
  hcan.Init.ReceiveFifoLocked = DISABLE;
  hcan.Init.TransmitFifoPriority = ENABLE;
  if (HAL_CAN_Init(&hcan) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN CAN_Init 2 */

  /* USER CODE END CAN_Init 2 */

}

void HAL_CAN_MspInit(CAN_HandleTypeDef* canHandle)
{

  GPIO_InitTypeDef GPIO_InitStruct = {0};
  if(canHandle->Instance==CAN1)
  {
  /* USER CODE BEGIN CAN1_MspInit 0 */

  /* USER CODE END CAN1_MspInit 0 */
    /* CAN1 clock enable */
    __HAL_RCC_CAN1_CLK_ENABLE();

    __HAL_RCC_GPIOB_CLK_ENABLE();
    /**CAN GPIO Configuration
    PB8     ------> CAN_RX
    PB9     ------> CAN_TX
    */
    GPIO_InitStruct.Pin = GPIO_PIN_8;
    GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
    GPIO_InitStruct.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

    GPIO_InitStruct.Pin = GPIO_PIN_9;
    GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

    __HAL_AFIO_REMAP_CAN1_2();

    /* CAN1 interrupt Init */
    HAL_NVIC_SetPriority(USB_LP_CAN1_RX0_IRQn, 5, 0);
    HAL_NVIC_EnableIRQ(USB_LP_CAN1_RX0_IRQn);
  /* USER CODE BEGIN CAN1_MspInit 1 */

  /* USER CODE END CAN1_MspInit 1 */
  }
}

void HAL_CAN_MspDeInit(CAN_HandleTypeDef* canHandle)
{

  if(canHandle->Instance==CAN1)
  {
  /* USER CODE BEGIN CAN1_MspDeInit 0 */

  /* USER CODE END CAN1_MspDeInit 0 */
    /* Peripheral clock disable */
    __HAL_RCC_CAN1_CLK_DISABLE();

    /**CAN GPIO Configuration
    PB8     ------> CAN_RX
    PB9     ------> CAN_TX
    */
    HAL_GPIO_DeInit(GPIOB, GPIO_PIN_8|GPIO_PIN_9);

    /* CAN1 interrupt Deinit */
    HAL_NVIC_DisableIRQ(USB_LP_CAN1_RX0_IRQn);
  /* USER CODE BEGIN CAN1_MspDeInit 1 */

  /* USER CODE END CAN1_MspDeInit 1 */
  }
}

/* USER CODE BEGIN 1 */




/**
 * @brief CAN FIFO0 收到消息后的 HAL 中断回调。
 * @param can_handle 触发中断的 CAN 外设句柄。
 * @note 中断中只做取帧、校验和保存，不调用 LVGL 或 printf。
 */
void HAL_CAN_RxFifo0MsgPendingCallback(
    CAN_HandleTypeDef *can_handle)
{
    CAN_RxHeaderTypeDef rx_header;
    uint8_t rx_data[8];

    /* 只处理本工程使用的 CAN1，防止以后增加其他 CAN 外设时串扰。 */
    if(can_handle->Instance != CAN1)
    {
        return;
    }

    /* 从 FIFO0 取出一帧；读取失败时直接退出本次回调。 */
    if(HAL_CAN_GetRxMessage(
           can_handle,
           CAN_RX_FIFO0,
           &rx_header,
           rx_data) != HAL_OK)
    {
        return;
    }

    /*
     * 严格校验协议：标准数据帧、标准 ID=0x201、有效载荷=4 字节。
     * 不符合条件的帧不会修改上一份有效转速数据。
     */
    if((rx_header.IDE == CAN_ID_STD) &&
       (rx_header.RTR == CAN_RTR_DATA) &&
       (rx_header.StdId == 0x201U) &&
       (rx_header.DLC == 4U))
    {
        /* Byte3 bit7 必须为 1，表示 F407 发送端数据有效。 */
        if((rx_data[3] & 0x80U) != 0U)
        {
            /* Byte0/Byte1 按小端序组合成 RPM×10。 */
            g_can_rpm_x10 =
                (uint16_t)rx_data[0] |
                ((uint16_t)rx_data[1] << 8);

            /* Byte2 是 8 位循环序号，可通过跳号判断是否丢帧。 */
            g_can_sequence =
                rx_data[2];

            /* Byte3 bit0 是方向：0=正转，1=反转。 */
            g_can_reverse =
                rx_data[3] & 0x01U;

            /* 先记录到达时间，最后置有效标志，供任务侧判断在线状态。 */
            g_can_last_rx_tick =
                HAL_GetTick();

            g_can_data_valid = 1U;
        }
    }
}



/**
 * @brief 配置 0x201 精确过滤器、启动 CAN1 并打开 FIFO0 接收中断。
 * @return HAL_OK 表示三个步骤全部成功，否则返回 HAL_ERROR。
 */
HAL_StatusTypeDef CAN_ReceiveStart(void)
{
    CAN_FilterTypeDef filter;

    /* 先清零结构体，避免未填写的保留字段带入随机值。 */
    memset(&filter, 0, sizeof(filter));

    /* CAN1 使用过滤器组 0。 */
    filter.FilterBank = 0U;

    /* 使用 ID/Mask 模式实现精确 ID 过滤。 */
    filter.FilterMode = CAN_FILTERMODE_IDMASK;

    /* 32 位过滤器可以同时匹配标准 ID、IDE 和 RTR 位。 */
    filter.FilterScale = CAN_FILTERSCALE_32BIT;

    /* bxCAN 的 11 位标准 ID 放在过滤寄存器高 16 位的 bit15:5。 */
    filter.FilterIdHigh =
        (uint16_t)(0x201U << 5);

    filter.FilterIdLow = 0x0000U;

    /* 0x7FF 覆盖全部 11 个标准 ID 位，因此只接受 0x201。 */
    filter.FilterMaskIdHigh =
        (uint16_t)(0x7FFU << 5);

    /* 低半字掩码 0x0006 同时校验 IDE=0（标准帧）和 RTR=0（数据帧）。 */
    filter.FilterMaskIdLow = 0x0006U;

    /* 匹配到的报文进入接收 FIFO0。 */
    filter.FilterFIFOAssignment =
        CAN_RX_FIFO0;

    /* 激活该过滤器。 */
    filter.FilterActivation = ENABLE;

    /* 过滤器组 14 以后分配给 CAN2；本工程仅使用 CAN1 的组 0。 */
    filter.SlaveStartFilterBank = 14U;

    /* 第一步：把过滤器配置写入 bxCAN。 */
    if(HAL_CAN_ConfigFilter(
           &hcan,
           &filter) != HAL_OK)
    {
        return HAL_ERROR;
    }

    /* 第二步：从初始化状态切换到 CAN 正常工作状态。 */
    if(HAL_CAN_Start(&hcan) != HAL_OK)
    {
        return HAL_ERROR;
    }

    /* 第三步：使能 FIFO0“有新消息”中断。 */
    if(HAL_CAN_ActivateNotification(
           &hcan,
           CAN_IT_RX_FIFO0_MSG_PENDING)
       != HAL_OK)
    {
        return HAL_ERROR;
    }

    return HAL_OK;
}


/* USER CODE END 1 */
