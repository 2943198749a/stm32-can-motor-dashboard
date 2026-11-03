#ifndef MOTOR_CAN_RX_H
#define MOTOR_CAN_RX_H

#include "main.h"
#include <stdbool.h>
#include <stdint.h>

#define MOTOR_CAN_ID          0x201U
#define MOTOR_CAN_TIMEOUT_MS  500U
typedef struct
{
    float rpm;
    bool reverse;
    bool valid;
    uint8_t sequence;
    uint32_t last_receive_tick;
} MotorCanData_t;

void MotorCanRx_Init(void);
MotorCanData_t MotorCanRx_GetData(void);

#endif
