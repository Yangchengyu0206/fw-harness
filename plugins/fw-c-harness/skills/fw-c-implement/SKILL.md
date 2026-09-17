---
name: fw-c-implement
description: "Implement a firmware ticket in C, test first, inside the module's approved layering. Use when the user asks to implement a ticket, write or extend a driver, add a module, or change embedded C behaviour."
---

# fw-c-implement

Write the test before the code, keep the module inside its approved dependencies, and finish with evidence rather than a claim.

Read [embedded-c-rules.md](embedded-c-rules.md) before writing any C here. Read [isr-concurrency.md](isr-concurrency.md) when the change touches an interrupt handler or state a handler reaches. Read [memory-budget.md](memory-budget.md) when the change adds a buffer, a task stack, or an allocation. Read [module-template.md](module-template.md) when you are creating a module rather than editing one.

## Process

### 1. Read the ticket and the module

Read the ticket with `py -3 harness/scripts/ticket.py show FW-NNNN`, and the ARCHITECTURE.md of every folder you are about to touch. The approved dependencies in those documents are the layering you work inside.

**Done when:** you can state the ticket's `user_visible_behavior` in one sentence, list its `verification_steps`, and name which module owns the change and what it may include.

### 2. Write the failing test

Add a Unity test under `test/` that fails for the reason the ticket exists, and run it:

```bash
py -3 harness/scripts/check.py
```

A test that passes before the code is written proves nothing, so read the failure and confirm it is the one you intended.

**Done when:** the run fails, and the failure names the behaviour the ticket asked for.

### 3. Implement

Write the smallest change that makes the test pass. Add every new `.c` file to the CMake target as well as to disk.

**Done when:** the new test passes and no existing test changed its expectations to accommodate the new code.

### 4. Run every gate

```bash
py -3 harness/scripts/check.py
```

Fix what it reports. A new include that crosses a layer is a design question, so take it to the user rather than adding a grandfather entry.

**Done when:** all seven steps pass.

### 5. Record the evidence

On a clean working tree:

```bash
py -3 harness/scripts/check.py --record FW-NNNN
```

**Done when:** the ticket carries a `check` entry for this commit, and you have told the user what it still owes: board verification when `requires_hil` is true, and a review by someone else.
