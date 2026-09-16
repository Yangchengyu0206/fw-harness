---
name: fw-misra-deviation
description: Record a MISRA deviation in docs/deviations when a rule cannot be met. Use when the user says a MISRA rule must be broken, when a review finds a required-rule violation the code needs to keep, or when someone asks how to document a deviation.
---

# fw-misra-deviation

Adapted from the deviation guidance in `agents/expert-embedded-c-engineer.agent.md` in [github/awesome-copilot](https://github.com/github/awesome-copilot) (MIT).

A deviation is a decision with a name on it, not a suppression. Writing it down is how the next reader learns why the rule was broken here and what was done about the risk.

## Process

### 1. Check the mode

Read `harness/review-policy.json`. In `advisory` mode a MISRA finding never blocks a merge, so a record is usually unnecessary: say so and stop. Write one when the mode is `required`, or when the user asks for it anyway.

**Done when:** you can state the mode and why this case needs a record.

### 2. Rule out the alternative first

A deviation is the answer when the rule cannot be met, not when meeting it is inconvenient. Show the user the change that would comply and what it costs. Many required rules have a compliant form once the code is restructured.

**Done when:** the user has seen the compliant alternative and chosen the deviation over it.

### 3. Write the record

Create `docs/deviations/DEV-NNNN.md`, where `NNNN` is the next unused number in that folder:

```markdown
# DEV-NNNN: <one line>

- Rule: MISRA C:2012 Rule X.Y (required)
- Raised by: <name> <email>, <date>
- Ticket: FW-NNNN
- Scope: <the exact files, functions, or lines this covers>

## Why the rule cannot be met here

<the constraint: the hardware, the vendor header, the toolchain>

## Risk

<what the rule protects against, and what could go wrong here without it>

## What limits the risk

<the review, the test, the assertion, or the runtime check that covers it>

## Approver

<name>, <date>
```

**Done when:** the file exists, its scope names exact files rather than a whole module, and the risk section says what could go wrong rather than that nothing will.

### 4. Get an approver who is not the author

The approver is someone other than whoever wrote the code. Leave that line for them and tell the user who needs to sign it.

**Done when:** the user knows the record needs another person's approval before the ticket can reach `done`, and a comment in the code names `DEV-NNNN` where the deviation applies.
