# Firmware

Applies to bare-metal and RTOS code on a microcontroller.

Adapted from `agents/expert-embedded-c-engineer.agent.md` in [github/awesome-copilot](https://github.com/github/awesome-copilot) (MIT) and from the references in the fw-c-harness plugin of this repository. The rules in `c.md` apply as well; where the two disagree, this file wins.

## Rules

### Types, scope, and errors

- Fixed-width integer types (`uint8_t`, `int16_t`, `uint32_t`) wherever a value's width matters, which in firmware is nearly everywhere.
- The narrowest scope that works: `static` at file scope for anything the module does not export.
- `const` on pointers to read-only data, on parameters the function does not modify, and on lookup tables, so they land in flash rather than RAM.
- An `enum` over a group of related `#define` constants, because a debugger can show an enum's name.
- Every function that can fail returns a status, and every status is checked. Validate inputs at the module boundary, meaning the functions the header exports, and trust them inside.
- Wrap every macro parameter in parentheses, and a multi-statement macro in `do { ... } while (0)`.
- Leave generated code, vendor code, linker scripts, startup files, and compiler flags alone. Their ARCHITECTURE.md says where they come from.

### Interrupts and shared state

- A variable written by an interrupt handler and read elsewhere is `volatile`, and so is every hardware register. Without it the compiler may keep a stale copy in a register.
- `volatile` orders nothing and makes nothing atomic. A value wider than the core's atomic word is read and written inside a critical section, or a reader can see half of the old value and half of the new one.
- Keep a critical section to the shortest sequence that must not be interrupted: copy the shared value out, then work on the copy.
- A single-producer, single-consumer ring buffer with one index owned by the handler and the other by the main loop needs no critical section. Write in a comment which side owns which index, because the design is safe only while that stays true.
- A handler sets a flag or pushes to a queue and returns. Blocking calls, waits on another peripheral, allocation, and long work belong in the main loop or a task.

### Memory

- Static allocation with a fixed bound. A statically sized pool shows up in the size report; a heap does not.
- If the project allows dynamic allocation at all, allocate during startup and never in a loop or a handler. Fragmentation on a device that runs for months reproduces only in the field.
- Size every buffer from the protocol or the hardware, and write the reason in a comment beside it.
- No recursion: its stack depth has no bound you can compute.
- Large locals live on the stack. Move them into a static buffer the module owns, or take them from the caller.
- Record each task's stack need in the folder's ARCHITECTURE.md, and check flash (`text + data`) and RAM (`data + bss`) with the size tool after each change.

### MISRA C:2012

- A reference standard, advisory unless AGENTS.md says the project requires it.
- Cite a rule with its classification: `Rule 10.4 (required)`, `Rule 15.5 (advisory)`.
- When a required rule cannot be met, first show the compliant alternative and what it costs. If the deviation stays, write `docs/deviations/DEV-NNNN.md` holding the rule, why it cannot be met here, the risk, the exact files or lines it covers, what limits the risk, and the date and name of the decision. Reference `DEV-NNNN` in a comment where the deviation lives.

## Review checklist

### Critical

- undefined behaviour, including signed overflow, misaligned access, and use after free
- an array or pointer access that can leave its object
- an integer overflow or truncation that changes the result
- state shared between an interrupt handler and the main loop without protection
- a missing `volatile` on a register or on state a handler writes
- an ignored error return code
- an external length or index used without validation
- a debug port left open, or a key or password in the source
- an include that crosses the dependencies the folder's ARCHITECTURE.md describes

### Important

- new logic with no test
- a resource acquired and not released on every path
- a blocking call on a time-critical path
- a magic number standing in for a register address or a timeout
- a required MISRA rule broken with no deviation record, when AGENTS.md makes MISRA required

### Suggestion

- naming that does not match the module it lives in
- a comment that explains what the code does instead of why
- deep nesting, or a function doing several jobs
- a MISRA advisory rule, while MISRA is advisory

## Debugging anchors

- **HardFault** (Cortex-M): decode the stacked frame. The stacked PC is the faulting instruction and the stacked LR is where it came from. `CFSR` says which fault fired; `BFAR` or `MMFAR` holds the faulting address when its valid bit in `CFSR` is set. An imprecise bus fault points somewhere after the real culprit.
- **Stack overflow**: fill each stack with a known pattern at startup and read how far the pattern was consumed. A variable corrupted next to a task stack is this until proven otherwise. Most RTOSes offer a high-water-mark call.
- **An interrupt race**: state shared with a handler and no protection, or a missing `volatile`. The symptom is a value that is right almost every time.
- **A watchdog reset** is a symptom. Find what stopped feeding it: a loop that never exits, a blocked task, or a handler storm.
- **Works in debug, fails in release**: optimisation exposing undefined behaviour or a missing `volatile`, far more often than a compiler bug.
- **It appeared recently**: `git bisect` with the shrunken reproduction on the board as the test.

## Build and test

Use the commands in AGENTS.md when the repository records them. Otherwise, the usual shapes are:

- Cross build: CMake with an `arm-none-eabi` toolchain file, `cmake --preset <target>` then `cmake --build --preset <target>`
- Host tests: logic that does not touch hardware, built for the host and run with Unity
- Size: `arm-none-eabi-size build/<target>/<image>.elf`
- Flash and serial: the probe and terminal the project uses (for example `openocd`, `pyocd`, `JLinkExe`, and a serial terminal at the project's baud rate)
- Logs from real hardware go under `docs/evidence/`, named after the feature and the step
