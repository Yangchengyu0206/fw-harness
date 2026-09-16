# fw-c-implement

The agent reaches this one on its own.

## What it does

Runs the test-first loop for a ticket: read the ticket and the module's ARCHITECTURE.md, write a Unity test and watch it fail, implement the smallest change that passes, run all seven gates, and record the evidence on the ticket.

## When to reach for it

Whenever you are writing or changing C for a ticket.

## Common questions

**Why must the test fail first?** A test written after the code usually tests what the code does rather than what the ticket asked for. Watching it fail is the cheapest proof it tests anything at all.

**The include I need crosses a layer.** That is a design question, not a formality. The skill brings it back to you rather than adding a grandfather entry to make the gate quiet.

**Where are the C rules?** Four reference files beside the skill: general rules, interrupts and shared state, the memory budget, and a skeleton for a new module. It reads the ones your change actually needs.

## It is working if

A test that failed first now passes, all seven gates pass, and the ticket carries a `check` entry for the commit.
