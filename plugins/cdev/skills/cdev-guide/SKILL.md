---
name: cdev-guide
description: "Ask which cdev skill fits your situation."
disable-model-invocation: true
---

# cdev-guide

Eleven skills is more than anyone remembers, so ask here instead. The ones marked "the agent reaches on its own" fire without you typing them; the rest you type.

## Setting the repository up

- **`/cdev-init`**: run once. It detects the repository's domains, writes AGENTS.md, CLAUDE.md, PROGRESS.md, the architecture documents, and the feature list, then hands you the whole result to review in one pass.

## A day of work

1. **`/cdev-session-start`**: begin here. It reads where the work stands and ends by agreeing with you on one feature.
2. **`cdev-implement`** (the agent reaches on its own): a failing test first when the repository has tests, otherwise an input and the output you expect; then the smallest change, then the build and a real run.
3. **`/cdev-target-verify`**: only when a feature needs real hardware or a real operating system to prove it: flashing a board, loading a driver, capturing the log. Pure algorithm work never needs it.
4. **`/cdev-done`**: close the session. PROGRESS.md, the feature's status, and a commit message for you to run.

**`cdev-feature`** (the agent reaches on its own) handles every change to `feature_list.json` underneath those steps, so you rarely call it yourself.

## Looking at code

- **`cdev-review`** (the agent reaches on its own): a two-axis review, Standards and Spec, written into `docs/reviews/`. Reviewing your own work is expected here, so it verifies every finding against the code before reporting it.
- **`cdev-test-gap`** (the agent reaches on its own): what has no test, ranked P0 to P3, read-only. Reach for it when the question is coverage rather than correctness.
- **`cdev-debug`** (the agent reaches on its own): make the defect show on demand, prove its cause, then fix. Reach for it for a crash, a hang, an oops, a bugcheck, or anything intermittent.

## When the structure changes

- **`cdev-architecture-sync`** (the agent reaches on its own): a folder appeared, or a folder's responsibility or dependencies changed.

## Where the rules live

The skills are thin on purpose. The domain rules, review checklists, debugging anchors, and build commands live in one reference per domain under `cdev-implement/references/`. The repository's own facts live in its files: AGENTS.md for domains and commands, CLAUDE.md for working rules, each ARCHITECTURE.md for its folder, and `feature_list.json` for what is being built.
