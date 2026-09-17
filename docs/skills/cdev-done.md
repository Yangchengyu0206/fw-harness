# cdev-done

User-invoked. Type `/cdev-done`.

## What it does

Closes a session: reads the diff, rewrites where PROGRESS.md says the work is, adds a dated log entry with the build and test result, updates the feature's status and next step, and drafts a commit message naming the feature.

## When to reach for it

At the end of every session, before you commit.

## Common questions

**Why does it not commit?** Committing and pushing stay with you. The skill hands you the message and stops.

**Why both PROGRESS.md and the feature list?** They answer different questions. The feature list says what is being built and how far each piece is; PROGRESS.md says where you stopped and why, which is what the next session needs first.

## It is working if

Tomorrow's session can start from `## Now` in PROGRESS.md without rereading today's conversation.
