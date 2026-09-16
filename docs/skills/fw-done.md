# fw-done

User-invoked. Type `/fw-done`.

## What it does

Closes a session in five steps: reads the diff, overwrites your handoff, adds a progress note, records this session's evidence on the ticket, and drafts a commit message that names the ticket.

## When to reach for it

At the end of every session, before you commit.

## Common questions

**Why does it not commit?** Committing and pushing stay with you in both tools. The skill hands you the message and stops.

**Which language is the message in?** The one in `language` in `harness/config.json`. The code and the harness files stay English; what the harness writes for humans follows that setting.

**Why one handoff file per person?** It is overwritten each time, so it says where you are rather than where you have been. The history lives in `harness/progress/`, one file per session, which is also why two people wrapping up on the same day never conflict.

## It is working if

The next person can pick up your ticket from the handoff alone, without this conversation.
