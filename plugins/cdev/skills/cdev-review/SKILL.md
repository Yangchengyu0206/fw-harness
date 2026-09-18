---
name: cdev-review
description: "Review changed C or Python code along two axes, Standards and Spec, each in its own sub-agent, and write the report into docs/reviews. Use when the user asks for a code review, asks to review a branch or a feature's changes, or wants a review before merging."
---

# cdev-review

The two-axis structure and the judgement-call baseline are adapted from `code-review` in [mattpocock/skills](https://github.com/mattpocock/skills) (MIT). The self-verification pass is adapted from `skills/security-review/SKILL.md`, and the caller check from `agents/gem-reviewer.agent.md`, both in [github/awesome-copilot](https://github.com/github/awesome-copilot) (MIT).

Two axes, each in its own sub-agent so neither pollutes the other, reported side by side:

- **Standards**: does the code follow the review checklist of every domain it belongs to, and does it break any caller it reaches?
- **Spec**: does the code deliver what the feature asked for?

Reviewing your own work is expected here. That is why step 5 re-reads every finding against the code: the verification pass carries the weight a second reviewer would.

Follow the reading rules in AGENTS.md while you work: search first and then read the function the search found, leave read-only folders out of broad searches, and send long command output to a file and read the errors and the tail. Two sub-agents plus a diff fill a context quickly.

## Process

### 1. Pin the range

Use the fixed point the user named. When they named none, use the merge base with the default branch, `git merge-base <default-branch> HEAD` (usually `main`), and say so in the report. Capture the diff command and the commit list once, and run both before anything else:

```bash
git diff <fixed-point>...HEAD
git log <fixed-point>..HEAD --oneline
```

Three dots in the diff, so the comparison is against the merge base. A bad ref or an empty diff fails here rather than inside two sub-agents.

**Done when:** the diff is non-empty and you can name the feature the range belongs to.

### 2. Load the checklists

Read the `Domains:` line in AGENTS.md, then the `## Review checklist` section of each listed domain's reference: [c](../cdev-implement/references/c.md), [firmware](../cdev-implement/references/firmware.md), [linux-driver](../cdev-implement/references/linux-driver.md), [windows-driver](../cdev-implement/references/windows-driver.md), [python](../cdev-implement/references/python.md). Read the ARCHITECTURE.md of every folder the diff touches.

Note which tools this repository already runs, from its build and test commands in AGENTS.md: a formatter, warnings as errors, `checkpatch.pl`, `ruff`, `mypy`. What they catch stays out of the review; repeating it buries the findings only a reviewer can make. A tool counts only when the repository really runs it, not when a reference merely suggests it.

**Done when:** you hold the checklist text for every active domain, can list the folders the diff touches, and can name the tools already run.

### 3. Find the callers the change reaches

List every function, macro, class, type, and global whose signature, meaning, units, error returns, locking, or calling context the diff changes. Find their users outside the diff:

```bash
git grep -n -w <name>
```

A change often breaks where it is called rather than where it is written: a return value that now means something else, a function that may now sleep, a length now counted in bytes instead of elements, an exception a caller never catches.

**Done when:** you hold a list of changed interfaces, each with its callers outside the diff, or the note that none changed.

### 4. Dispatch both sub-agents at once

Send both in the same turn. Where the tool runs sub-agents one at a time, run them in sequence, still as two separate sub-agents.

**Standards.** Give it the diff command, the full text of every loaded checklist, what each touched folder is allowed to depend on, the tools already run, and the caller list from step 3. It has no other access to any of that. Brief it to report, per file and hunk:

- every place the diff breaks a checklist item, with the severity that item carries
- every new dependency the folder's ARCHITECTURE.md does not describe
- every caller from the list that the change breaks, cited at the caller's line
- the judgement calls below, labelled as judgement and rated at most Suggestion

The judgement calls, which the checklists and the repository's own documents always override:

- **Speculative generality**: parameters, configuration switches, or abstraction layers the feature does not need
- **Duplicated logic**: the same shape in more than one hunk or file of the change
- **A bare number or primitive** standing in for a unit, a flag set, or a state that deserves a named constant or a type
- **Shotgun surgery**: one logical change forcing scattered edits across many modules
- **A mysterious name**: a function or variable whose name does not say what it does or holds

Ask for, per finding: an exact `path:line`, whether it is a rule or a judgement, the problem, why it matters when the code runs, a suggested fix, and a confidence rating. Nothing the tools already catch. Under 500 words.

**Spec.** Give it the diff command, the commit list, and the feature's `behavior` and `verification`, from `py -3 tools/feature.py show F-NNN`. Brief it to report requirements that are missing or only partly delivered, behaviour in the diff nobody asked for, and requirements that look delivered but look wrong. Ask it to quote the feature line behind each finding. Under 500 words.

When no feature is known, skip the Spec sub-agent and say so in the report.

**Done when:** both sub-agents have returned, every Standards finding carries a `path:line` and a rule-or-judgement label, and every Spec finding quotes its feature line.

### 5. Verify each finding

Re-read the code behind every finding and rule out the false positive: a check that already happened earlier on the path, a bound the caller guarantees, a lock that is held after all, a caller the same range already updated. Drop what does not survive, drop anything the tools already catch, and lower the confidence of anything resting on thin evidence.

**Done when:** every finding left has been re-read against the code, and you can say why each one is real.

### 6. Write the report

Follow [report-format.md](report-format.md) and write it to `docs/reviews/<YYYY-MM-DD>_F-NNN.md`. Keep the two axes under their own headings, in the words the sub-agents used; merging or reranking them undoes the separation.

**Done when:** the file exists, the counts in its table match the findings below it, and the two axes are still separate.

### 7. Hand it back

Tell the user which critical findings remain, and propose patches for them rather than applying them.

**Done when:** the user knows every critical finding and has a proposed fix for each.
