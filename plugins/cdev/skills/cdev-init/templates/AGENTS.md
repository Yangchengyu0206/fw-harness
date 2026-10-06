# {{PROJECT}}

Entry point for any agent working in this repository. Every rule the agent follows is in this file; CLAUDE.md only imports it.

## Domains

Domains: {{DOMAINS}}

The cdev skills read the matching domain reference for each domain listed here before they write, review, or debug code.

## Verification

Verification: {{VERIFICATION}}

- `off`: leave every `verification` list empty (no `--verify`) and write no checklist. A feature closes when it builds and its behaviour looks right in a run or in the code, and its `## Log` entry says plainly what was checked and what was not checked on real hardware.
- `light`: name the one step still owed as the feature's next step, in a line such as `on the board: confirm the retry fires after 3 ms`. No checklist, no evidence files.
- `full`: write the checklist described in step 9 below, keep the logs the user captures under `docs/evidence/F-NNN/`, and ask the user to type `/cdev-target-verify` for each step.

At every level, when the build, flashing, or the run happens outside this editor, the feature waits at `verifying` with one line under `Waiting on the user` in `## Now`: what to build or flash, and what output shows success. `full` expands that line into the checklist.

Change this line as the project moves on, most often from `off` to `light` once the board runs the code.

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

In VS Code, the `SessionStart` hook in `.github/hooks/cdev.json` puts `## Now`, the feature list, and the state of the documents in front of you before your first answer. When that context is there, report it in a few lines and go to step 4.

When it is not there, the hook is off or unsupported, so do it yourself:

1. Read `## Now` in PROGRESS.md.
2. Run `py -3 tools/feature.py show` and `py -3 tools/doc_check.py`.
3. Report in a few lines: the feature in progress, where it stopped, its next step, and any drift `doc_check` found.
4. When the user has not already said what to work on, ask which feature to take. Mark it with `py -3 tools/feature.py set F-NNN --status active` once they answer.

## Answering questions about the code

The architecture documents are a map for finding the code. The code is the source of truth.

1. Read the topic lines in NOTES.md and open the note whose line matches the question. Read the root ARCHITECTURE.md, including `## Terms` where the question uses one of them, and the one in each folder the question touches. Use their `## Files` and `## Flows` to decide what to open. When a folder's document says it is not documented yet, read that folder and write its document first, with cdev-architecture-sync.
2. Verify every claim about behaviour in the code. Read whole functions, follow definitions and callers, and follow interrupt handlers and shared state when the path crosses them.
3. Leave read-only folders out of broad searches. Read vendor code directly when the question turns on it: a HAL call, a register sequence, an SDK driver's locking.
4. Say where each part of the answer came from: verified in the code (with file and function), returned by a named tool, or taken from a document without checking.
5. When a document disagrees with the code, say so and offer the correction.

## Keeping the context small

- Delegate a question that means reading several files to the `cdev-explorer` agent (`.github/agents/cdev-explorer.agent.md`). It reads in its own context and returns the answer with `path:line` citations, so this conversation keeps room for the work. Claude Code does not read `.github/agents/`; use its built-in Explore agent there.
- Search first, then read the function or section the search found.
- Send long build or run output to a file and read the errors and the tail: `<command> > build.log 2>&1`.
- Filter logs and dumps before reading them.

## Using git

Git shows this clone's changes and history. It is not how you read or search the code, and each command costs a turn and often an approval.

- Run it when the task is about a change (`git status`, `git diff` for a review, a wrap-up, or a commit message) or about history (`git log`, `git blame`, `git bisect` when the question is when or why something changed).
- Read and search files with your read and search tools, not `git show`, `git grep`, `git ls-files`, or `git log -p`.
- Another repository, or a branch this clone does not hold, is not reachable with git here: use a code tool, as `## Tools beyond this repository` says. Do not run `git branch -a`, `git fetch`, or `git log --all` to look for one.
- Do not run git to re-check what the session opening or `## Now` already told you.

## Tools beyond this repository

This repository holds one branch of one project. The tools this session carries (MCP servers among them) may reach the rest: other repositories and branches, datasheets, application notes. They answer from sources; your memory of a part or of someone else's code does not. Reach for them first, not after you run out of ideas.

