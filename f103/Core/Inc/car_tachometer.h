#ifndef CAR_TACHOMETER_H
#define CAR_TACHOMETER_H

#include "lvgl.h"
#include <stdbool.h>
#include <stdint.h>

void CarTachometer_Create(lv_obj_t *parent);
void CarTachometer_SetRpm(uint16_t rpm);
void CarTachometer_SetOnline(bool online);

#endif
