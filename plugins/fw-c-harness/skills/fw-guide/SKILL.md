---
name: fw-guide
description: Ask which fw-harness skill fits your situation.
disable-model-invocation: true
---

# fw-guide

Fourteen skills is more than anyone remembers, so ask here instead. The ones marked "the agent reaches on its own" fire without you typing them; the rest you type.

## Setting the repository up

- **`/fw-harness-init`**: run once in a firmware repository. It writes the harness, drafts the architecture, and generates the ARCHITECTURE.md files.
- **`/fw-harness-upgrade`**: run after the plugin updates. Managed files are replaced, and anything your team owns is proposed for you to review one at a time.

## A day of work

1. **`/fw-session-start`**: begin here every session. It verifies the environment, reads your handoff, and ends by agreeing with you on the ticket.
2. **`fw-c-implement`** (the agent reaches on its own): the test-first loop, inside the module's approved layering.
3. **`/fw-hil-verify`**: when the ticket owes board verification, this collects the log and records it as evidence.
4. **`/fw-done`**: close the session. Handoff, progress note, ticket update, and a commit message for you to run.

**`fw-ticket`** (the agent reaches on its own) handles every ticket write underneath those steps, so you rarely call it yourself.

## Looking at code

- **`fw-c-review`** (the agent reaches on its own): the two-axis review, Standards and Spec, written into `harness/reviews/`. Reach for it before merging, and remember that a review by the author counts for nothing at the Definition of Done.
- **`fw-review-respond`** (the agent reaches on its own): a review of your ticket came back. It checks each finding against the code, fixes or declines it with evidence, writes the answer into the report, and hands the change back for re-review.
- **`fw-c-test-gap`** (the agent reaches on its own): what has no test, ranked P0 to P3, read-only. Reach for it when the question is coverage rather than correctness.
- **`fw-c-debug`** (the agent reaches on its own): reproduce, shrink, then fix. Reach for it for a hang, a HardFault, or anything intermittent.

## When a rule gets in the way

- **`fw-architecture-sync`** (the agent reaches on its own): `arch_check` failed, or a new folder of C sources appeared.
- **`fw-misra-deviation`** (the agent reaches on its own): a MISRA rule cannot be met and the decision needs a name on it.

## Where the rules actually live

The skills are thin on purpose. `harness/scripts/` holds the gates, `harness/architecture.json` holds the approved layering, `harness/review-checklist.json` holds the review severities, and `CLAUDE.md` holds the Definition of Done. When a skill and a script disagree, the script is right.
