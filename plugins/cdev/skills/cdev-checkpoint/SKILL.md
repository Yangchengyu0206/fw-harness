---
name: cdev-checkpoint
description: "Save everything this conversation knows into PROGRESS.md, so a summarised or a new conversation resumes without losing it."
disable-model-invocation: true
---

# cdev-checkpoint

A long conversation gets summarised when the context fills, and the summary drops details. Type this when the context usage indicator runs high, before you close the editor, or before a long step such as a build in a vendor IDE. It writes what the conversation holds into `## Now`, where a summary cannot lose it.

## Process

### 1. Collect what the conversation holds

List, from this conversation:

- the feature and the step in progress
- the steps finished since `## Now` was last written
- every fact confirmed by reading the code, running something, or the user's report: addresses, register values, timings, call orders, error messages and their causes
- hypotheses still open, each marked unconfirmed
- the next step, and what is waiting on the user

**Done when:** every item is either on the list or you can say why the next conversation does not need it.

### 2. Rewrite `## Now`

Rewrite `## Now` in PROGRESS.md from the list. Keep confirmed facts and open hypotheses apart. Keep it short enough to read at the start of every conversation: a fact that only mattered to a finished step belongs in the next `## Log` entry, not in `## Now`.

Make the feature agree with it:

```bash
py -3 tools/feature.py set F-NNN --next "<the step>"
```

**Done when:** a reader of `## Now` alone could take the next step without asking what was found, and `py -3 tools/feature.py show F-NNN` names the same next step.

### 3. Confirm

Show the user the new `## Now`.

**Done when:** the user has seen it.
