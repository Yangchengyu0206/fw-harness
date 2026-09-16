# fw-session-start

User-invoked. Type `/fw-session-start`.

## What it does

Runs the six steps that open a firmware session: confirms the repository and your git identity, runs `init` to verify the environment, reads your handoff and the recent progress notes, lists the tickets you could take, and ends by agreeing with you on one.

## When to reach for it

At the start of every session, before any code. Reach for it again after a long break in the same session, when you no longer trust what the working tree contains.

## Common questions

**It stops at a `[FAIL]` line. What now?** Each line names its own fix. A missing `core.hooksPath` is one command; a missing toolchain is an install that `init` deliberately will not do for you.

**Can it pick the ticket for me?** No. It presents candidates and takes your answer, because the ticket decides what the rest of the session means.

**Someone else is the assignee.** It reads their handoff before you take over, so you start from what they left rather than from the code alone.

## It is working if

You end the six steps with one `active` ticket that is yours, and you can say in one sentence what the ticket must make the product do.
