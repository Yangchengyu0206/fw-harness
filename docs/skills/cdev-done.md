# cdev-done

User-invoked. Type `/cdev-done`.

## What it does

Closes a feature or a session: reads the diff, brings the architecture documents in line with it, sets the feature's status (`verifying` with a checklist for you when a build or a test outside the editor is owed, `done` only after you confirm), rewrites where PROGRESS.md says the work is, adds a dated log entry with the evidence and the decisions, and drafts a commit message naming the feature.

## When to reach for it

When a feature's verification has passed, or at the end of a session, before you commit.

## Common questions

**Why does it not commit?** Committing and pushing stay with you. The skill hands you the message and stops.

**Why does it ask before setting `done`?** An agent marking its own work finished makes `done` mean nothing. You see the evidence and decide.

**Why both PROGRESS.md and the feature list?** They answer different questions. The feature list says what is being built and how far each piece is; PROGRESS.md says where you stopped and why, which is what the next session needs first.

## It is working if

Tomorrow's session can start from `## Now` in PROGRESS.md without rereading today's conversation.
