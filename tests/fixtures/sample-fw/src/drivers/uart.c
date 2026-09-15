#include "uart.h"
#include "hal_gpio.h"

int uart_init(void)
{
    return hal_gpio_init();
}
