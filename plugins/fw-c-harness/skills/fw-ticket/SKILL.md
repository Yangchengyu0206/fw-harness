---
name: fw-ticket
description: Create, claim, move, and add evidence to the tickets in harness/tickets. Use when the user asks for a new ticket, asks to claim or move one, mentions an FW-NNNN id, or when a check run or a review produces evidence that belongs on a ticket.
---

# fw-ticket

`harness/scripts/ticket.py` is the only way state changes. It fills in the identity and the time from git and enforces the transitions, so it is the tool for every write here. Editing a ticket file by hand skips the rules it exists to apply.

## Commands

```bash
py -3 harness/scripts/ticket.py new --title "<title>" --area <area> [--priority N] [--behavior "<what the product does>"] [--step "<verification step>"] [--no-hil]
py -3 harness/scripts/ticket.py claim FW-NNNN
py -3 harness/scripts/ticket.py move FW-NNNN <status>
py -3 harness/scripts/ticket.py block FW-NNNN --reason "<reason>"
py -3 harness/scripts/ticket.py unblock FW-NNNN
py -3 harness/scripts/ticket.py evidence FW-NNNN review --ref <path> --open-critical N
py -3 harness/scripts/ticket.py dod FW-NNNN --add "<debt>" --remove "<debt paid off>"
py -3 harness/scripts/ticket.py show FW-NNNN
```

`check` records its own evidence: `py -3 harness/scripts/check.py --record FW-NNNN`, on a clean working tree.

## Rules this skill follows

- **A new ticket names user visible behaviour.** Write `user_visible_behavior` as what the product does differently, and `verification_steps` as the checks that prove it: one host check, plus one board check when the ticket needs a board.
- **One active ticket per person.** When the user asks for a second one, say which ticket is already active and ask which one they want.
- **`done` belongs to a human.** Run `ticket.py show FW-NNNN` to read what the ticket still owes in `dod_pending`, and leave the transition to the user: `move FW-NNNN done` asks for typed confirmation in a terminal. Say so plainly rather than trying it. `dod` edits that list; it takes at least one `--add` or `--remove`.
- **A blocked ticket carries a reason.** `block` requires one, and unblocking returns the ticket to the status it came from.

**Done when:** the command exits zero, and you have read back the ticket's new status and what it still owes.