Always take these from a tool when one covers them, before they go into code, a review, or an answer:

- a register address or bit, a timing, an electrical limit, a pin, a recommended sequence, an erratum: from a document tool. With none available, say the value is unverified memory and ask where it should come from.
- how another repository or a branch this clone does not hold does something, or where it is implemented: from a code tool, not from local `git` and not from a guess.

Pick the tool by what the answer is made of, not by the words in the question:

- the answer is code (a file, a function, a repository, a branch, how a driver or firmware does something) → a code tool, even when the question names a chip, a part number, or a register. A name shaped like a repository or a branch is code, even when it begins like a part number.
- the answer is a value or a sentence in a datasheet or an application note → a document tool.
- the answer needs both (how this firmware sets a register, and what the datasheet says it should be) → call both, the code tool first.

Name the tool each part of the answer came from. When the tool you need is not in this session, `py -3 tools/mcp_list.py` shows which servers are configured, so you can tell the user which one to enable. Ask the user only when no tool fits, and say what you looked for.

## Notes that outlive a feature

`## Now` is rewritten as the work moves and `## Log` is read by date, so a fact that will matter after the feature closes is kept by topic: how a tool or a board is set up, a trap, a measured number, a false positive to expect, why an option was ruled out.

1. Write it into `docs/notes/<topic>.md`: a `# <topic>` title, a `Last checked: <date>` line, the facts, then `**Why:**` it matters and `**How to apply:**` it. When a note on the topic exists, update it and its date rather than starting a second.
2. Add or update its line under `## Topics` in NOTES.md: `- [<topic>](docs/notes/<topic>.md): <when it matters>`. The line is what the next conversation sees, so say when to open the note.
3. Write only what is true for anyone who clones this repository. A path on one person's machine, a network one machine cannot reach, credentials, and a personal preference stay out: leave them to your own memory if this tool keeps one, or tell the user what you left out.
4. A rule that must hold every time, such as a command never to run here, also goes under `Ask before` in `## Where to work`, which every conversation reads.
5. A choice made with a reason goes in `## Decisions and why` in the root ARCHITECTURE.md; a note holds facts.
6. When a note turns out wrong, correct it or delete it and its line. Do not append a contradiction below it.

## Working on a feature

1. One active feature at a time.
2. {{FIRST_STEP}}
3. Build: {{BUILD}}
4. Test: {{TEST}}
5. Run: {{RUN}}
6. After each step, rewrite `## Now` in PROGRESS.md: what is done, the facts confirmed so far, and the next step. Write a confirmed fact (an address, a timing, a call order) there the moment it is confirmed; a long conversation gets summarised and loses details that live only in chat.
7. Before the first change inside a folder whose document says it is not documented yet, write that document with cdev-architecture-sync.
8. When a change adds, removes, or renames a file, changes what a folder depends on, or changes a flow a document describes, update that folder's ARCHITECTURE.md in the same change.
9. When the code is written and a step is still owed, set the feature to `verifying` with `py -3 tools/feature.py set F-NNN --status verifying --next "<the step>"`, as far as the `Verification:` section above asks. Under `full`, write the checklist under `Waiting on the user` in `## Now`: what to build, what to flash or load, what to do, what output shows success, and what shows failure.
10. Propose closing the feature against `## What done means`, with the commands and output (or the user's reported result) and the documents you changed. Under `off`, say what has not been checked on real hardware. The user confirms before the feature becomes `done`; for the full wrap-up, suggest they type `/cdev-done`.

{{TEST_RULE}}

## What done means

A feature is done when:

- the behaviour in its `behavior` field has been observed, in a run by the agent, in a result the user reports, or under `off` in the code and the build
- every step in its `verification` list, if it has one, has passed
- the ARCHITECTURE.md of every folder it changed matches the code
- a fact it confirmed that will matter later is in a note
- a `## Log` entry in PROGRESS.md records what was done, how it was verified, and any decision with its reason
- the user has confirmed it

## Other rules

- A new source file goes into the build as well as onto disk.
- `feature_list.json` changes through `tools/feature.py`, which validates the file before every write.

## Running Python

- On Windows, run Python as `py -3`. A bare `python` can be the Microsoft Store stub, which exits without running anything. On macOS and Linux, use `python3` wherever this file says `py -3`.
