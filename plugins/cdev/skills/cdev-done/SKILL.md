---
name: cdev-done
description: "Wrap up a feature or a session: check the documents against the change, record where the work stands, set the feature's status with the user's confirmation, and draft the commit message for the user to run."
disable-model-invocation: true
---

# cdev-done

Five steps. A feature becomes `done` only on the user's word, and the commit stays theirs to run.

## Process

### 1. Read what changed

```bash
git status --porcelain
git diff
```

**Done when:** you can list every changed file and say, per file, why it changed.

### 2. Bring the documents in line

```bash
py -3 tools/doc_check.py
```

Fix every drift it reports. Then compare the change with `## Flows` and `## Depends on` in each touched folder's ARCHITECTURE.md, which `doc_check` does not read, and update what the change made untrue.

**Done when:** `doc_check` reports no drift, and you can name each document you changed, or say why a touched folder's document still holds.

### 3. Decide the feature's status

- **Verification is owed and runs outside this editor** (a build in a vendor IDE, flashing, a test on the board): set `verifying` with `--next "<the step>"`, and write the checklist for the user under `Waiting on the user` in `## Now`: what to build, what to flash or load, what to do, what output shows success, and what shows failure.
- **Every verification step has passed**, run by you or reported by the user: show the user the evidence (the commands and their output, or the result they reported) and the documents you changed, and ask whether to close the feature.
- **The work is unfinished**: leave it `active`.

```bash
py -3 tools/feature.py set F-NNN --status done
```

Run that only after the user confirms.

**Done when:** `py -3 tools/feature.py show F-NNN` has the status the evidence supports, and a `done` status follows a confirmation from the user in this conversation.

### 4. Update PROGRESS.md

Rewrite `## Now`: the feature, where it stopped, the confirmed facts still needed, the next step, what is waiting on the user, and anything blocking it.

Add an entry at the top of `## Log` under today's date: what was done, how it was verified (each command with its result, or the result the user reported), which documents changed, and each decision with its reason.

**Done when:** `## Now` names a next step specific enough to start from without this conversation, and the log entry quotes the evidence.

### 5. Draft the commit message

Write a message that names the feature id and says what changed and why. Show it to the user and let them run the commit.

**Done when:** the message is shown, it contains the feature id, and you have told the user that committing and pushing are theirs to run.
