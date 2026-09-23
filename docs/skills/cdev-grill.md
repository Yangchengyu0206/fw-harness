# cdev-grill

User-invoked. Type `/cdev-grill`.

## What it does

Interviews you about a plan, a port, or a decision, one round of numbered questions at a time, until the assumptions under it are on the table. It looks up the facts itself, in the repository, through the `cdev-explorer` agent, and through whatever tools the session holds, and asks you only what you have to decide. At the end it writes each decision and its reason into `## Decisions and why` in the root ARCHITECTURE.md, and turns deferred work into features.

## When to reach for it

Before the work, not during it: bringing up a new chip, porting a driver, choosing how a feature will be structured, or any time you catch yourself saying "it should be the same as the last one".

## Common questions

**Is it going to interrogate me all day?** It is user-invoked, so it runs when you type it and never on its own. Each round is one message of questions with a recommended answer for each, so answering is usually quick.

**Why does it ask where a value came from?** A timing or a register sequence carried over from another part is the most common way firmware work goes wrong quietly. Naming the source, and what makes the two parts the same, is the cheapest moment to catch it.

**It asked something I do not care about.** Say so. The point is the assumptions you have not examined, not every branch of the tree.

## It is working if

You change your mind about something, or you write down a reason you were holding only in your head, before any code is written.
