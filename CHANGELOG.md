# Changelog

## cdev 0.5.0

What the first trial runs showed. A repository set up by 0.4.0 picks this up with `/cdev-upgrade`.

### Added

- **`tools/value_check.py`**, the fifth script: hardware values (`#define NAME 0x..`, enum members `NAME = 0x..`) added since the last commit with no source marker on their line or the comment above. The stop hook reports them every turn. In a trial with a small model, every run asked to add a register setting invented the address (four runs, four different addresses), with or without the rule in AGENTS.md; a rule alone did not hold, so this makes it a check.
- **`## Hardware values are never written from memory`** at the top of AGENTS.md: cite the source beside the value, or write the code anyway and mark the value `/* UNVERIFIED: <what to look up> */`, and name it in the reply.
- **Submodules are no longer vendor code.** A trial repository's most edited code (its algorithm) was a submodule that `cdev-init` locked read-only and left undocumented. Now each submodule gets a row in the root map and is one of three kinds the user picks: edited a lot (documented inside it like any folder), edited now and then (documented inside it when the work first reaches a folder), or only used (a map row only). `doc_check` reads the files of checked-out submodules, so documents inside one are checked like any other, and reports a submodule the map does not mention. `value_check` checks values added inside submodules too. AGENTS.md says to commit inside a submodule on its branch, not a detached HEAD, before updating its pointer.

- **A personal harness by default.** `tools/personal.py`, the sixth script, adds every `.md` file (in the repository and in each submodule) and the harness's other files to `.git/info/exclude`, which is never committed or pushed, so trying cdev on a team's repository changes nothing anyone else sees. AGENTS.md carries `Sharing: personal`; `team` is one word and a commit away. `doc_check` still reads the excluded documents.

### Changed

- `Ask before` in AGENTS.md lists `git commit`, unless the user asked for one. In the trial, three of four runs committed without being asked.
- cdev-implement, cdev-review, and cdev-done run `value_check` and handle what it lists.

## cdev 0.4.0

A repository set up by 0.2.0 picks all of this up with `/cdev-upgrade`. There was no 0.3.0 release; its changes are folded in here.

### Added

- **Notes that outlive a feature.** `## Now` is rewritten and `## Log` is read by date, so facts that matter later (a tool's setup, a trap, a measured number, a false positive to expect) now go into `docs/notes/<topic>.md`, one per topic with why it matters and how to apply it, indexed one line each in NOTES.md. The session hook hands the agent the index; answering, the explorer agent, and `/cdev-grill` consult it; `/cdev-done` and `/cdev-checkpoint` ask which facts outlive the feature; `doc_check` reports a note without a line and a line without a note. Only facts true for anyone who clones the repository are written: one machine's paths, networks, and credentials stay out, left to the tool's own memory.
- **The session opens itself.** `.github/hooks/cdev.json` and `tools/hooks.py` put `## Now`, the feature list, and the document check in front of the agent at the start of a VS Code session, and report document drift the session added when it stops. Hooks are a VS Code preview; where they do not run, the rule in AGENTS.md does the opening.
- **`cdev-explorer`**, a read-only agent (read and search tools only) that reads code in its own context and returns the answer with `path:line` citations.
- **`/cdev-grill`**, an interview before the work that records each decision with its reason. Adapted from mattpocock/skills.
- **Tools first.** `## Tools beyond this repository` in AGENTS.md has the agent take hardware values (registers, timings, limits, sequences, errata) from a document tool and other repositories' code from a code tool before they go into code, a review, or an answer, instead of from memory. It picks the tool by what the answer is made of, so a question about code goes to a code tool even when it names a chip. cdev-implement, cdev-debug, and cdev-review each check hardware values against their source, and the session hook names the configured MCP servers.
- **`## Using git`** in AGENTS.md: git is for changes and history, not for reading or searching code, and never for finding another repository or a branch this clone does not hold. cdev-review finds callers with the search tool instead of `git grep`.
- `tools/mcp_list.py` lists the servers configured for this repository and this machine, including VS Code `settings.json`, `~/.claude.json` and its per-project entries, and files with comments or trailing commas; a file it cannot read is reported rather than counted as empty.
- **`## Terms`** in the root ARCHITECTURE.md, for the words this project reads differently.
- **TESTING.md** and TESTING.zh-TW.md for the first people trying cdev.
- A CHANGELOG.

### Fixed

- `.vscode/settings.json`: the rule that holds destructive `git` commands was invalid JSON (single backslashes), so it never applied, and it could not match `git checkout -- <file>`. `/cdev-upgrade` replaces the old rule.
- `tools/hooks.py` waited on stdin when run by hand, which hung the last check of `/cdev-init` and `/cdev-upgrade`. It no longer reads stdin and always exits 0; exit code 2 would make VS Code treat the hook as a blocking error.
- The session hook reported an invalid `feature_list.json` as "no features". It now says the features are unknown and how to fix the file.
- A PROGRESS.md that was not UTF-8 replaced the whole opening with an error; each section now fails on its own.
- `feature.py`, `doc_check.py`, and `hooks.py` accept files with a UTF-8 byte order mark, as Notepad and PowerShell write them.
- `doc_check.py`: map links to folders with spaces (`<my dir/ARCHITECTURE.md>`, `my%20dir/…`, `./…`) count; a file named like `foo[1].c` is not read as a glob; a heading with a trailing space is found; a machine without `git` on PATH falls back to walking the tree.
- The Stop hook no longer repeats drift that was there before the session started.
- `Verification: off` and a build in a vendor IDE no longer contradict each other: at every level, work that runs outside the editor waits at `verifying` with one line saying what to build or flash and what output shows success.
- Skills no longer tell the agent to start `cdev-target-verify` or `cdev-done`, which only you can start; they ask you to type the command.
- `cdev-session-start` proposes a `backlog` feature when nothing is `next`.
- Under `Verification: off`, no skill adds `--verify` steps.
- `cdev-upgrade` refreshes sentences an older version wrote inside sections that already exist (the hook-aware opening, the `## Terms` pointer, the explorer delegation), instead of only checking that the sections exist.
- `cdev-init` keeps the harness's own folders out of domain detection, and links every folder from the root map, which `doc_check` requires.
- The offline installer prints `chat.plugins.enabled: true` with the plugin location, since plugins stay off without it, and says which skill folders a re-run replaced or no longer ships.

### Documentation

- INSTALL: fourteen skills, `/cdev-grill` in the command table, the hook-based opening, Python on macOS and Linux, and troubleshooting for the hook.
- AGENTS.md says `python3` replaces `py -3` on macOS and Linux, and that Claude Code uses its own Explore agent.
- Known limits now name the VS Code issue where the Copilot agent harness ignores a workspace's terminal approval rules.

## cdev 0.2.0

Copilot first, verification levels starting at `off`, an offline package, `/cdev-upgrade`, and stub documents for large repositories.

## fw-c-harness 0.1.0

First preview.
