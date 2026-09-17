# {{PROJECT}}

Entry point for any agent working in this repository. Every rule the agent follows is in this file; CLAUDE.md only imports it.

## Domains

Domains: {{DOMAINS}}

The cdev skills read the matching domain reference for each domain listed here before they write, review, or debug code. Change this line when the repository gains or loses a domain.

## Where to work

Editable:

{{EDITABLE}}

Read-only (vendor or generated; upgrade from the source instead of editing here):

{{READ_ONLY}}

Ask before any of these:

- `git clean`, `git push`, force pushes, and rewriting history
- deleting a file the current task did not create
- editing a read-only folder
- changing compiler flags, linker scripts, or build configuration the task did not ask about

## Opening a conversation

Before the first answer in a new conversation:

1. Read `## Now` in PROGRESS.md.
2. Run `py -3 tools/feature.py show` and `py -3 tools/doc_check.py`.
3. Report in a few lines: the feature in progress, where it stopped, its next step, and any drift `doc_check` found.
4. When the user has not already said what to work on, ask which feature to take. Mark it with `py -3 tools/feature.py set F-NNN --status active` once they answer.

## Answering questions about the code

The architecture documents are a map for finding the code. The code is the source of truth.

1. Read the root ARCHITECTURE.md and the one in each folder the question touches. Use their `## Files` and `## Flows` to decide what to open.
2. Verify every claim about behaviour in the code. Read whole functions, follow definitions and callers, and follow interrupt handlers and shared state when the path crosses them.
3. Leave read-only folders out of broad searches. Read vendor code directly when the question turns on it: a HAL call, a register sequence, an SDK driver's locking.
4. Say where each part of the answer came from: verified in the code (with file and function), or taken from a document without checking.
5. When a document disagrees with the code, say so and offer the correction.

## Keeping the context small

- Search first, then read the function or section the search found.
- Send long build or run output to a file and read the errors and the tail: `<command> > build.log 2>&1`.
- Filter logs and dumps before reading them.

## Working on a feature

1. One active feature at a time.
2. {{FIRST_STEP}}
3. Build: {{BUILD}}
4. Test: {{TEST}}
5. Run: {{RUN}}
6. After each step, rewrite `## Now` in PROGRESS.md: what is done, the facts confirmed so far, and the next step. Write a confirmed fact (an address, a timing, a call order) there the moment it is confirmed; a long conversation gets summarised and loses details that live only in chat.
7. When a change adds, removes, or renames a file, changes what a folder depends on, or changes a flow a document describes, update that folder's ARCHITECTURE.md in the same change.
8. When the code is written and verification is owed, set the feature to `verifying` with `py -3 tools/feature.py set F-NNN --status verifying --next "<the step>"`. When the build, flashing, or the run happens outside this editor, write a checklist for the user under `Waiting on the user` in `## Now`: what to build, what to flash or load, what to do, what output shows success, and what shows failure.
9. When every verification step has passed, propose closing the feature and show the commands and output (or the user's reported result) and the documents you changed. The user confirms before the feature becomes `done`.

{{TEST_RULE}}

## What done means

A feature is done when:

- the behaviour in its `behavior` field has been observed in a run, by the agent or reported by the user
- every step in its `verification` list, if it has one, has passed
- the ARCHITECTURE.md of every folder it changed matches the code
- a `## Log` entry in PROGRESS.md records what was done, how it was verified, and any decision with its reason
- the user has confirmed it

## Other rules

- Generated and vendor code stays as it came. Upgrade it from its source.
- A new source file goes into the build as well as onto disk.
- `feature_list.json` changes through `tools/feature.py`, which validates the file before every write.

## Windows notes

- Run Python as `py -3`. A bare `python` can be the Microsoft Store stub, which exits without running anything.
- Every file in this repository is UTF-8. Pass `encoding="utf-8"` when a script reads or writes text.
