# cdev-init

User-invoked. Type `/cdev-init`.

## What it does

Detects which domains the repository belongs to, then writes AGENTS.md (every rule, with CLAUDE.md importing it), PROGRESS.md, `feature_list.json`, six scripts in `tools/` (`feature.py`, `doc_check.py`, `hooks.py`, `mcp_list.py`, `value_check.py`, `personal.py`), an ARCHITECTURE.md for the root and every code folder with a line per file and the flows through it, empty `## Decisions and why` and `## Terms` tables in the root one, an empty NOTES.md for the facts that outlive a feature, and the VS Code files: settings that guard read-only folders, an instructions file that keeps the documents in the agent's view, the session hooks in `.github/hooks/cdev.json`, and the read-only `cdev-explorer` agent. It runs the whole generation without stopping and hands you the finished result to review in one pass.

## When to reach for it

Once per repository, on a clean working tree.

## Common questions

**How does it decide the domains?** From files it can name: a linker script or `startup_*.s` means firmware, `obj-m` or `Kconfig` means a Linux driver, an `.inf` or `<wdf.h>` means a Windows driver, `pyproject.toml` or `.py` files mean Python, and plain `.c` files mean C. A repository can be several at once, such as firmware with Python test tooling.

**Why does it not ask me anything until the end?** Reviewing finished files is faster and more reliable than approving a plan for them. Nothing is committed until you say so, so `git diff` shows you the real result.

**My project has no tests.** That is fine. It writes `Test: none` into AGENTS.md, and no cdev skill adds a test framework unless you ask. Changes are checked by running the code on a real input instead.

**How much verification does it set up?** `Verification: off`, every time. It offers `light` and `full` in the message that hands you the result, and the line is one word to change later. At `off` no skill asks for a board result; a feature still needs your confirmation to become `done`.

**My project builds in AndeSight, Keil, or another vendor IDE.** AGENTS.md then says the build and flashing happen outside the editor. Each feature stops at `verifying`, with what to build or flash and what output shows success under `Waiting on the user` in `## Now` (the full checklist at `full`), and you report the result back. When the IDE's toolchain also runs from a command line, put that command into the Build line and the agent compiles before handing over.

**My repository has submodules.** A submodule is not vendor code for being one; often the most edited code in a project lives in one. Each gets a row in the root map, and the handover asks which kind it is here: edited a lot (documented inside it like any folder), edited now and then (a folder's document is written inside it when the work first reaches it), or only used (a row in the map and nothing written inside it). Documents inside a submodule are committed in its own repository, on its branch rather than a detached HEAD.

**Will this end up in my team's repository?** Not by default. A harness starts personal: `tools/personal.py` puts every `.md` file, here and in each submodule, and the harness's other files into `.git/info/exclude`, which is never committed or pushed. To share it later, set `Sharing: team` in AGENTS.md, remove those lines from `info/exclude`, and commit the files.

**What if I already have an AGENTS.md?** It is left alone. The generated version lands as `AGENTS.md.cdev-proposed` for you to compare.

## It is working if

Every code folder has an ARCHITECTURE.md whose responsibility line describes what the folder does and whose flows name real functions, `doc_check` reports no drift, AGENTS.md names the right domains, build command, run command, and whether the repository has tests, and everything lands in one commit you made.
