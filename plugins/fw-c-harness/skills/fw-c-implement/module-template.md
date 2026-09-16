# New module skeleton

Adapted from `agents/expert-embedded-c-engineer.agent.md` in [github/awesome-copilot](https://github.com/github/awesome-copilot) (MIT).

Read this when you are creating a module rather than editing one. A new folder of C sources also needs an entry in `harness/architecture.json` and an ARCHITECTURE.md, which `fw-architecture-sync` drafts.

## Header

```c
#ifndef UART_H
#define UART_H

#include <stdbool.h>
#include <stdint.h>

/* Status returned by every uart function that can fail. */
typedef enum {
    UART_OK = 0,
    UART_ERR_PARAM,
    UART_ERR_BUSY,
    UART_ERR_TIMEOUT
} uart_status_t;

/* Initialise the peripheral. Call once, before any other uart function. */
uart_status_t uart_init(uint32_t baud);

/* Queue len bytes for transmission. Returns UART_ERR_BUSY when the queue is full. */
uart_status_t uart_write(const uint8_t *data, uint16_t len);

#endif /* UART_H */
```

## Source

```c
#include "uart.h"

#include "hal_gpio.h"

#define UART_TX_BUFFER_LEN 256U

static uint8_t tx_buffer[UART_TX_BUFFER_LEN];
static volatile uint16_t tx_head; /* written by the ISR */
static uint16_t tx_tail;          /* written by the main loop */

static bool is_initialised(void);

uart_status_t uart_init(uint32_t baud)
{
    if (baud == 0U) {
        return UART_ERR_PARAM;
    }
    /* ... */
    return UART_OK;
}
```

## The checklist for a new module

- An include guard named after the file, one status enum for the module, and every exported function documented with what it returns when it fails.
- Everything not exported is `static`.
- The `.c` file is added to the CMake target.
- The module's includes stay inside the dependencies its ARCHITECTURE.md approves.
- A Unity test exists for the behaviour the ticket asked for, and it failed before the module existed.
