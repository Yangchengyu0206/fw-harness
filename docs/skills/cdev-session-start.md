# cdev-session-start

User-invoked. Type `/cdev-session-start`.

## What it does

Reads AGENTS.md and CLAUDE.md, reads where PROGRESS.md says the work stopped, lists the features, proposes the one to take with its behaviour read back, and marks it active once you agree.

## When to reach for it

At the start of every session, before any code.

## Common questions

**Can it pick the feature for me?** It proposes one, in a fixed order: the active feature, then one still owed verification, then the next in the queue. You make the choice.

**There are no features yet.** It asks what to build and adds the first one.

**Why read the domains first?** They decide which rules the other skills apply to the code you are about to write.

## It is working if

You start writing code with one active feature, and you can say in one sentence what it must make the product do.
