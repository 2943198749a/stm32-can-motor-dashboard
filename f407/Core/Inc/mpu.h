/*
 * @Author: error: error: git config user.name & please set dead value or install git && error: git config user.email & please set dead value or install git & please set dead value or install git
 * @Date: 2026-08-03 17:06:40
 * @LastEditors: error: error: git config user.name & please set dead value or install git && error: git config user.email & please set dead value or install git & please set dead value or install git
 * @LastEditTime: 2026-08-03 17:07:59
 * @FilePath: \MDK-ARMd:\aiguigu\STM32F407\LED1\Core\Src\mpu.c
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD
 * 
 * 
 * //
 *  
 */

#ifndef __MPU_H
#define __MPU_H

#include "stm32f4xx_hal.h"


void mpu_init(void);
void mpu_get_data(int16_t *ax, int16_t *ay, int16_t *az, int16_t *gx, int16_t *gy, int16_t *gz);





#endif
 

