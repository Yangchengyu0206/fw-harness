---
name: fw-c-review
description: "Review changed C code along two axes, Standards and Spec, each in its own sub-agent, and write the report into harness/reviews. Use when the user asks for a code review, asks to review a branch or a ticket's changes, or wants a review before merging."
---

# fw-c-review

The two-axis structure and the judgement-call baseline are adapted from `code-review` in [mattpocock/skills](https://github.com/mattpocock/skills) (MIT). The self-verification pass is adapted from `skills/security-review/SKILL.md`, and the caller check from `agents/gem-reviewer.agent.md`, both in [github/awesome-copilot](https://github.com/github/awesome-copilot) (MIT).

Two axes, each in its own sub-agent so neither pollutes the other, reported side by side:

- **Standards**: does the code follow the checklist, the approved layering, and the MISRA mode, and does it break any caller it reaches?
- **Spec**: does the code deliver what the ticket asked for?

A reviewer is someone other than the author. `harness/review-policy.json` sets `forbid_self_review`, and the Definition of Done counts only the latest review by another person, so a self-review buys the ticket nothing.

## Process

### 1. Pin the range

Use the fixed point the user named. When they named none, use the merge base with the default branch, `git merge-base <default-branch> HEAD` (usually `main`), and say so in the report. Capture the diff command and the commit list once, and run both before anything else:

```bash
git diff <fixed-point>...HEAD
git log <fixed-point>..HEAD --oneline
```

Three dots in the diff, so the comparison is against the merge base. A bad ref or an empty diff fails here rather than inside two sub-agents.

**Done when:** the diff is non-empty and you can name the ticket the range belongs to.

### 2. Load the rules

Read `harness/review-checklist.json` and `harness/review-policy.json`. The checklist is the severity list; the policy sets the MISRA mode and what blocks a merge. Read the ARCHITECTURE.md of every folder the diff touches, for its approved dependencies.

Read the `check` section of `harness/config.json` too. Whatever it already enforces (the formatter, `cppcheck`, the `-Werror` build) stays out of the review: the gate reports it, and repeating it buries the findings only a reviewer can make.

**Done when:** you can state the MISRA mode, list the folders the diff touches, and name the checks the gates already run.

### 3. Find the callers the change reaches

List every function, macro, type, and global whose signature, meaning, units, error returns, locking, or calling context the diff changes. Find their users outside the diff:

```bash
git grep -n -w <name>
```

A C change often breaks where it is called rather than where it is written: a return code that now means something else, a function that may now block, a buffer length now counted in bytes instead of elements.

**Done when:** you hold a list of changed interfaces, each with its callers outside the diff, or the note that none changed.

### 4. Dispatch both sub-agents at once

Send both in the same turn. Where the tool runs sub-agents one at a time, run them in sequence, still as two separate sub-agents.

**Standards.** Give it the diff command, the full checklist text, the MISRA mode, the approved dependencies of the touched modules, the checks the gates already run, and the caller list from step 3. It has no other access to any of that. Brief it to report, per file and hunk:

- every place the diff breaks a checklist item, with the severity that item carries
- every include that leaves the module's approved dependencies
- in `required` mode, every required MISRA rule broken with no deviation record
- every caller from the list that the change breaks, cited at the caller's line
- the judgement calls below, labelled as judgement and rated at most Suggestion

The judgement calls, which the checklist and the team's documents always override:

- **Speculative generality**: parameters, configuration switches, or abstraction layers the ticket does not need
- **Duplicated logic**: the same shape in more than one hunk or file of the change
- **A bare number or primitive** standing in for a unit, a register field, or a state that deserves a named constant or a type
- **Shotgun surgery**: one logical change forcing scattered edits across many modules
- **A mysterious name**: a function or variable whose name does not say what it does or holds

Ask for, per finding: an exact `path:line`, whether it is a rule or a judgement, the problem, why it matters on the device, a suggested fix, and a confidence rating. Nothing the gates already enforce. Under 500 words.

**Spec.** Give it the diff command, the commit list, and the ticket's `user_visible_behavior`, `verification_steps`, and `dod_pending`, from `py -3 harness/scripts/ticket.py show FW-NNNN`. Brief it to report requirements that are missing or only partly delivered, behaviour in the diff nobody asked for, and requirements that look delivered but look wrong. Ask it to quote the ticket line behind each finding. Under 500 words.

When no ticket is known, skip the Spec sub-agent and say so in the report.

**Done when:** both sub-agents have returned, every Standards finding carries a `path:line` and a rule-or-judgement label, and every Spec finding quotes its ticket line.

### 5. Verify each finding

Re-read the code behind every finding and rule out the false positive: a check that already happened earlier on the path, a bound the caller guarantees, a `volatile` that is there after all, a caller the same range already updated. Drop what does not survive, drop anything the gates already enforce, and lower the confidence of anything that rests on thin evidence.

**Done when:** every finding left has been re-read against the code, and you can say why each survivor is real.

### 6. Write the report

Follow [report-format.md](report-format.md). Write it to `harness/reviews/FW-NNNN_<your-slug>_<YYYY-MM-DD>.md`, in the language from `language` in `harness/config.json`. Keep the two axes under their own headings, in the words the sub-agents used. Merging or reranking them across axes undoes the separation, so present them side by side.

**Done when:** the file exists, the counts in its table match the findings below it, and the two axes are still separate.

### 7. Record the evidence

```bash
py -3 harness/scripts/ticket.py evidence FW-NNNN review --ref harness/reviews/<file> --open-critical <count>
```

The count is the number of critical findings still open. Propose patches and leave applying them to a human.

**Done when:** the ticket carries the review evidence, and you have told the user which findings block the merge.
