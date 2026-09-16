---
name: fw-session-start
description: Start a firmware session: verify the environment, read your handoff and the recent history, and agree with the user which ticket you are taking.
disable-model-invocation: true
---

# fw-session-start

Six steps, in order. The last one is a question for the user, not a decision for you.

## Process

### 1. Confirm where and who you are

Print the repository root, the current branch, and `git config user.name` and `user.email`. Every state write records that identity, so a wrong identity quietly attributes your work to someone else.

**Done when:** all four values are printed and the user has not corrected them.

### 2. Verify the environment

```bash
sh init.sh
```

On Windows PowerShell, run `.\init.ps1`. It checks Python, identity, `core.hooksPath`, the harness layout, and the toolchain, then runs `check` once.

**Done when:** `init` exits zero, or every `[FAIL]` line is reported to the user with the fix it names.

### 3. Read your handoff

Read `harness/handoff/<your-slug>.md`. It holds what your previous session left behind.

**Done when:** you can state the goal, the blockers, and the suggested next step it records, or you have confirmed the file does not exist yet.

### 4. Read the recent history

Read the last three files in `harness/progress/` and run `git log --oneline -10`.

**Done when:** you can name what changed in the repository since your handoff was written.

### 5. List the candidates

Read `feature_list.json`, running `py -3 harness/scripts/index.py` first when it is missing. Present, in this order: your own `active` ticket, then `verifying` tickets that still owe work, then the `next` queue by priority.

**Done when:** the list is presented with each ticket's id, title, status, and assignee.

### 6. Agree on the ticket

Ask the user which ticket to take, and take that answer. When it is not already yours, claim it:

```bash
py -3 harness/scripts/ticket.py claim FW-NNNN
```

When you are taking over someone else's ticket, read their handoff at `harness/handoff/<their-slug>.md` first.

**Done when:** the user has named the ticket, it is `active` with you as the assignee, and you have read its `user_visible_behavior` and `verification_steps` back to the user before any code is written.
