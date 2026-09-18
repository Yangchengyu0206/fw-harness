---
name: cdev-session-start
description: "Start a session in full: read where the work stands, check the architecture documents for drift, and agree with the user which feature to take."
disable-model-invocation: true
---

# cdev-session-start

AGENTS.md already tells the agent to open every conversation with a short version of this. Type it when you want the full pass: the newest log entry, the drift fixed before work starts, and the feature's behaviour read back. The last step is a question for the user, not a decision for you.

## Process

### 1. Read where the work stands

Read the `Domains:` line in AGENTS.md, `## Now` in PROGRESS.md, and the newest entry under `## Log`, then list the features:

```bash
py -3 tools/feature.py show
```

**Done when:** you can say which feature was last worked on, where it stopped, its next step, and what `Waiting on the user` holds.

### 2. Check the documents

```bash
py -3 tools/doc_check.py
```

When it reports drift, show it to the user and offer to fix it before the feature work starts, with cdev-architecture-sync when a folder appeared or disappeared.

**Done when:** `doc_check` reports no drift, or the user has chosen to leave the drift for later.

### 3. Propose the feature

Propose, in this order: the `active` feature, then a `verifying` feature whose checklist is waiting on the user, then the first `next` feature. For the one you propose, read back its `behavior`, and its `verification` list when it has one, with `py -3 tools/feature.py show F-NNN`.

When a `verifying` feature is waiting on the user, ask for the result of the checklist in `## Now` first.

When there are no features yet, ask the user what to build and add it with `py -3 tools/feature.py add --title "..." --behavior "..."`. Add `--verify "..."` only for a check the user names or one that needs real hardware.

**Done when:** the user has the proposal with its behaviour in front of them.

### 4. Agree on it

Take the user's answer. When the feature is not already active, mark it:

```bash
py -3 tools/feature.py set F-NNN --status active
```

**Done when:** the user has named the feature, it is `active`, and no code has been written before that answer.
