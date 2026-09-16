---
name: fw-c-debug
description: Reproduce and then fix a firmware defect. Use when the user reports a hang, a reset loop, a HardFault, corrupted data, a peripheral that works intermittently, or asks to debug embedded C.
---

# fw-c-debug

Adapted from `agents/debug.agent.md` in [github/awesome-copilot](https://github.com/github/awesome-copilot) (MIT), with the firmware specifics this harness needs.

Reproduce before fixing. A fix for a defect you have not reproduced is a guess, and on a device the guess usually survives the test and fails in the field.

## Process

### 1. Reproduce

Get the defect to happen on demand: the exact build, the exact steps, and the output it produces. Capture the serial log or the debugger state into `harness/evidence/FW-NNNN/` when a board is involved.

**Done when:** you can name one command or one sequence on the board that shows the defect, and you have run it at least once and shown its output.

### 2. Shrink the reproduction

Remove everything not needed to make it happen: peripherals, tasks, inputs, the optimisation level. Keep removing until every remaining element is load bearing.

**Done when:** removing any remaining element makes the defect disappear.

### 3. Test one hypothesis at a time

Firmware anchors worth ruling in or out early:

- **HardFault**: decode the stacked registers. The stacked PC is the faulting instruction and the stacked LR is where it came from. `CFSR` says which fault fired, and `BFAR` or `MMFAR` holds the address when its valid bit is set.
- **Stack overflow**: paint the stack with a known pattern at startup and read how far it was consumed. A corrupted variable next to a task stack is this until proven otherwise.
- **An interrupt race**: state shared with a handler and no protection, or a missing `volatile`. Read [isr-concurrency.md](../fw-c-implement/isr-concurrency.md).
- **It appeared recently**: `git bisect`, with the shrunken reproduction as the test.

**Done when:** one hypothesis is confirmed by evidence you can show, rather than by the fix appearing to work.

### 4. Write the regression test first

Add a Unity test that fails for this defect. When the defect needs the board, add the check to the ticket's `verification_steps` instead and say so.

**Done when:** the test fails, and its failure is the defect.

### 5. Fix and verify

Make the smallest change that addresses the cause you confirmed, then:

```bash
py -3 harness/scripts/check.py
```

**Done when:** the regression test passes, every other gate passes, and you have told the user the root cause in one sentence plus where else the same pattern appears in this repository.
