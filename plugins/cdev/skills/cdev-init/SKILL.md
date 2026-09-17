---
name: cdev-init
description: Generate a markdown-first harness in this repository: AGENTS.md, CLAUDE.md, architecture documents, a progress log, and a feature list.
disable-model-invocation: true
---

# cdev-init

Writes the harness into the repository you are standing in, then hands the finished result to the user for one review. It creates files and never overwrites them: an existing file keeps its content, and the new version lands beside it as `<name>.cdev-proposed`.

The templates sit beside this skill in [templates](templates).

## Process

### 1. Confirm the target

Confirm the repository root with the user, and that `git status --porcelain` is empty. A clean tree lets the user review everything this skill writes as one diff.

**Done when:** the user has confirmed the path and the working tree is clean.

### 2. Detect the domains

A repository belongs to a set of domains, not one. Look for these signals and record every domain that has at least one:

| Domain | Signals |
|---|---|
| `firmware` | a linker script (`*.ld`, `*.icf`, `*.sct`), a `startup_*.s`, an `arm-none-eabi` toolchain file, vendor HAL folders |
| `linux-driver` | `obj-m` in a Makefile, a `Kconfig`, `#include <linux/module.h>` |
| `windows-driver` | an `.inf`, a driver project in a `.vcxproj`, `#include <wdf.h>` or `<ntddk.h>` |
| `python` | `pyproject.toml`, `setup.py`, `requirements*.txt`, or `.py` files |
| `c` | `.c` or `.h` files, when none of `firmware`, `linux-driver`, or `windows-driver` matched |

Each domain has a reference the other cdev skills read: [c](../cdev-implement/references/c.md), [firmware](../cdev-implement/references/firmware.md), [linux-driver](../cdev-implement/references/linux-driver.md), [windows-driver](../cdev-implement/references/windows-driver.md), [python](../cdev-implement/references/python.md).

**Done when:** every domain in the set is backed by a file you can name.

### 3. Generate everything, with no questions in between

Nothing is committed yet, so the whole result stays a draft the user can change. Do all of this, then stop:

1. Copy `templates/tools/feature.py` to `tools/feature.py` and `templates/feature_list.json` to `feature_list.json`.
2. Scan the code folders two levels deep. A folder named like `third_party`, `vendor`, `external`, or a vendor SDK, or whose files carry a generated marker in their first lines, is read-only.
3. For each code folder, read its code and write `ARCHITECTURE.md` from `templates/ARCHITECTURE.folder.md`.
4. Write `ARCHITECTURE.md` at the root from `templates/ARCHITECTURE.root.md`, and `AGENTS.md`, `CLAUDE.md`, and `PROGRESS.md` from their templates.
5. Run `py -3 tools/feature.py check`.

Fill every placeholder from what you found:

| Placeholder | Value |
|---|---|
| `{{PROJECT}}` | the repository's name, from its folder or its build files |
| `{{DOMAINS}}` | the detected set, comma separated, for example `firmware, python` |
| `{{EDITABLE}}` | a bullet list of the folders the user owns |
| `{{READ_ONLY}}` | a bullet list of vendor and generated folders, or `none` |
| `{{BUILD}}` | the build command from the repository's build files; when there are none, the Build and test section of the domain's reference |
| `{{TEST}}` | the test command, found the same way |
| `{{DATE}}` | today's date, `YYYY-MM-DD` |
| `{{MODULES}}` | a table of every code folder: folder, role, and what it depends on |
| `{{FOLDER}}` | the folder's path from the repository root |
| `{{RESPONSIBILITY}}` | one sentence on what the folder does, from reading its code rather than its file names |
| `{{ENTRY_POINTS}}` | the functions or commands other code is meant to call |
| `{{DEPENDS_ON}}` | the folders and libraries it includes or imports |
| `{{NOTES}}` | what the domain needs recorded: interrupts, shared state, and stack for firmware; locking and context for drivers; external services and hardware for Python |

**Done when:** every file exists, no `{{` remains in any file you wrote, and `feature.py check` passes.

### 4. Hand the whole result over for review

One message, with the finished work rather than a plan for it:

- the domain set, and the file behind each domain
- a table of code folders: role, depends on, read-only or not, and a Note column flagging every guess (a folder classified read-only from its name alone, a responsibility inferred from little code, a build or test command taken from a reference because the repository had none)
- every `.cdev-proposed` file, and why it exists
- what is left to the user: the decisions table in CLAUDE.md and the first features

Then ask one question: what is wrong? One answer covering every row is the approval these documents need. `git diff` stays open to the user the whole time, so they read the real files. Apply each correction and show the difference it made.

**Done when:** the user has answered once, and every correction they named is applied.

### 5. Commit

**Done when:** everything this skill wrote is in one commit, made after the user says to commit.
