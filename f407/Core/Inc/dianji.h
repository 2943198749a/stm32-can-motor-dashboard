/* Core/Inc/dianji.h */
#ifndef __DIANJI_H
#define __DIANJI_H

#include "main.h"

#define DIANJI_ENCODER_LINES       (13.0f)
#define DIANJI_GEAR_RATIO          (30.0f)
#define DIANJI_ENCODER_MULTIPLIER  (4.0f)

#define DIANJI_ENCODER_CPR         \
    (DIANJI_ENCODER_LINES *        \
     DIANJI_GEAR_RATIO *           \
     DIANJI_ENCODER_MULTIPLIER)

#define DIANJI_ENCODER_SIGN        (1)

void Dianji_Init(void);
void Dianji_SetDuty(int16_t duty);
void Dianji_Update(uint32_t period_ms);

int32_t Dianji_GetDeltaCount(void);
int32_t Dianji_GetTotalCount(void);
float Dianji_GetRPM(void);

#endif
