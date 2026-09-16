# fw-ticket

The agent reaches this one on its own.

## What it does

Creates, claims, moves, blocks, and adds evidence to the tickets in `harness/tickets/`, always through `harness/scripts/ticket.py`, which fills in who you are and what time it is from git and enforces the transition rules.

## When to reach for it

Whenever ticket state changes. In practice the other skills reach it for you, and you type it only when you want a specific write.

## Common questions

**Why can an agent not mark a ticket `done`?** The last transition needs a typed confirmation in a real terminal, which an agent's shell usually is not. The gate can prove a `done` ticket carries HIL evidence and a review by someone else; it cannot prove a person produced them. That last step is yours.

**Why not edit the JSON directly?** The identity, the timestamp, the history entry, and the transition rules all come from the script. Hand edits skip the rules the file exists to record.

**Two of us created the same ticket id.** One file per ticket means git reports an add/add conflict instead of losing one. Run `ticket.py collisions` before merging, and `renumber` to free the id.

## It is working if

The ticket's status and evidence match what actually happened, and every entry names the person who made it.
