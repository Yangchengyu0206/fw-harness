---
name: fw-c-test-gap
description: "Audit which behaviour in this firmware has no test, ranked P0 to P3, read-only. Use when the user asks what is untested, whether coverage is enough, what regression test a fix needs, or how to prove a change is safe."
---

# fw-c-test-gap

Adapted from `skills/test-gap-audit/SKILL.md` in [github/awesome-copilot](https://github.com/github/awesome-copilot) (MIT), narrowed to C firmware and to this harness.

Read-only. Add tests only when the user asks, and then through `fw-c-implement`.

## Scope

When the user names a ticket, a module, or a branch, audit that and the code paths it reaches. When they name nothing, audit the modules marked `owned` in `harness/architecture.json`, breadth first, and say which ones you inspected deeply and which you only surveyed.

## Evidence standards

These are what make the report trustworthy:

- **The line you cite literally contains the thing you name.** Citing a function means citing the line its name is on, not the line above it and not a line inside its body.
- **Every number appears next to the command that produced it**, under Checks Run. A count with no visible command behind it is the easiest claim to get wrong, so evidence it or describe the pattern instead.
- **A negative claim needs more than one search.** Before reporting that nothing tests a function, search the test folder for the module name, for the header name, and for the behaviour's wording.
- Separate what you confirmed from what you inferred, and give an inferred gap a confidence rating.

## What to look for in firmware

- A driver's error paths: the peripheral timing out, the bus reporting an error, the buffer filling up.
- Boundary values on every parsed length, index, and count.
- The state machine's illegal transitions, not only its happy path.
- Behaviour only the board can show, which belongs in the ticket's `verification_steps`. Say so rather than proposing a host test that cannot prove it.
- A fixed bug with no regression test.

## Severity

- `P0`: untested code whose failure corrupts data, bricks the device, or drives an output unsafely.
- `P1`: untested common path, error return, or interface contract another module depends on.
- `P2`: untested edge case, validation, or state transition, or a test whose assertions do not prove what its name claims.
- `P3`: naming drift, redundant tests, fixture cleanup.

## Report

```markdown
**Test gap audit: <scope>**

No code changed. I reviewed <scope>, the existing tests under test/, and the ticket's verification steps.

1. **P1: <gap title>.**
   Gap: <behaviour not covered>
   Current coverage: <what exists, or where you looked and found nothing>
   Evidence: code `src/drivers/uart.c:142`; tests: no direct test found in `test/`
   Suggested test: <file, name, and the assertions that would prove it>

**Checks Run**
- `<command>`: <result>

**Not tested here**
- <what needs the board, and which verification step covers it>
```

**Done when:** every gap carries a `path:line` you re-read, every number has its command beside it, and board-only behaviour is named rather than quietly turned into a host test.
