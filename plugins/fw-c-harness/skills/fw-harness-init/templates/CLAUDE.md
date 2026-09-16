# CLAUDE.md

The handbook for this repository. [AGENTS.md](AGENTS.md) is the short entry point; this file holds the rules and the reasons behind them.

## 1. Session start

1. Confirm where you are and who you are: the repository path, the branch, and `git config user.name` and `user.email`.
2. Run `sh init.sh` (PowerShell: `.\init.ps1`). It verifies Python, identity, hooks, the harness layout, and the toolchain, then runs `check` once.
3. Read your own handoff: `harness/handoff/<your-slug>.md`.
4. Read the last few progress notes in `harness/progress/` and the recent `git log`.
5. List candidate tickets: `py -3 harness/scripts/ticket.py show FW-NNNN` for your active ticket, then the `next` queue in `feature_list.json`.
6. Confirm the ticket with a human before writing code.

## 2. Working rules

- One `active` ticket per person. Claiming a second one fails.
- Run `check` on the merged tree before merging, not only on your own branch.
- A new C file goes into the CMake target as well as onto disk. A file that compiles only on your machine is not built.
- Leave compiler flags as they are. If a warning needs a flag change, raise it as a ticket.
- Fix the cause of a `cppcheck` finding. `harness/cppcheck-suppressions.txt` may only shrink.
- Run every command from the repository root, so relative paths in `harness/config.json` resolve.

## 3. Definition of Done

A ticket reaches `done` when all of these hold:

- `dod_pending` is empty.
- A `check` evidence entry passed on a commit that is HEAD or an ancestor of HEAD.
- When `requires_hil` is true, a `hil` evidence entry points at a captured log under `harness/evidence/`.
- The latest `review` evidence is by someone other than the assignee, with `open_critical` at zero.
- A human types the ticket ID in a terminal to confirm. `ticket.py move <id> done` needs a real terminal, which an agent shell usually does not have.

"Written" and "done" are different states. When the code is written and `check` passes but board verification or review is still owed, the ticket stays in `verifying` with the debt listed in `dod_pending`.

The limit of this design: `ticket_check` can prove that a `done` ticket carries HIL evidence and a review by another person, and it cannot prove a human produced that evidence. Pull request review is the final safeguard.

## 4. Why the gates look like this

| Gate | Why |
|---|---|
| `clang-format` on changed files only | Formatting the whole tree buries real changes in a reformatting diff. |
| `cppcheck` with a shrinking suppression list | A suppression is a debt. Recording it is fine; growing the list quietly is not. |
| `arch_check` | An include that crosses a layer is cheap to add and expensive to undo. The graph is checked on every run. |
| `ticket_check` | State files are edited by several people. The gate catches a ticket that says `done` without evidence. |
| Cross build with `-Wall -Wextra -Werror` | A warning on an embedded target is usually a real defect. |
| Host Unity tests | Logic that can run on the host should be tested without a board. |
| Size budget | Flash and RAM run out late and all at once. The budget turns that into a failing check. |
| Commit evidence derived from `git log` | Writing evidence into ticket files from a hook dirties the working tree and causes merge conflicts. |
| One file per ticket | Two people adding tickets in parallel get an add/add conflict git can show, instead of a silent overwrite. |

## 5. Incidents that became rules

Record what went wrong, so the rule keeps its reason.

| Date | What happened | The rule it produced |
|---|---|---|
| | | |
