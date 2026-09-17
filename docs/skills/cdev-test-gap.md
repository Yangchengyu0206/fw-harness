# cdev-test-gap

The agent reaches this one on its own.

## What it does

A read-only audit of what has no test, ranked P0 to P3. It maps the behaviour in scope against the tests that exist, says what those tests actually prove, and names the test that would close each gap.

## When to reach for it

When the question is coverage rather than correctness: what is untested, what regression test a fix needs, whether a change is safe.

## Common questions

**Why must every number come with a command?** A count with nothing behind it is the easiest claim in a report to get wrong.

**It says something needs the target.** An interrupt, a driver load, or board-level timing cannot be proven by a host test. The audit points at the feature's verification list instead of proposing a test that would pass without proving anything.

**Will it write the tests?** Only when you ask, and then through `cdev-implement`, so each test still fails first.

## It is working if

Every gap names a line you can open, and nothing in the report is claimed without the evidence beside it.
