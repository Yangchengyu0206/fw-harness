# Memory budget

Adapted from `agents/expert-embedded-c-engineer.agent.md` in [github/awesome-copilot](https://github.com/github/awesome-copilot) (MIT).

Read this when the change adds a buffer, a task stack, or an allocation.

## The budget is a gate

`check` runs the size tool on the ELF and compares the result with `flash_budget` and `ram_budget` in `harness/config.json`. Flash is `text + data`; RAM is `data + bss`. Exceeding either fails the run, so a large static buffer becomes a build failure instead of a surprise months later.

Run it before you commit:

```bash
py -3 harness/scripts/check.py
```

The size step prints the current numbers against the budget, so you can see what your change cost.

## Allocation

- Prefer static allocation with a fixed bound. A statically sized pool is visible in the size report; a heap is not.
- Where the team allows dynamic allocation at all, allocate during startup and keep it out of loops and handlers. Fragmentation on a device that runs for months is a fault that reproduces only in the field.
- Size every buffer from the protocol or the hardware rather than from a round number, and write the reason in a comment beside it.

## Stack

- A recursive function has no bound you can compute, so the bound becomes a runtime crash. Write it as a loop.
- Large locals live on the stack. Move anything sizeable into a static buffer owned by the module, or take it from the caller as a parameter.
- Record the stack a task needs in its ARCHITECTURE.md under the ISR and memory notes, so the next person sizing that task has your number.
