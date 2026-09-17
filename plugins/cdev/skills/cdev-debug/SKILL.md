---
name: cdev-debug
description: Diagnose and then fix a defect in C or Python code. Build a loop that reproduces it, rank hypotheses, prove one, and lock it down with a regression test. Use when the user reports a crash, a hang, a reset loop, corrupted data, a kernel oops, a bugcheck, an intermittent failure, a slowdown, or asks to debug.
---

# cdev-debug

The phases are adapted from `diagnosing-bugs` in [mattpocock/skills](https://github.com/mattpocock/skills) (MIT). The defect record is adapted from `skills/bug-reproduction-brief/SKILL.md` and the stopping rule from `agents/gem-debugger.agent.md`, both in [github/awesome-copilot](https://github.com/github/awesome-copilot) (MIT).

A fix for a defect nobody reproduced is a guess, and a guess usually passes the test and fails later. Most of the work is step 2: once a loop goes red on this defect, the rest is mechanical.

**Shortcut.** When a test already fails with exactly the reported symptom and the cause is plain in the code it exercises, that test is your loop. Go straight to step 5, and tell the user you took the shortcut and why.

**Redact.** Write passwords, keys, and tokens as `<REDACTED>` in anything you show, and quote only the log lines that carry the signal.

## Process

### 1. Record the defect

Before changing anything, write down:

- **Expected**: what should be observable
- **Actual**: what is observed, as the message, the crash, the wrong value, or the timing
- **Build**: commit, compiler or interpreter version, flags, package versions that matter
- **Target**: host OS, board, kernel or Windows build, virtual machine, attached hardware

Keep the suspected cause out of Expected and Actual. Mark anything you only heard second hand as unverified.

**Done when:** all four lines are filled from things you inspected, and every unknown is written as unknown.

### 2. Build a loop that goes red

Find one command that shows this defect. Try these roughly in order, cheapest first:

1. **A unit test** at whatever seam reaches the defect: CTest or Unity for C, pytest for Python.
2. **A CLI run** with a fixture input, its output diffed against a known good one.
3. **A replay**: a captured serial log, packet capture, or input file fed through the code path on the host.
4. **A differential run**: the same input through the last good build and the current one, outputs diffed.
5. **A sanitizer or fuzz loop**: an ASan, UBSan, or TSan build running the trigger, or many generated inputs (libFuzzer, Hypothesis) when the output is only sometimes wrong.
6. **An on-target script**: flash and match the serial reply for firmware; load the driver and run a user-mode test program against it for a driver.
7. **A debugger script**: a GDB batch file, a `cdb -c` command string, or `python -X faulthandler`, printing the state that shows the defect.
8. **A bisect harness**: `git bisect run` with one of the above, when a known good commit exists.
9. **A human in the loop**, last. When someone must press reset, move a cable, or click through a dialog, copy [scripts/hitl_loop.py](scripts/hitl_loop.py) into a folder git ignores (`git check-ignore -v <folder>` confirms it), edit its steps, and ask the user to run it in their own terminal with `--out docs/evidence/F-NNN/hitl-<YYYY-MM-DD>.txt`. Read their answers from that file.

A driver defect that takes the machine down belongs in a virtual machine you can snapshot and restore, with the crash dump as the loop's output: kdump for Linux, a memory dump for Windows.

Then tighten it. Faster: host before target, one test before the suite. Sharper: assert the exact symptom, not "did not crash". Steadier: fixed input, fixed seed, the same machine.

For a defect that shows up only sometimes, aim for a higher reproduction rate rather than a clean run: loop the trigger a hundred times, run it in parallel, add load, narrow the timing window. Half the time is debuggable; one in a hundred is not yet.

When no loop can be built, stop. Tell the user what you tried and ask for one of: access to the setup that shows it, a captured log or crash dump, or permission to add instrumentation to a build they run. Hypothesising without a loop is the failure this skill exists to prevent.

**Done when:** you have run the loop at least once, shown the command and its output, and it is:

- **red on this defect**: it asserts the user's symptom, not a failure that happens nearby
- **repeatable**: the same verdict every run, or a stated high rate for an intermittent defect
- **fast**: seconds, or one deploy and run, rather than a manual session
- **runnable**: by you, or by the user through the loop script

### 3. Shrink it

Cut one thing at a time and rerun the loop: inputs, threads, devices, configuration, steps. Keep only what the failure needs. The shrunken reproduction becomes the regression test in step 5.

Build settings are experiments, not clutter. When the defect vanishes at `-O0`, under the debugger, or with a print added, write that down: it points at undefined behaviour, memory corruption, or timing.

**Done when:** removing any remaining element turns the loop green, and every build-setting experiment is recorded with its result.

### 4. Rank hypotheses, then prove one

Write three to five hypotheses, most likely first, each with the prediction that would falsify it:

> If <cause>, then <change> makes the defect disappear, and <other change> makes it worse.

A hypothesis with no prediction is a hunch: sharpen it or drop it. Show the ranked list to the user before testing, because they often know the recent change or the environment detail that settles it. If they are away, go ahead with your ranking.

Read the `Domains:` line in AGENTS.md, then the `## Debugging anchors` section of each listed domain's reference. They name the failure modes worth putting on the list and the tools that show them: [c](../cdev-implement/references/c.md), [firmware](../cdev-implement/references/firmware.md), [linux-driver](../cdev-implement/references/linux-driver.md), [windows-driver](../cdev-implement/references/windows-driver.md), [python](../cdev-implement/references/python.md).

Test one prediction at a time, changing one variable per run. Prefer, in order:

1. **The debugger**: a breakpoint, a watchpoint on the corrupted value, `pytest --pdb`, WinDbg on the dump.
2. **Tracing built for the job**: RTT or ITM on a microcontroller, ftrace on Linux, WPP on Windows, the `logging` module at DEBUG in Python.
3. **Print lines**, last. A `printf`, `printk`, or `DbgPrint` changes timing and can hide the race you are chasing.

Tag every line you add with one prefix, such as `DEBUG-a4f2`, so cleanup is a single search.

For a slowdown, measure before changing anything: `perf`, `cProfile`, Windows Performance Analyzer, or a cycle counter on a microcontroller. Then bisect. Logs are the wrong tool for timing.

Stop once one hypothesis is confirmed. A check that cannot change the diagnosis is not worth running.

**Done when:** one hypothesis is confirmed by evidence you can show, and the others are ruled out, rather than a change merely appearing to fix it.

### 5. Regression test first, then the fix

Check the seam first. A good seam exercises the defect the way it happens at the real call site. A unit test that cannot reproduce the thread interleaving, or a single-caller test for a defect that needs two callers, gives false confidence.

- **With a good seam**: turn the shrunken reproduction into a test, watch it fail on the defect, make the smallest change that addresses the confirmed cause, and watch it pass.
- **With no seam off the target**: add the check to the feature with `py -3 tools/feature.py set F-NNN --verify "..."` and say so. When the architecture is what rules out a seam, tell the user, because that is a finding in its own right.

Then run the build and test commands from AGENTS.md, and run the step 2 loop again against the original, unshrunk scenario.

**Done when:** the regression test or the recorded verification failed before the fix and passes after it, the original loop is green, and every other test passes.

### 6. Clean up and hand over

- Search for your debug prefix and remove every tagged line.
- Delete the copied loop script and any throwaway harness.
- State the confirmed hypothesis, so `cdev-done` can carry it into the commit message.

**Done when:** the prefix search finds nothing, and you have told the user the root cause in one sentence, the evidence that confirmed it, and where else the same pattern appears in this repository.
