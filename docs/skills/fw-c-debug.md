# fw-c-debug

The agent reaches this one on its own.

## What it does

Reproduces the defect first, shrinks the reproduction until every remaining element is load bearing, confirms one hypothesis with evidence, writes a regression test that fails, and only then fixes.

## When to reach for it

A hang, a reset loop, a HardFault, corrupted data, a peripheral that works intermittently.

## Common questions

**Why reproduce first?** On a device, a fix for a defect nobody reproduced usually passes the test and fails in the field. Reproduction is what turns "it seems better" into a result.

**How do I read a HardFault?** The stacked PC is the faulting instruction and the stacked LR is where it came from. `CFSR` says which fault fired, and `BFAR` or `MMFAR` holds the address when its valid bit is set.

**The defect needs the board.** Then the regression check belongs in the ticket's `verification_steps`, and the skill says so rather than inventing a host test.

## It is working if

The defect was reproduced before the fix, a test now fails for it, and you can name the root cause in one sentence.
