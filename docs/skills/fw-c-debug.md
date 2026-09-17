# fw-c-debug

The agent reaches this one on its own.

## What it does

Records the defect as expected against actual, builds a loop that goes red on it, shrinks the reproduction, ranks three to five falsifiable hypotheses and shows them to you, proves one with the debugger or light tracing, writes a regression test that fails, fixes, and cleans up every tagged debug line.

## When to reach for it

A hang, a reset loop, a HardFault, corrupted data, a peripheral that works intermittently, a missed deadline.

## Common questions

**Why build a loop before looking for the cause?** A fix for a defect nobody reproduced usually passes the test and fails in the field. With a command that goes red on this exact defect, every hypothesis can be checked in seconds; without one, the agent is guessing.

**What if nothing reproduces it?** The skill stops, lists what it tried, and asks you for access to the setup, a captured log or fault register dump, or permission to instrument a build you run. It does not guess a fix.

**The defect needs someone to press reset.** The skill copies `scripts/hitl_loop.py` into `build/debug/`, writes the steps, and asks you to run it in your own terminal. Your answers land in the ticket's evidence folder, where the agent reads them.

**Why does it prefer the debugger over `printf`?** A log line over UART changes timing and can make a race disappear. The order is debugger, then RTT, ITM, or a ring buffer, then log lines.

**How do I read a HardFault?** The stacked PC is the faulting instruction and the stacked LR is where it came from. `CFSR` says which fault fired, and `BFAR` or `MMFAR` holds the address when its valid bit is set.

**The defect needs the board.** Then the regression check belongs in the ticket's `verification_steps`, and the skill says so rather than inventing a host test that cannot see it.

## It is working if

You saw the loop go red before any fix, you were shown the ranked hypotheses, a test or board step now fails for the defect, no `DEBUG-` line is left behind, and you can name the root cause in one sentence.
