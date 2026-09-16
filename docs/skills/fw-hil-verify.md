# fw-hil-verify

User-invoked. Type `/fw-hil-verify`.

## What it does

Walks the board verification a ticket still owes: reads what the ticket asks for, hands you the flash and serial commands, stores the capture under `harness/evidence/`, and records `hil` evidence against the ticket.

## When to reach for it

When a ticket sits in `verifying` with a board step left in `dod_pending`.

## Common questions

**Who flashes the board?** You do. The skill supplies the commands and keeps the evidence; it never claims a board result it did not see.

**Where does the log go?** `harness/evidence/FW-NNNN/<step>-<date>.log`, committed with the ticket, so a reviewer months later can open the same capture.

**What happens to `dod_pending`?** The step you just paid off is removed, and the skill tells you what the ticket still owes.

## It is working if

The ticket carries a log a reader can open, and the board debt it named is gone.
