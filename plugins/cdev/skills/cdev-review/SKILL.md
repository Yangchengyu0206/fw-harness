---
name: cdev-review
description: Review changed C or Python code along two axes, Standards and Spec, each in its own sub-agent, and write the report into docs/reviews. Use when the user asks for a code review, asks to review a branch or a feature's changes, or wants a review before merging.
---

# cdev-review

The two-axis structure is adapted from `code-review` in [mattpocock/skills](https://github.com/mattpocock/skills) (MIT); the self-verification pass from `skills/security-review/SKILL.md` in [github/awesome-copilot](https://github.com/github/awesome-copilot) (MIT).

Two axes, each in its own sub-agent so neither pollutes the other, reported side by side:

- **Standards**: does the code follow the review checklist of every domain it belongs to?
- **Spec**: does the code deliver what the feature asked for?

Reviewing your own work is expected here. That is why step 5 re-reads every finding against the code: the verification pass carries the weight a second reviewer would.

## Process

### 1. Pin the range

Capture the diff command once and run it before anything else:

```bash
git diff <fixed-point>...HEAD
```

Three dots, so the comparison is against the merge base. A bad ref or an empty diff fails here rather than inside two sub-agents.

**Done when:** the command prints a non-empty diff and you can name the feature the range belongs to.

### 2. Load the checklists

Read the `Domains:` line in AGENTS.md, then the `## Review checklist` section of each listed domain's reference: [c](../cdev-implement/references/c.md), [firmware](../cdev-implement/references/firmware.md), [linux-driver](../cdev-implement/references/linux-driver.md), [windows-driver](../cdev-implement/references/windows-driver.md), [python](../cdev-implement/references/python.md). Read the ARCHITECTURE.md of every folder the diff touches.

**Done when:** you hold the checklist text for every active domain and can list the folders the diff touches.

### 3. Dispatch the Standards sub-agent

Give it the diff command, the full text of every loaded checklist, and what each touched folder is allowed to depend on. It has no other access to any of that.

Brief it to report, per file and hunk: every place the diff breaks a checklist item, with the severity that item carries, and every new dependency the folder's ARCHITECTURE.md does not describe. Ask for an exact `path:line`, the problem, why it matters, a suggested fix, and a confidence rating. Under 500 words.

**Done when:** the sub-agent has returned findings, each with a `path:line`.

### 4. Dispatch the Spec sub-agent

Give it the diff command and the feature's `behavior` and `verification`, from `py -3 tools/feature.py show F-NNN`.

Brief it to report requirements that are missing or only partly delivered, behaviour in the diff nobody asked for, and requirements that look delivered but look wrong. Ask it to quote the feature line behind each finding. Under 500 words.

When no feature is known, skip this axis and say so in the report.

**Done when:** the sub-agent has returned findings, each quoting the feature line it answers to.

### 5. Verify each finding

Re-read the code behind every finding and rule out the false positive: a check that already happened earlier on the path, a bound the caller guarantees, a lock that is held after all. Drop what does not survive, and lower the confidence of anything resting on thin evidence.

**Done when:** every finding left has been re-read against the code, and you can say why each one is real.

### 6. Write the report

Follow [report-format.md](report-format.md) and write it to `docs/reviews/<YYYY-MM-DD>_F-NNN.md`. Keep the two axes under their own headings, in the words the sub-agents used; merging or reranking them undoes the separation.

**Done when:** the file exists, the counts in its table match the findings below it, and the two axes are still separate.

### 7. Hand it back

Tell the user which critical findings remain, and propose patches for them rather than applying them.

**Done when:** the user knows every critical finding and has a proposed fix for each.
