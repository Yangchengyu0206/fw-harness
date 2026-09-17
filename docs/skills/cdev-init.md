# cdev-init

User-invoked. Type `/cdev-init`.

## What it does

Detects which domains the repository belongs to, then writes AGENTS.md, CLAUDE.md, PROGRESS.md, `feature_list.json` with `tools/feature.py`, and an ARCHITECTURE.md for the root and every code folder. It runs the whole generation without stopping and hands you the finished result to review in one pass.

## When to reach for it

Once per repository, on a clean working tree.

## Common questions

**How does it decide the domains?** From files it can name: a linker script or `startup_*.s` means firmware, `obj-m` or `Kconfig` means a Linux driver, an `.inf` or `<wdf.h>` means a Windows driver, `pyproject.toml` or `.py` files mean Python, and plain `.c` files mean C. A repository can be several at once, such as firmware with Python test tooling.

**Why does it not ask me anything until the end?** Reviewing finished files is faster and more reliable than approving a plan for them. Nothing is committed until you say so, so `git diff` shows you the real result.

**My project has no tests.** That is fine. It writes `Test: none` into AGENTS.md, and no cdev skill adds a test framework unless you ask. Changes are checked by running the code on a real input instead.

**What if I already have an AGENTS.md?** It is left alone. The generated version lands as `AGENTS.md.cdev-proposed` for you to compare.

## It is working if

Every code folder has an ARCHITECTURE.md whose responsibility line describes what the folder does, AGENTS.md names the right domains, build command, run command, and whether the repository has tests, and everything lands in one commit you made.
