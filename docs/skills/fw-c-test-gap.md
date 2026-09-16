# fw-c-test-gap

The agent reaches this one on its own.

## What it does

A read-only audit of what has no test, ranked P0 to P3. It maps the behaviour in scope against the tests that exist, says what the current tests actually prove, and names the test that would close each gap.

## When to reach for it

When the question is coverage rather than correctness: what is untested, what regression test a fix needs, whether a change is safe to ship.

## Common questions

**Why must every number come with a command?** A count with nothing behind it is the easiest claim in a report to get wrong. The rule is to show the command that produced it or to describe the pattern instead.

**It says something needs the board.** Some behaviour a host test cannot prove. The audit says so and points at the ticket's `verification_steps` rather than proposing a test that would pass without proving anything.

**Will it write the tests?** Only if you ask, and then through `fw-c-implement`, so the test still fails first.

## It is working if

Every gap names a line you can open, and nothing in the report is asserted without the evidence beside it.
