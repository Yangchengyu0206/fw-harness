---
name: cdev-debug
description: Diagnose and then fix a defect in C or Python code. Build a loop that reproduces it, rank hypotheses, prove one, and lock the fix down. Use when the user reports a crash, a hang, a reset loop, corrupted data, a kernel oops, a bugcheck, an intermittent failure, a slowdown, or asks to debug.
---

# cdev-debug

The phases are adapted from `diagnosing-bugs` in [mattpocock/skills](https://github.com/mattpocock/skills) (MIT). The defect record is adapted from `skills/bug-reproduction-brief/SKILL.md` and the stopping rule from `agents/gem-debugger.agent.md`, both in [github/awesome-copilot](https://github.com/github/awesome-copilot) (MIT). The comparison with working code, the trace back to the source, and the three-fix limit are adapted from `skills/systematic-debugging` in [obra/superpowers](https://github.com/obra/superpowers) (MIT).

A fix for a defect nobody reproduced is a guess, and a guess usually passes the test and fails later. Most of the work is step 2: once a loop goes red on this defect, the rest is mechanical.

**Shortcut.** Not every defect needs every step. When one run on the reported input already shows exactly the symptom, and the cause is plain in the code it exercises, that run is your loop: go straight to step 5, and tell the user you took the shortcut and why. Take the full path when the first fix does not turn the run green.

**Redact.** Write passwords, keys, and tokens as `<REDACTED>` in anything you show, and quote only the log lines that carry the signal.

## Process

### 1. Record the defect

Before changing anything, write down:

- **Expected**: what should be observable
- **Actual**: what is observed, as the message, the crash, the wrong value, or the timing
- **Input**: the data, arguments, or steps that trigger it
- **Environment**, only the parts that could matter: commit, compiler or interpreter version, flags, and for hardware or drivers the board, kernel, or Windows build

Keep the suspected cause out of Expected and Actual. Mark anything you only heard second hand as unverified.

**Done when:** the lines are filled from things you inspected, and every unknown is written as unknown.

### 2. Build a loop that goes red

Find one command that shows this defect. Try these roughly in order, cheapest first:

1. **A scratch script** that calls the suspect function or program on the failing input and compares the output with the expected one, within a tolerance for floating point. For algorithm code this is usually the whole loop. Keep it in a folder git ignores (`git check-ignore -v <folder>` confirms it).
2. **A unit test** at whatever seam reaches the defect, when the repository has tests: CTest or Unity for C, pytest for Python.
3. **A replay**: a captured data file, serial log, or packet capture fed through the code path on the host.
4. **A differential run**: the same input through the last good build and the current one, outputs diffed.
5. **A sanitizer or fuzz loop**: an ASan, UBSan, or TSan build running the trigger, or many generated inputs (libFuzzer, Hypothesis) when the output is only sometimes wrong.
6. **An on-target script**: flash and match the serial reply for firmware; load the driver and run a user-mode test program against it for a driver.
7. **A debugger script**: a GDB batch file, a `cdb -c` command string, or `python -X faulthandler`, printing the state that shows the defect.
8. **A bisect harness**: `git bisect run` with one of the above, when a known good commit exists.
9. **A human in the loop**, last. When someone must press reset, move a cable, or click through a dialog, copy [scripts/hitl_loop.py](scripts/hitl_loop.py) into a folder git ignores, edit its steps, and ask the user to run it in their own terminal with `--out docs/evidence/F-NNN/hitl-<YYYY-MM-DD>.txt`. Read their answers from that file.

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

**Compare with code that works.** Find the closest thing that does work: the same driver on another port, the same routine before the regression, or, for an algorithm, the reference implementation it was ported from, such as a MATLAB or NumPy version, run on the same input with intermediate values printed side by side. List every difference between the two, however small, before deciding one cannot matter. The differences are the first hypotheses.

Write three to five hypotheses, most likely first, each with the prediction that would falsify it:

> If <cause>, then <change> makes the defect disappear, and <other change> makes it worse.

A hypothesis with no prediction is a hunch: sharpen it or drop it. Show the ranked list to the user and start testing the first one without waiting; they often know the recent change or the input detail that settles it, and can interrupt when they do.

Read the `Domains:` line in AGENTS.md, then the `## Debugging anchors` section of each listed domain's reference. They name the failure modes worth putting on the list and the tools that show them: [c](../cdev-implement/references/c.md), [firmware](../cdev-implement/references/firmware.md), [linux-driver](../cdev-implement/references/linux-driver.md), [windows-driver](../cdev-implement/references/windows-driver.md), [python](../cdev-implement/references/python.md).

Test one prediction at a time, changing one variable per run. Prefer, in order:

1. **The debugger**: a breakpoint, a watchpoint on the corrupted value, `pytest --pdb`, WinDbg on the dump.
2. **Tracing built for the job**: RTT or ITM on a microcontroller, ftrace on Linux, WPP on Windows, the `logging` module at DEBUG in Python.
3. **Print lines**, last. A `printf`, `printk`, or `DbgPrint` changes timing and can hide the race you are chasing.

Tag every line you add with one prefix, such as `DEBUG-a4f2`, so cleanup is a single search.

For a slowdown, measure before changing anything: `perf`, `cProfile`, Windows Performance Analyzer, or a cycle counter on a microcontroller. Then bisect. Logs are the wrong tool for timing.

Stop once one hypothesis is confirmed. A check that cannot change the diagnosis is not worth running.

**Done when:** one hypothesis is confirmed by evidence you can show, and the others are ruled out, rather than a change merely appearing to fix it.

### 5. Lock it down, then fix

Check the seam first. A good seam exercises the defect the way it happens at the real call site. A unit test that cannot reproduce the thread interleaving, or a single-caller test for a defect that needs two callers, gives false confidence.

Fix where the fault starts, not where it shows. When a bad value surfaces deep in a call chain, follow it backwards, caller by caller, to the first place it goes wrong, and change that place. A guard added at the symptom hides the defect from the next caller.

- **With `Test: none` in AGENTS.md**: add no test framework. Make the smallest change that addresses the confirmed cause and watch the shrunken loop turn green. Then ask the user whether to keep the loop script in the repository as a check for this defect, or delete it.
- **With a good seam**: turn the shrunken reproduction into a test, watch it fail on the defect, make the smallest change that addresses the confirmed cause, and watch it pass.
- **With no seam off the target**: add the check to the feature with `py -3 tools/feature.py set F-NNN --verify "..."` and say so. When the architecture is what rules out a seam, tell the user, because that is a finding in its own right.

When the fix does not turn the loop green, revert it rather than stacking another change on top, and go back to step 4 with what it taught you. After three fixes that did not hold, stop and talk it through with the user before a fourth. When each fix exposes a new problem somewhere else, the design around the defect is the likely cause, and patching symptoms will not converge.

Then run the build command from AGENTS.md, the test command when there is one, and the step 2 loop again against the original, unshrunk scenario.

**Done when:** the loop, the regression test, or the recorded verification was red before the fix and is green after it, on the original scenario as well, and every other test passes where there are tests.

### 6. Clean up and hand over

- Search for your debug prefix and remove every tagged line.
- Delete the loop script and any throwaway harness, unless the user chose to keep one.
- State the confirmed hypothesis, so `cdev-done` can carry it into the commit message.

**Done when:** the prefix search finds nothing, and you have told the user the root cause in one sentence, the evidence that confirmed it, and where else the same pattern appears in this repository.
