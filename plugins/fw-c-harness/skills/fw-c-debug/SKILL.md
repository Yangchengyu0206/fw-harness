---
name: fw-c-debug
description: Diagnose and then fix a firmware defect. Build a loop that reproduces it, rank hypotheses, prove one, and lock it down with a regression test. Use when the user reports a hang, a reset loop, a HardFault, corrupted data, a peripheral that works intermittently, a missed deadline, or asks to debug embedded C.
---

# fw-c-debug

The phases are adapted from `diagnosing-bugs` in [mattpocock/skills](https://github.com/mattpocock/skills) (MIT). The defect record is adapted from `skills/bug-reproduction-brief/SKILL.md` and the stopping rule from `agents/gem-debugger.agent.md`, both in [github/awesome-copilot](https://github.com/github/awesome-copilot) (MIT). The firmware specifics are this harness's own.

A fix for a defect nobody reproduced is a guess, and on a device the guess usually passes the test and fails in the field. Most of the work is step 2: once a loop goes red on this defect, the rest is mechanical.

**Shortcut.** When a test already fails with exactly the reported symptom and the cause is plain in the code it exercises, that test is your loop. Go straight to step 5, and tell the user you took the shortcut and why.

**Redact.** Write Wi-Fi credentials, device keys, and tokens as `<REDACTED>` in anything you show, and quote only the log lines that carry the signal.

## Process

### 1. Record the defect

Before changing anything, write down:

- **Expected**: what should be observable
- **Actual**: what is observed, as the log line, the fault, the wrong value, or the timing
- **Build**: commit, toolchain version, compiler flags, optimisation level
- **Target**: board and revision, debug probe, attached hardware

Keep the suspected cause out of Expected and Actual. Mark anything you only heard second hand as unverified.

**Done when:** all four lines are filled from things you inspected, and every unknown is written as unknown.

### 2. Build a loop that goes red

Find one command that shows this defect. Try these roughly in order, cheapest first:

1. **A Unity host test** that drives the suspect module through the failing input.
2. **A replay**: a captured UART, CAN, or sensor trace fed through the parser or state machine on the host.
3. **A differential run**: the same input through the last good build and the current one, outputs diffed.
4. **A serial script**: flash, send the trigger over the serial port, match the reply against the expected line.
5. **A debugger script**: a GDB batch file against OpenOCD or J-Link that runs to a breakpoint and prints the registers or variables that show the defect.
6. **A bisect harness**: `git bisect run` with one of the above, when a known good commit exists.
7. **A human in the loop**, last. When someone must press reset or move a cable, copy [scripts/hitl_loop.py](scripts/hitl_loop.py) into `build/debug/`, edit its steps, and ask the user to run it in their own terminal with `--out harness/evidence/FW-NNNN/hitl-<YYYY-MM-DD>.txt`. Read their answers from that file.

Then tighten it. Faster: host before board, one test before the suite. Sharper: assert the exact symptom, not "did not crash". Steadier: fixed input, fixed seed, the same board.

For a defect that shows up only sometimes, aim for a higher reproduction rate rather than a clean run: loop the trigger a hundred times, raise the interrupt rate, load the bus, narrow the timing window. Half the time is debuggable; one in a hundred is not yet.

When no loop can be built, stop. Tell the user what you tried and ask for one of: access to the setup that shows it, a captured log or fault register dump, or permission to add instrumentation to a build they run. Hypothesising without a loop is the failure this skill exists to prevent.

**Done when:** you have run the loop at least once, shown the command and its output, and it is:

- **red on this defect**: it asserts the user's symptom, not a failure that happens nearby
- **repeatable**: the same verdict every run, or a stated high rate for an intermittent defect
- **fast**: seconds, or one flash and run, rather than a manual session
- **runnable**: by you, or by the user through the loop script

### 3. Shrink it

Cut one thing at a time and rerun the loop: inputs, tasks, peripherals, configuration, steps. Keep only what the failure needs. The shrunken reproduction becomes the regression test in step 5.

Build settings are experiments, not clutter. When the defect vanishes at `-O0`, with the debugger attached, or with a log line added, write that down: it points at undefined behaviour, a missing `volatile`, or timing.

**Done when:** removing any remaining element turns the loop green, and every build-setting experiment is recorded with its result.

### 4. Rank hypotheses, then prove one

Write three to five hypotheses, most likely first, each with the prediction that would falsify it:

> If <cause>, then <change> makes the defect disappear, and <other change> makes it worse.

A hypothesis with no prediction is a hunch: sharpen it or drop it. Show the ranked list to the user before testing, because they often know the board revision or the recent change that settles it. If they are away, go ahead with your ranking.

Firmware anchors worth putting on the list:

- **HardFault**: decode the stacked frame. The stacked PC is the faulting instruction and the stacked LR is where it came from. `CFSR` says which fault fired, and `BFAR` or `MMFAR` holds the address when its valid bit is set. An imprecise bus fault points somewhere after the real culprit.
- **Stack overflow**: paint the stack with a known pattern at startup and read how far it was consumed. A corrupted variable next to a task stack is this until proven otherwise.
- **An interrupt race**: state shared with a handler and no protection, or a missing `volatile`. Read [isr-concurrency.md](../fw-c-implement/isr-concurrency.md).
- **A watchdog reset** is a symptom. Find what stopped feeding it: a loop that never exits, a blocked task, or a handler storm.
- **It appeared recently**: `git bisect run` with the shrunken reproduction as the test.

Test one prediction at a time, changing one variable per run. Prefer, in order:

1. **The debugger**: a breakpoint, a watchpoint on the corrupted variable, the fault registers.
2. **Tracing that barely moves timing**: RTT, ITM or SWO, or a ring buffer read afterwards.
3. **Log lines**, last. A `printf` over UART changes timing and can hide the race you are chasing.

Tag every line you add with one prefix, such as `DEBUG-a4f2`, so cleanup is a single search.

For a slowdown or a missed deadline, measure before changing anything: `DWT_CYCCNT`, or a GPIO toggled around the section and watched on a logic analyser. Then bisect. Logs are the wrong tool for timing.

Stop once one hypothesis is confirmed. A check that cannot change the diagnosis is not worth a flash cycle.

**Done when:** one hypothesis is confirmed by evidence you can show, and the others are ruled out, rather than a change merely appearing to fix it.

### 5. Regression test first, then the fix

Check the seam first. A good seam exercises the defect the way it happens at the real call site. A host test that cannot reproduce the interrupt ordering, or a single-caller test for a defect that needs two callers, gives false confidence.

- **With a good seam**: turn the shrunken reproduction into a Unity test, watch it fail on the defect, make the smallest change that addresses the confirmed cause, and watch it pass.
- **With no seam on the host**: add the board check to the ticket's `verification_steps` and say so. When the architecture is what rules out a seam, tell the user, because that is a finding in its own right.

Then run the gates, and run the step 2 loop again against the original, unshrunk scenario:

```bash
py -3 harness/scripts/check.py
```

**Done when:** the regression test or the recorded board step failed before the fix and passes after it, the original loop is green, and every gate passes.

### 6. Clean up and hand over

- Search for your debug prefix and remove every tagged line.
- Delete the copies in `build/debug/` and any throwaway harness.
- State the confirmed hypothesis, so `fw-done` can carry it into the commit message.

**Done when:** the prefix search finds nothing, and you have told the user the root cause in one sentence, the evidence that confirmed it, and where else the same pattern appears in this repository.
