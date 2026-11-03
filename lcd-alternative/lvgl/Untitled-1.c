/*
 * @Author: error: error: git config user.name & please set dead value or install git && error: git config user.email & please set dead value or install git & please set dead value or install git
 * @Date: 2026-08-25 16:13:52
 * @LastEditors: error: error: git config user.name & please set dead value or install git && error: git config user.email & please set dead value or install git & please set dead value or install git
 * @LastEditTime: 2026-09-03 13:45:23
 * @FilePath: \undefinedd:\aiguigu\STM32F407\42_lcd_hal\lvgl\Untitled-1.c
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
 */
#include <stdint.h>
#include <stdio.h>

// 实习生定义的单字节状态机
typedef enum { STATE_HEAD1, STATE_HEAD2, STATE_LEN, STATE_PAYLOAD, STATE_CS } rx_state_t;

rx_state_t state = STATE_HEAD1;
uint8_t payload_buf[256];
uint8_t expected_len = 0;
uint8_t payload_idx = 0;

void uart_rx_byte_handler(uint8_t byte) {
    switch (state) {
        case STATE_HEAD1:
            if (byte == 0xAA) state = STATE_HEAD2;
            break;
            
        case STATE_HEAD2:
            if (byte == 0x55) state = STATE_LEN;
            else if (byte == 0xAA) state = STATE_HEAD2; // 如果连续收到0xAA，保持在STATE_HEAD2
            else state = STATE_HEAD1; 
            break;
            
        case STATE_LEN:
        if (byte == 0 || byte > 255)
        {
            state = STATE_HEAD1; // 无效长度
            break;
        }
        
            expected_len = byte;
            payload_idx = 0;
            state = STATE_PAYLOAD;
            break;
            
        case STATE_PAYLOAD:
              if (byte == 0xAA) {
                // 检测到新帧头，直接丢弃当前半包，跳转HEAD2重新同步
                state = STATE_HEAD2;
                payload_idx = 0;
                return;
            }
            payload_buf[payload_idx++] = byte;
            if (payload_idx == expected_len) state = STATE_CS;
            break;
            
        case STATE_CS:
            uint8_t cs = expected_len;
            for (int i = 0; i < expected_len; i++) {
                cs += payload_buf[i];
            }
            printf("Payload len: %d\n", expected_len);
            if (cs == byte) {
                // 校验通过，处理业务
                printf("Valid frame received!\n");
                printf("Payload: ");
                for (int i = 0; i < expected_len; i++) {
                    printf("0x%02X ", payload_buf[i]);
                }
            }
            // 无论校验对错，状态机强行复位
            state = STATE_HEAD1;
            break;
    }
}


int main(){
    uint8_t test_data[] ={0xAA, 0xAA, 0x55, 0x05, 0x01, 0x41, 0x01, 0x2C, 0x02, 0x76}; // Example frame with checksum
    for(int i=0; i<sizeof(test_data); i++){
        printf("Feed byte[%d]: 0x%02X\n", i, test_data[i]);
        uart_rx_byte_handler(test_data[i]);
    }
      uint8_t test_b[] = {0xAA, 0x55, 0x05, 0x01, 0xAA, 0x55, 0x05, 0x01, 0x41, 0x01, 0x2C, 0x02, 0x76};
    for(int i=0; i<sizeof(test_b); i++){
        printf("Feed byte[%d]: 0x%02X\n", i, test_b[i]);
        uart_rx_byte_handler(test_b[i]);
    }
    


}