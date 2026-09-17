---
name: cdev-guide
description: "Ask which cdev skill fits your situation."
disable-model-invocation: true
---

# cdev-guide

Twelve skills is more than anyone remembers, so ask here instead. The ones marked "the agent reaches on its own" fire without you typing them; the rest you type.

## Setting the repository up

- **`/cdev-init`**: run once. It detects the repository's domains, writes AGENTS.md, PROGRESS.md, the architecture documents, the feature list, and the VS Code settings that guard read-only code, then hands you the whole result to review in one pass.

## A day of work

Every new conversation opens on its own: AGENTS.md tells the agent to read `## Now`, list the features, run `doc_check`, and ask which feature to take.

1. **`/cdev-session-start`**: optional. The full version of that opening, with the drift fixed and the feature's behaviour read back.
2. **`cdev-implement`** (the agent reaches on its own): a failing test first when the repository has tests, otherwise an input and the output you expect; then the smallest change, then the build and a real run.
3. **`/cdev-target-verify`**: only when a feature needs real hardware or a real operating system to prove it: flashing a board, loading a driver, capturing the log. Pure algorithm work never needs it. When the build and flashing happen in a vendor IDE, the agent writes you a checklist in `## Now` instead, and you report back.
4. **`/cdev-checkpoint`**: when the context usage runs high, before a long break, or before a build in a vendor IDE. It saves what the conversation found into `## Now`, so a summary or a new conversation loses nothing.
5. **`/cdev-done`**: close a feature or a session. The documents checked against the change, PROGRESS.md, the feature's status on your confirmation, and a commit message for you to run.

**`cdev-feature`** (the agent reaches on its own) handles every change to `feature_list.json` underneath those steps, so you rarely call it yourself.

## Looking at code

- **`cdev-review`** (the agent reaches on its own): a two-axis review, Standards and Spec, written into `docs/reviews/`. Reviewing your own work is expected here, so it verifies every finding against the code before reporting it.
- **`cdev-test-gap`** (the agent reaches on its own): what has no test, ranked P0 to P3, read-only. Reach for it when the question is coverage rather than correctness.
- **`cdev-debug`** (the agent reaches on its own): make the defect show on demand, prove its cause, then fix. Reach for it for a crash, a hang, an oops, a bugcheck, or anything intermittent.

## When the structure changes

- **`cdev-architecture-sync`** (the agent reaches on its own): `doc_check` reported drift, a folder appeared, or a folder's files, flows, or dependencies changed.

## Where the rules live

The skills are thin on purpose. The domain rules, review checklists, debugging anchors, and build commands live in one reference per domain under `cdev-implement/references/`. The repository's own facts live in its files: AGENTS.md for domains, commands, and working rules (CLAUDE.md only imports it), each ARCHITECTURE.md for its folder's files and flows, PROGRESS.md for where the work stands, and `feature_list.json` for what is being built.
