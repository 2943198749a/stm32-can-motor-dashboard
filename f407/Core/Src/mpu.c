/*
 * @Author: error: error: git config user.name & please set dead value or install git && error: git config user.email & please set dead value or install git & please set dead value or install git
 * @Date: 2026-08-03 17:06:40
 * @LastEditors: error: error: git config user.name & please set dead value or install git && error: git config user.email & please set dead value or install git & please set dead value or install git
 * @LastEditTime: 2026-08-03 18:07:25
 * @FilePath: \MDK-ARMd:\aiguigu\STM32F407\LED1\Core\Src\KEY.c
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
 */
#include "mpu.h"
#include "i2c.h"

// 写一个寄存器
static void mpu_write(uint8_t reg, uint8_t val)
{
    HAL_I2C_Mem_Write(&hi2c1, 0xD0, reg, 1, &val, 1, 1000);
}

// 读一个寄存器
static uint8_t mpu_read(uint8_t reg)
{
    uint8_t val;
    HAL_I2C_Mem_Read(&hi2c1, 0xD0, reg, 1, &val, 1, 1000);
    return val;
}

// 初始化
void mpu_init(void)
{
    mpu_write(0x6B, 0x00); // 唤醒MPU6050
    HAL_Delay(100);
    mpu_write(0x1B, 0x18); // 陀螺仪量程设为最大
    mpu_write(0x1C, 0x00); // 加速度计量程设为±2g
}

// 读6轴原始数据
void mpu_get_data(int16_t *ax, int16_t *ay, int16_t *az, int16_t *gx, int16_t *gy, int16_t *gz)
{
    uint8_t buf[14];
    HAL_I2C_Mem_Read(&hi2c1, 0xD0, 0x3B, 1, buf, 14, 1000);
    *ax = (buf[0]<<8) | buf[1];
    *ay = (buf[2]<<8) | buf[3];
    *az = (buf[4]<<8) | buf[5];
    *gx = (buf[8]<<8) | buf[9];
    *gy = (buf[10]<<8) | buf[11];
    *gz = (buf[12]<<8) | buf[13];
}

