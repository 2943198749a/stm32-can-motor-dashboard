/*
 * @Author: error: error: git config user.name & please set dead value or install git && error: git config user.email & please set dead value or install git & please set dead value or install git
 * @Date: 2026-08-03 16:37:11
 * @LastEditors: error: error: git config user.name & please set dead value or install git && error: git config user.email & please set dead value or install git & please set dead value or install git
 * @LastEditTime: 2026-08-03 18:55:43
 * @FilePath: \MDK-ARMd:\aiguigu\STM32F407\LED1\Core\Src\BEEP.c
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
 */
#include "BEEP.h"

void beep_on_time(int times, int delay)
{
    for (int i = 0; i < times; i++)
    {
        BEEP_ON();
        vTaskDelay(delay);
        BEEP_OFF();
        vTaskDelay(delay);
    }
}

