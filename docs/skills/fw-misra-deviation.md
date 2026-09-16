# fw-misra-deviation

The agent reaches this one on its own.

## What it does

Writes a deviation record under `docs/deviations/`: the rule and its classification, why it cannot be met here, the risk that creates, the exact scope it covers, what limits the risk, and an approver.

## When to reach for it

When a required MISRA rule cannot be met and the code needs to keep doing what it does.

## Common questions

**Do I need a record in advisory mode?** Usually not. In `advisory` a MISRA finding never blocks a merge, so the skill says so and stops unless you want the record anyway.

**Why does it argue with me first?** A deviation is the answer when the rule cannot be met, not when meeting it is inconvenient. You see the compliant alternative and its cost before deciding.

**Why can I not approve my own deviation?** The approver is the second pair of eyes on a risk you accepted. Signing your own leaves the risk unreviewed.

## It is working if

The record names exact files rather than a whole module, states a real risk, and carries another person's name under Approver.
