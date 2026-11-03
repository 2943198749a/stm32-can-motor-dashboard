#include "motor_can_rx.h"
#include "can.h"

static volatile uint16_t motor_rpm_x10;
static volatile uint8_t motor_sequence;
static volatile uint8_t motor_status;
static volatile uint32_t motor_last_receive_tick;
static volatile uint8_t motor_has_received;

void MotorCanRx_Init(void)
{
    CAN_FilterTypeDef filter = {0};

    filter.FilterIdHigh = (uint16_t)(MOTOR_CAN_ID << 5);
    filter.FilterIdLow = 0x0000U;
    filter.FilterMaskIdHigh = 0xFFE0U;
    filter.FilterMaskIdLow = 0x0006U;
    filter.FilterFIFOAssignment = CAN_RX_FIFO0;
    filter.FilterBank = 0U;
    filter.FilterMode = CAN_FILTERMODE_IDMASK;
    filter.FilterScale = CAN_FILTERSCALE_32BIT;
    filter.FilterActivation = ENABLE;
    filter.SlaveStartFilterBank = 14U;

    if(HAL_CAN_ConfigFilter(&hcan, &filter) != HAL_OK)
        Error_Handler();

    if(HAL_CAN_Start(&hcan) != HAL_OK)
        Error_Handler();

    if(HAL_CAN_ActivateNotification(
           &hcan, CAN_IT_RX_FIFO0_MSG_PENDING) != HAL_OK)
        Error_Handler();
}

void HAL_CAN_RxFifo0MsgPendingCallback(CAN_HandleTypeDef *can_handle)
{
    CAN_RxHeaderTypeDef header;
    uint8_t data[8];

    if(can_handle->Instance != CAN1)
        return;

    while(HAL_CAN_GetRxFifoFillLevel(
              can_handle, CAN_RX_FIFO0) != 0U)
    {
if(HAL_CAN_GetRxMessage(can_handle,
                               CAN_RX_FIFO0,
                               &header,
                               data) != HAL_OK)
            break;

        if((header.IDE == CAN_ID_STD) &&
           (header.RTR == CAN_RTR_DATA) &&
           (header.StdId == MOTOR_CAN_ID) &&
           (header.DLC >= 4U))
        {
            motor_rpm_x10 =
                (uint16_t)data[0] |
                ((uint16_t)data[1] << 8);
            motor_sequence = data[2];
            motor_status = data[3];
            motor_last_receive_tick = HAL_GetTick();
            motor_has_received = 1U;
        }
    }
}

MotorCanData_t MotorCanRx_GetData(void)
{
    MotorCanData_t result;
    uint16_t rpm_x10;
    uint8_t sequence;
    uint8_t status;
    uint8_t has_received;
    uint32_t receive_tick;
    uint32_t primask;

    primask = __get_PRIMASK();
    __disable_irq();

    rpm_x10 = motor_rpm_x10;
    sequence = motor_sequence;
    status = motor_status;
    has_received = motor_has_received;
    receive_tick = motor_last_receive_tick;

    if(primask == 0U)
        __enable_irq();

    result.rpm = (float)rpm_x10 / 10.0f;
    result.sequence = sequence;
    result.reverse = ((status & 0x01U) != 0U);
    result.last_receive_tick = receive_tick;
    result.valid =
        (has_received != 0U) &&
        ((status & 0x80U) != 0U) &&
        ((HAL_GetTick() - receive_tick) <= MOTOR_CAN_TIMEOUT_MS);

    return result;
}
