---
name: cdev-test-gap
description: "Audit which behaviour in this C or Python code has no test, ranked P0 to P3, read-only. Use when the user asks what is untested, whether coverage is enough, what regression test a fix needs, or how to prove a change is safe."
---

# cdev-test-gap

Adapted from `skills/test-gap-audit/SKILL.md` in [github/awesome-copilot](https://github.com/github/awesome-copilot) (MIT), narrowed to C and Python and to this harness.

Read-only. Add tests only when the user asks, and then through `cdev-implement`.

## Scope

When the user names a feature, a folder, or a branch, audit that and the code paths it reaches. When they name nothing, audit every editable folder listed in AGENTS.md, breadth first, and say which ones you inspected deeply and which you only surveyed.

## Evidence standards

These are what make the report trustworthy:

- **The line you cite literally contains the thing you name.** Citing a function means citing the line its name is on, not the line above it and not a line inside its body.
- **Every number appears next to the command that produced it**, under Checks Run. A count with no visible command behind it is the easiest claim to get wrong, so show the command or describe the pattern instead.
- **A negative claim needs more than one search.** Before reporting that nothing tests a function, search the tests for the module name, the function name, and the behaviour's wording.
- Separate what you confirmed from what you inferred, and give an inferred gap a confidence rating.

## What to look for

- Error paths: the allocation that fails, the device that times out, the file that is missing, the process that exits non-zero.
- Boundary values on every parsed length, index, and count.
- Illegal state transitions, not only the happy path.
- A fixed bug with no regression test.
- Behaviour only real hardware or a real operating system can show: an interrupt, a driver load, a board-level timing. That belongs in the feature's `verification` list, not in a host test that cannot prove it. Say so.

The Review checklist section of each active domain's reference names the failures that matter most in that domain, and they are the first places to look for missing tests: [c](../cdev-implement/references/c.md), [firmware](../cdev-implement/references/firmware.md), [linux-driver](../cdev-implement/references/linux-driver.md), [windows-driver](../cdev-implement/references/windows-driver.md), [python](../cdev-implement/references/python.md).

## Severity

- `P0`: untested code whose failure corrupts data, crashes the system, bricks a device, or drives hardware unsafely.
- `P1`: an untested common path, error return, or interface other code depends on.
- `P2`: an untested edge case, validation, or state transition, or a test whose assertions do not prove what its name claims.
- `P3`: naming drift, redundant tests, fixture cleanup.

## Report

```markdown
**Test gap audit: <scope>**

No code changed. I reviewed <scope>, the existing tests, and the features' verification lists.

1. **P1: <gap title>.**
   Gap: <behaviour not covered>
   Current coverage: <what exists, or where you looked and found nothing>
   Evidence: code `src/drivers/uart.c:142`; tests: no direct test found in `test/`
   Suggested test: <file, name, and the assertions that would prove it>

**Checks Run**
- `<command>`: <result>

**Needs real hardware or a real OS**
- <behaviour, and the feature verification step that covers it>
```

**Done when:** every gap carries a `path:line` you re-read, every number has its command beside it, and behaviour only real hardware or a real OS can show is named rather than turned into a host test.
