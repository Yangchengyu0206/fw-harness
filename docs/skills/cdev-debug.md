# cdev-debug

The agent reaches this one on its own.

## What it does

Reproduces the defect, shrinks the reproduction until every element is load bearing, confirms one hypothesis with evidence using the debugging anchors of the repository's domains, writes a regression test that fails, and only then fixes.

## When to reach for it

A crash, a hang, a reset loop, corrupted data, a kernel oops, a Windows bugcheck, or anything intermittent.

## Common questions

**Why reproduce first?** A fix for a defect nobody reproduced usually passes the test and fails later. Reproduction turns "it seems better" into a result.

**Where do the domain-specific tricks come from?** Each domain reference has a Debugging anchors section: sanitizers for C, HardFault decoding for firmware, lockdep and KASAN for Linux drivers, Driver Verifier and `!analyze` for Windows drivers, `faulthandler` for Python.

**The defect only happens on the target.** The regression check goes into the feature's verification list, and the skill says so rather than inventing a host test.

## It is working if

The defect was reproduced before the fix, a test now fails for it, and you can name the root cause in one sentence.
