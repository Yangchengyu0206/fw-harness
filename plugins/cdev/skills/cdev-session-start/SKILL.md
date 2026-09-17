---
name: cdev-session-start
description: Start a session: read where the work stands, and agree with the user which feature to take.
disable-model-invocation: true
---

# cdev-session-start

Four steps. The last one is a question for the user, not a decision for you.

## Process

### 1. Read the entry point

Read AGENTS.md, including the `Domains:` line, and CLAUDE.md.

**Done when:** you can name the repository's domains, its build and test commands, and its read-only folders.

### 2. Read where the work stands

Read `## Now` in PROGRESS.md and the newest entry under `## Log`, then list the features:

```bash
py -3 tools/feature.py show
```

**Done when:** you can say which feature was last worked on, where it stopped, and what its next step is.

### 3. Propose the feature

Propose, in this order: the `active` feature, then a `verifying` feature that still owes a step, then the first `next` feature. For the one you propose, read back its `behavior`, and its `verification` list when it has one, with `py -3 tools/feature.py show F-NNN`.

When there are no features yet, ask the user what to build and add it with `py -3 tools/feature.py add --title "..." --behavior "..."`. Add `--verify "..."` only for a check the user names or one that needs real hardware.

**Done when:** the user has the proposal with its behaviour in front of them.

### 4. Agree on it

Take the user's answer. When the feature is not already active, mark it:

```bash
py -3 tools/feature.py set F-NNN --status active
```

**Done when:** the user has named the feature, it is `active`, and no code has been written before that answer.
