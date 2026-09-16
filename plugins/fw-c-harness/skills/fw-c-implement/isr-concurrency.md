# Interrupts and shared state

Adapted from `agents/expert-embedded-c-engineer.agent.md` in [github/awesome-copilot](https://github.com/github/awesome-copilot) (MIT).

Read this when the change adds or edits an interrupt handler, or touches a variable a handler writes.

## volatile

- Any variable written by a handler and read by the main loop is `volatile`, and so is every hardware register. Without it the compiler may cache the value in a register, and the loop reads a stale copy for ever.
- `volatile` orders nothing and makes nothing atomic. It only stops the compiler from optimising the access away.

## Sharing state with a handler

- A value wider than the target's atomic word is read and written under a critical section, or a reader can see half of the old value and half of the new one.
- Keep the critical section to the shortest sequence that must not be interrupted: copy the shared value out, then work on the copy outside the section.
- A single-producer, single-consumer ring buffer with one index owned by the handler and the other owned by the main loop needs no critical section. Write in a comment which side owns which index, because the design is safe only while that stays true.

## What a handler does not do

- Set a flag or push to a queue, and let the main loop do the rest. Long work belongs outside the handler.
- Keep it free of blocking calls, busy waits on another peripheral, and allocation.
- Use a logger inside a handler only when the team has a handler-safe one and its ARCHITECTURE.md says so.

## Review anchors

The critical findings a reviewer looks for here are shared state with no protection, a missing `volatile`, and work inside a handler that belongs in the main loop. They live in `harness/review-checklist.json`, which is the list `fw-c-review` applies.
