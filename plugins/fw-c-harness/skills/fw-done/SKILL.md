---
name: fw-done
description: "Wrap up a session: update your handoff, add a progress note, update the ticket, and draft the commit message for the user to run."
disable-model-invocation: true
---

# fw-done

Five steps. The last one hands a commit message to the user, because committing is theirs.

## Process

### 1. Read what changed

```bash
git status --porcelain
git diff
git log --oneline <session-start-commit>..HEAD
```

**Done when:** you can list every changed file and say, per file, why it changed.

### 2. Update your handoff

Overwrite `harness/handoff/<your-slug>.md` with the goal, what was done, what is blocked and why, and the suggested next step. One file per person, overwritten each time, so it says where you are rather than where you have been.

**Done when:** the file names the ticket, the branch, and a next step specific enough to act on without this conversation.

### 3. Add a progress note

Create `harness/progress/<YYYY-MM-DD>_<your-slug>_<n>.md`, where `<n>` is the next unused number for you today. Record the author, the ticket id, the start and end commits, what was done, and the `check` summary as evidence.

**Done when:** the file exists with a header carrying author, ticket, and both commits.

### 4. Update the ticket

Record the evidence this session produced, on a clean working tree:

```bash
py -3 harness/scripts/check.py --record FW-NNNN
```

Move the ticket to `verifying` when the code is written and `check` passes, and list what it still owes in `dod_pending`. Leave `done` to the user.

**Done when:** `ticket.py show FW-NNNN` reflects this session, and `dod_pending` names every debt that is left.

### 5. Draft the commit message

Write the message in the language from `language` in `harness/config.json`. It names the ticket id and says what changed and why. Show it to the user and let them run the commit.

**Done when:** the message is shown, it contains the ticket id, and you have told the user that committing and pushing are theirs to run.
