# cdev-implement

The agent reaches this one on its own.

## What it does

Reads the domain references the repository needs, then works a feature through: read the feature and the folder documents, decide how to know it works, make the smallest change, build and run it, and update the feature. When the repository has tests, knowing it works means a test that fails first. When AGENTS.md says `Test: none`, it means an input and the output you expect, and no test framework is added.

## When to reach for it

Whenever you are writing or changing C or Python for a feature.

## Common questions

**My project has no tests. Will it add some?** No, unless you ask. It writes down an input and the output you expect, runs the code before and after the change, and shows you both. For floating point it records the tolerance too.

**Why must a test fail first, when there are tests?** A test written after the code tends to check what the code does rather than what the feature asked for. Watching it fail is the cheapest proof it tests anything.

**What about behaviour only the board or the kernel can show?** It writes the host-side test for the logic it can reach, and leaves the rest to `cdev-target-verify`.

**Where do the rules come from?** One reference per domain: C, firmware, Linux driver, Windows driver, and Python. It reads only the ones AGENTS.md lists.

## It is working if

You were shown the command and output that prove the change works, the build is clean, and the feature is `done` or names the verification step still owed.
