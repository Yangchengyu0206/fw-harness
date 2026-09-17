# CLAUDE.md

Working rules for {{PROJECT}}. [AGENTS.md](AGENTS.md) is the short entry point; this file holds the rules and the reasons behind them.

## Working rules

- One active feature at a time. Finishing one before starting the next keeps PROGRESS.md honest about where the work is.
- {{TEST_RULE}}
- Run the change before calling it done: the build, the tests when there are any, and the code itself on a real input, with the commands in AGENTS.md. A change nobody ran is only a claim.
- Generated and vendor code stays as it came. Upgrade it from its source.
- A new source file goes into the build as well as onto disk.
- `feature_list.json` changes through `tools/feature.py`, which validates the file before every write.

## What done means

A feature is done when:

- the behaviour in its `behavior` field has been observed in a run, not only reasoned about
- every step in its `verification` list, if it has one, has been run
- the result, with the command and output that showed it, is recorded in PROGRESS.md

`verification` is optional. Leave it empty when running the code is proof enough. When a listed step is still owed, such as one that needs real hardware, the feature stays `verifying`, and the step it owes is its `next_step`.

## Decisions and why

Record a decision when the next reader would otherwise undo it.

| Date | Decision | Reason |
|---|---|---|
| | | |
