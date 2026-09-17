# cdev-debug

The agent reaches this one on its own.

## What it does

Records the defect as expected against actual, builds a loop that goes red on it, shrinks the reproduction, ranks three to five falsifiable hypotheses using the debugging anchors of the repository's domains and shows them to you, proves one, writes a regression test that fails, fixes, and cleans up every tagged debug line.

## When to reach for it

A crash, a hang, a reset loop, corrupted data, a kernel oops, a Windows bugcheck, a slowdown, or anything intermittent.

## Common questions

**Why build a loop before looking for the cause?** A fix for a defect nobody reproduced usually passes the test and fails later. With a command that goes red on this exact defect, every hypothesis can be checked in seconds; without one, the agent is guessing.

**What if nothing reproduces it?** The skill stops, lists what it tried, and asks you for access to the setup, a captured log or crash dump, or permission to instrument a build you run. It does not guess a fix.

**Where do the domain-specific tricks come from?** Each domain reference has a Debugging anchors section: sanitizers for C, HardFault decoding for firmware, lockdep and KASAN for Linux drivers, Driver Verifier and `!analyze` for Windows drivers, `faulthandler` for Python.

**A driver crash takes the machine down.** The skill moves the loop into a virtual machine you can snapshot, and reads the crash dump instead of rebooting by hand.

**Reproducing it needs a person.** The skill copies `scripts/hitl_loop.py` into a folder git ignores, writes the steps, and asks you to run it in your own terminal. Your answers land in `docs/evidence/`, where the agent reads them.

**The defect only happens on the target.** The regression check goes into the feature's verification list, and the skill says so rather than inventing a host test that cannot see it.

## It is working if

You saw the loop go red before any fix, you were shown the ranked hypotheses, a test or verification step now fails for the defect, no `DEBUG-` line is left behind, and you can name the root cause in one sentence.
