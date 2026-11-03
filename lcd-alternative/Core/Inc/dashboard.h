#ifndef DASHBOARD_H
#define DASHBOARD_H

#include "lvgl.h"
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/** @brief 创建汽车转速表的全部 LVGL 对象，只调用一次。 */
void Dashboard_Init(void);

/**
 * @brief 更新转速圆弧、数字和 CAN 状态。
 * @param rpm_x10 转速扩大 10 倍后的无符号整数。
 * @param can_online 1=CAN 在线，0=CAN 超时。
 */
void Dashboard_Update(uint16_t rpm_x10, uint8_t can_online);

#ifdef __cplusplus
}
#endif

#endif /* DASHBOARD_H */


