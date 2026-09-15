#include "unity.h"
#include "uart.h"
#include "../src/app/app_config.h"

void test_uart_init_returns_gpio_count(void)
{
    TEST_ASSERT_EQUAL_INT(APP_GPIO_COUNT, uart_init());
}
