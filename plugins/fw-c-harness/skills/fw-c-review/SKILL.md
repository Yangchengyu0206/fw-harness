---
name: fw-c-review
description: Review changed C code along two axes, Standards and Spec, each in its own sub-agent, and write the report into harness/reviews. Use when the user asks for a code review, asks to review a branch or a ticket's changes, or wants a review before merging.
---

# fw-c-review

Two axes, each in its own sub-agent so neither pollutes the other, reported side by side:

- **Standards**: does the code follow the checklist, the approved layering, and the MISRA mode?
- **Spec**: does the code deliver what the ticket asked for?

A reviewer is someone other than the author. `harness/review-policy.json` sets `forbid_self_review`, and the Definition of Done counts only the latest review by another person, so a self-review buys the ticket nothing.

## Process

### 1. Pin the range

Capture the diff command once and run it before anything else:

```bash
git diff <fixed-point>...HEAD
```

Three dots, so the comparison is against the merge base. A bad ref or an empty diff fails here rather than inside two sub-agents.

**Done when:** the command prints a non-empty diff and you can name the ticket the range belongs to.

### 2. Load the rules

Read `harness/review-checklist.json` and `harness/review-policy.json`. The checklist is the severity list; the policy sets the MISRA mode and what blocks a merge. Read the ARCHITECTURE.md of every folder the diff touches, for its approved dependencies.

**Done when:** you can state the MISRA mode and list the folders the diff touches.

### 3. Dispatch the Standards sub-agent

Give it the diff command, the full checklist text from `harness/review-checklist.json`, the MISRA mode, and the approved dependencies of the touched modules. It has no other access to any of that.

Brief it to report, per file and hunk: every place the diff breaks a checklist item, with the severity that item carries; every include that leaves the module's approved dependencies; and, in `required` mode, every required MISRA rule broken with no deviation record. Ask for an exact `path:line`, the problem, why it matters, a suggested fix, and a confidence rating. Under 500 words.

**Done when:** the sub-agent has returned findings, each with a `path:line`.

### 4. Dispatch the Spec sub-agent

Give it the diff command and the ticket's `user_visible_behavior`, `verification_steps`, and `dod_pending`, from `py -3 harness/scripts/ticket.py show FW-NNNN`.

Brief it to report requirements that are missing or only partly delivered, behaviour in the diff nobody asked for, and requirements that look delivered but look wrong. Ask it to quote the ticket line behind each finding. Under 500 words.

When no ticket is known, skip this axis and say so in the report.

**Done when:** the sub-agent has returned findings, each quoting the ticket line it answers to.

### 5. Verify each finding

Re-read the code behind every finding and rule out the false positive: a check that already happened earlier on the path, a bound the caller guarantees, a `volatile` that is there after all. Drop what does not survive, and lower the confidence of anything that rests on thin evidence.

**Done when:** every finding left in the report has been re-read against the code, and you can say why each survivor is real.

### 6. Write the report

Follow [report-format.md](report-format.md). Write it to `harness/reviews/FW-NNNN_<your-slug>_<YYYY-MM-DD>.md`, in the language from `language` in `harness/config.json`. Keep the two axes under their own headings, in the words the sub-agents used. Merging or reranking them across axes undoes the separation, so present them side by side.

**Done when:** the file exists, the counts in its table match the findings below it, and the two axes are still separate.

### 7. Record the evidence

```bash
py -3 harness/scripts/ticket.py evidence FW-NNNN review --ref harness/reviews/<file> --open-critical <count>
```

The count is the number of critical findings still open. Propose patches and leave applying them to a human.

**Done when:** the ticket carries the review evidence, and you have told the user which findings block the merge.
