#ifndef LV_PORT_DISP_H
#define LV_PORT_DISP_H

#include "lvgl.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief 注册 STM32F103 + FSMC + ILI9486 的 LVGL 显示端口。
 * @return 成功返回 LVGL 显示对象，失败返回 NULL。
 */
lv_display_t *LV_PortDisp_Init(void);

#ifdef __cplusplus
}
#endif

#endif /* LV_PORT_DISP_H */
