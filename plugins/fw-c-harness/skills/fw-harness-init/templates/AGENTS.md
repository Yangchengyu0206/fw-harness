# AGENTS.md

Entry point for everyone working in this repository, human or agent. Read this file first, then [CLAUDE.md](CLAUDE.md).

## Where to work

- Edit code in folders marked `owned` in `harness/architecture.json`.
- Folders marked `vendor` or `generated` are read-only. Their ARCHITECTURE.md says where the code comes from and how to upgrade it.
- Every folder holding C sources has an ARCHITECTURE.md. Read the one next to the code before changing that code.

## Guardrails

Ask a human before any of these:

- `git clean`, `git push`, `git commit --no-verify`, force pushes, and history rewrites
- editing linker scripts, startup files, or compiler flags
- editing approved rules in `harness/architecture.json`
- adding a line to `harness/cppcheck-suppressions.txt` or to the grandfather list, because both lists may only shrink
- moving a ticket to `done`

## The loop

1. Verify the environment: `sh init.sh`, or `.\init.ps1` in PowerShell. It checks and installs nothing.
2. Claim one ticket: `py -3 harness/scripts/ticket.py claim FW-NNNN`. One active ticket per person.
3. Write a failing test, implement, and run `py -3 harness/scripts/check.py` until every step passes.
4. Record evidence on a clean working tree: `py -3 harness/scripts/check.py --record FW-NNNN`.
5. Wrap up with the `fw-done` skill: handoff, progress note, and a commit message naming the ticket.

## Identity

Every state change records `git config user.name` and `user.email`, so set both before your first commit. No command takes someone else's identity.

## Windows notes

- Run Python as `py -3`. A bare `python` can be the Microsoft Store stub, which exits without running anything.
- Console code pages such as cp950 cannot print every character. The scripts force UTF-8 on their own output, and every file in the repository is UTF-8.
- The git hooks are POSIX shell scripts. Git for Windows ships the shell they need, so they run the same from PowerShell, cmd, and Git Bash.

The full handbook, including the Definition of Done, is [CLAUDE.md](CLAUDE.md).
