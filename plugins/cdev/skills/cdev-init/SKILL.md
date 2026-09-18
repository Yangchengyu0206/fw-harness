---
name: cdev-init
description: "Generate a markdown-first harness in this repository: AGENTS.md, architecture documents, a progress log, a feature list, and the editor settings that guard read-only code."
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

1. Copy `templates/tools/feature.py` and `templates/tools/doc_check.py` into `tools/`, and `templates/feature_list.json` to `feature_list.json`.
2. Scan the code folders two levels deep. A folder named like `third_party`, `vendor`, `external`, or a vendor SDK, or whose files carry a generated marker in their first lines, is read-only.
3. For each code folder, read its code and write `ARCHITECTURE.md` from `templates/ARCHITECTURE.folder.md`. Read the functions a flow passes through before writing the flow.
4. Write `ARCHITECTURE.md` at the root from `templates/ARCHITECTURE.root.md`, and `AGENTS.md`, `CLAUDE.md`, and `PROGRESS.md` from their templates.
5. Write `.vscode/settings.json` and `.github/instructions/architecture.instructions.md` from the templates of the same path. GitHub Copilot in VS Code reads both: the settings make read-only folders uneditable and keep destructive terminal commands from running without the user's approval, and the instructions reach the agent whenever it works on code a document describes.
6. Run `py -3 tools/feature.py check` and `py -3 tools/doc_check.py`.

Fill every placeholder from what you found:

| Placeholder | Value |
|---|---|
| `{{PROJECT}}` | the repository's name, from its folder or its build files |
| `{{DOMAINS}}` | the detected set, comma separated, for example `firmware, python` |
| `{{VERIFICATION}}` | `off`. Every repository starts there, and step 4 offers the other two |
| `{{EDITABLE}}` | a bullet list of the folders the user owns |
| `{{READ_ONLY}}` | a bullet list of vendor and generated folders, or `none` |
| `{{BUILD}}` | the build command in backticks, from the repository's build files; when there are none, the Build and test section of the domain's reference. When the project builds only inside a vendor IDE (AndeSight, Keil, IAR, MCUXpresso, or any Eclipse-based IDE whose project files you find), write `in <IDE>, outside this editor; the user builds and reports the errors` |
| `{{TEST}}` | the test command in backticks, from the repository's own test setup, or `none` when it has no tests. Never take it from a reference, and never add a test framework here |
| `{{RUN}}` | the command in backticks that runs the program or its main example, from the README, the build files, or the entry point. For firmware flashed from a vendor IDE, write `flashed and run by the user; the agent writes the checklist`. Write `unknown` when none is found |
| `{{FIRST_STEP}}` | with tests: `Write a failing test first.` With `Test: none`: `Write down the input you will run the change on and the output you expect.` |
| `{{TEST_RULE}}` | with tests: `A failing test before the code. A test written after the code tends to check what the code does rather than what the feature asked for.` With `Test: none`: `No test framework is added unless the user asks for one. Each change is checked by running it on a real input and comparing the output with what was expected.` |
| `{{DATE}}` | today's date, `YYYY-MM-DD` |
| `{{MODULES}}` | a table of every code folder: folder, role, and what it depends on |
| `{{FOLDER}}` | the folder's path from the repository root |
| `{{RESPONSIBILITY}}` | one sentence on what the folder does, from reading its code rather than its file names |
| `{{FILES}}` | one bullet per file directly in the folder: the name in backticks, a colon, and its role in a few words. A glob such as `hal_*.c` stands for a group with one role |
| `{{FLOWS}}` | the sequences that run through the folder, each as a short numbered list naming the function and file at every step: start-up and initialisation, the interrupt or event path, the main loop, and the procedure behind each main feature. Write `none` for a folder of helpers with no sequence of its own |
| `{{ENTRY_POINTS}}` | the functions or commands other code is meant to call |
| `{{DEPENDS_ON}}` | the folders and libraries it includes or imports |
| `{{NOTES}}` | what the domain needs recorded: interrupts, shared state, and stack for firmware; locking and context for drivers; external services and hardware for Python |
| `{{READ_ONLY_GLOBS}}` | a JSON object with one `"<folder>/**": true` entry per read-only folder, or `{}` when there are none |
| `{{CODE_GLOBS}}` | the editable code folders as comma-separated globs, for example `src/**,drivers/**` |

**Done when:** every file exists, no `{{` remains in any file you wrote, `feature.py check` passes, and `doc_check.py` reports no drift.

### 4. Hand the whole result over for review

One message, with the finished work rather than a plan for it:

- the domain set, and the file behind each domain
- a table of code folders: role, depends on, read-only or not, and a Note column flagging every guess (a folder classified read-only from its name alone, a responsibility inferred from little code, a flow written from part of its path, a build command taken from a reference because the repository had none, a run command marked `unknown`)
- whether the build and the run happen in this editor or in a vendor IDE. When they happen in an IDE, say that each feature will stop at `verifying` with a checklist for the user, and ask whether the IDE's toolchain can be run from a command line
- whether the repository has tests. When it has none, say plainly that the skills will not add any unless asked, and will run each change on a real input instead
- every `.cdev-proposed` file, and why it exists
- what is left to the user: the decisions table in the root ARCHITECTURE.md and the first features

Ask the verification question inside that same message, so it stays one question: the `Verification:` line in AGENTS.md starts at `off`, which keeps the agent from asking for hardware results and records in each log entry what was not checked on hardware; `light` adds the one step still owed as the feature's next step; `full` adds the checklist, the evidence files, and cdev-target-verify. Say which one you would pick for this repository and why, and that the line is one word to change later.

Then ask what is wrong? One answer covering every row is the approval these documents need. `git diff` stays open to the user the whole time, so they read the real files. Apply each correction and show the difference it made.

**Done when:** the user has answered once, every correction they named is applied, and the `Verification:` line holds the mode they chose.

### 5. Commit

**Done when:** everything this skill wrote is in one commit, made after the user says to commit.
