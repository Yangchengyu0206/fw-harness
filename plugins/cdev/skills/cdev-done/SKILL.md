---
name: cdev-done
description: Wrap up a session: record where the work stands, update the feature, and draft the commit message for the user to run.
disable-model-invocation: true
---

# cdev-done

Four steps. The last one hands a commit message to the user, because committing is theirs.

## Process

### 1. Read what changed

```bash
git status --porcelain
git diff
```

**Done when:** you can list every changed file and say, per file, why it changed.

### 2. Update PROGRESS.md

Rewrite `## Now` so it says where the work is at this moment: the feature, where it stopped, the next step, and anything blocking it.

Add an entry at the top of `## Log` under today's date: what was done, what the build and tests reported (the command and its result), and anything the next session needs that is not in the code.

**Done when:** `## Now` names a next step specific enough to start from without this conversation, and the log entry quotes the build and test result.

### 3. Update the feature

```bash
py -3 tools/feature.py set F-NNN --status verifying --next "run the on-board loopback"
```

Use `verifying` when the code is written and a verification step is still owed, `done` when every step in the feature's `verification` has run, and leave it `active` when the work is unfinished.

**Done when:** `py -3 tools/feature.py show F-NNN` matches what PROGRESS.md says.

### 4. Draft the commit message

Write a message that names the feature id and says what changed and why. Show it to the user and let them run the commit.

**Done when:** the message is shown, it contains the feature id, and you have told the user that committing and pushing are theirs to run.
