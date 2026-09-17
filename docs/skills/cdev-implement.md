# cdev-implement

The agent reaches this one on its own.

## What it does

Reads the domain references the repository needs, then runs the test-first loop for a feature: read the feature and the folder documents, write a test and watch it fail, make the smallest change that passes, build and test with the project's own commands, and update the feature.

## When to reach for it

Whenever you are writing or changing C or Python for a feature.

## Common questions

**Why must the test fail first?** A test written after the code tends to check what the code does rather than what the feature asked for. Watching it fail is the cheapest proof it tests anything.

**What about behaviour only the board or the kernel can show?** It writes the host-side test for the logic it can reach, and leaves the rest to `cdev-target-verify`.

**Where do the rules come from?** One reference per domain: C, firmware, Linux driver, Windows driver, and Python. It reads only the ones AGENTS.md lists.

## It is working if

A test that failed first now passes, the build is clean, and the feature says which verification steps are still owed.
