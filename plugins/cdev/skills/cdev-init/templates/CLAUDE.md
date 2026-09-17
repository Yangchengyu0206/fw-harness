# CLAUDE.md

Working rules for {{PROJECT}}. [AGENTS.md](AGENTS.md) is the short entry point; this file holds the rules and the reasons behind them.

## Working rules

- One active feature at a time. Finishing one before starting the next keeps PROGRESS.md honest about where the work is.
- A failing test before the code. A test written after the code tends to check what the code does rather than what the feature asked for.
- Build and test before calling a feature done, with the commands in AGENTS.md.
- Generated and vendor code stays as it came. Upgrade it from its source.
- A new source file goes into the build as well as onto disk.
- `feature_list.json` changes through `tools/feature.py`, which validates the file before every write.

## What done means

A feature is done when:

- the behaviour in its `behavior` field can be observed, not only reasoned about
- every step in its `verification` list has been run, including the ones that need real hardware or a real operating system
- the result, with the build and test output that showed it, is recorded in PROGRESS.md

When the code is written but a verification step is still owed, the feature stays `verifying`, and the step it owes is its `next_step`.

## Decisions and why

Record a decision when the next reader would otherwise undo it.

| Date | Decision | Reason |
|---|---|---|
| | | |
