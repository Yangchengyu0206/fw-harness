---
name: cdev-debug
description: Reproduce and then fix a defect in C or Python code. Use when the user reports a crash, a hang, a reset loop, corrupted data, a kernel oops, a bugcheck, an intermittent failure, or asks to debug.
---

# cdev-debug

Adapted from `agents/debug.agent.md` in [github/awesome-copilot](https://github.com/github/awesome-copilot) (MIT).

Reproduce before fixing. A fix for a defect you have not reproduced is a guess, and a guess usually survives the test and fails later.

## Process

### 1. Reproduce

Get the defect to happen on demand: the exact build, the exact steps, and the output it produces. When real hardware or a real operating system is involved, capture the log into `docs/evidence/`.

**Done when:** you can name one command or one sequence that shows the defect, and you have run it at least once and shown its output.

### 2. Shrink the reproduction

Remove everything not needed to make it happen: inputs, devices, threads, the optimisation level. Keep removing until every remaining element is load bearing.

**Done when:** removing any remaining element makes the defect disappear.

### 3. Test one hypothesis at a time

Read the `Domains:` line in AGENTS.md, then the `## Debugging anchors` section of each listed domain's reference. They name the failure modes worth ruling in or out first, and the tools that show them: [c](../cdev-implement/references/c.md), [firmware](../cdev-implement/references/firmware.md), [linux-driver](../cdev-implement/references/linux-driver.md), [windows-driver](../cdev-implement/references/windows-driver.md), [python](../cdev-implement/references/python.md).

When the defect appeared recently, `git bisect run` with the shrunken reproduction as the test finds the commit faster than reading does.

**Done when:** one hypothesis is confirmed by evidence you can show, rather than by a change appearing to fix it.

### 4. Write the regression test first

Add a test that fails for this defect. When the defect needs real hardware or a real operating system, add the check to the feature's `verification` with `py -3 tools/feature.py set F-NNN --verify "..."` and say so.

**Done when:** the test fails, and its failure is the defect.

### 5. Fix and verify

Make the smallest change that addresses the cause you confirmed, then run the build and test commands from AGENTS.md.

**Done when:** the regression test passes, every other test passes, and you have told the user the root cause in one sentence plus where else the same pattern appears in this repository.
