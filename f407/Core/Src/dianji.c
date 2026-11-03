/*
 * @Author: error: error: git config user.name & please set dead value or install git && error: git config user.email & please set dead value or install git & please set dead value or install git
 * @Date: 2026-08-05 19:45:03
 * @LastEditors: error: error: git config user.name & please set dead value or install git && error: git config user.email & please set dead value or install git & please set dead value or install git
 * @LastEditTime: 2026-08-05 19:49:35
 * @FilePath: \MDK-ARMd:\aiguigu\STM32F407\LED1\Core\Src\dianji.c
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
 */
/* Core/Src/dianji.c */

/* Core/Src/dianji.c */

#include "dianji.h"
#include "tim.h"

static volatile int32_t dianji_delta_count = 0;
static volatile int32_t dianji_total_count = 0;
static volatile float dianji_rpm = 0.0f;

static int16_t Dianji_ClampDuty(int16_t duty)
{
    if (duty > 1000) return 1000;
    if (duty < -1000) return -1000;

    return duty;
}

void Dianji_Init(void)
{
    HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_1);
    HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_2);

    HAL_TIM_Encoder_Start(&htim2, TIM_CHANNEL_ALL);

    __HAL_TIM_SET_COUNTER(&htim2, 0);

    dianji_delta_count = 0;
    dianji_total_count = 0;
    dianji_rpm = 0.0f;

    Dianji_SetDuty(0);
}

void Dianji_SetDuty(int16_t duty)
{
    uint32_t period;
    uint32_t magnitude;

    duty = Dianji_ClampDuty(duty);
    period = __HAL_TIM_GET_AUTORELOAD(&htim1) + 1U;

    if (duty > 0)
    {
        magnitude = ((uint32_t)duty * period) / 1000U;

        __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_1, period);
        __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_2, period - magnitude);
    }
    else if (duty < 0)
    {
        magnitude = ((uint32_t)(-duty) * period) / 1000U;

        __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_1, period - magnitude);
        __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_2, period);
    }
    else
    {
        __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_1, 0);
        __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_2, 0);
    }
}

void Dianji_Update(uint32_t period_ms)
{
    int32_t delta;
    float raw_rpm;

    if(period_ms == 0U)
    {
        return;
    }

    delta = (int32_t)__HAL_TIM_GET_COUNTER(&htim2);
    __HAL_TIM_SET_COUNTER(&htim2, 0U);

    delta *= DIANJI_ENCODER_SIGN;
    dianji_delta_count = delta;
    dianji_total_count += delta;

    raw_rpm = ((float)delta * 60000.0f) /
              (DIANJI_ENCODER_CPR * (float)period_ms);

    /* 一阶低通：兼顾响应速度与仪表盘稳定性。 */
    dianji_rpm += 0.25f * (raw_rpm - dianji_rpm);

    if((dianji_rpm > -0.15f) &&
       (dianji_rpm < 0.15f))
    {
        dianji_rpm = 0.0f;
    }
}

int32_t Dianji_GetDeltaCount(void)
{
    return dianji_delta_count;
}

int32_t Dianji_GetTotalCount(void)
{
    return dianji_total_count;
}

float Dianji_GetRPM(void)
{
    return dianji_rpm;
}


