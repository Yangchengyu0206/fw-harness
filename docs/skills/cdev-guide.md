# cdev-guide

User-invoked. Type `/cdev-guide`.

## What it does

Names every other cdev skill and when to reach for it, grouped by what you are doing: setting up, a day of work, looking at code, and keeping the architecture documents true.

## When to reach for it

When you cannot remember which skill fits.

## Common questions

**Why are some skills typed and others not?** A skill the agent can reach on its own keeps a description loaded in every conversation. That is worth paying for a skill the agent needs to find by itself, and not for one only you ever start.

**Does it run the skill it names?** No. It tells you which one, and you run it.

**One difference between the two tools:** the typed skills are marked `disable-model-invocation: true`, which Claude Code honours. Copilot does not document that key for skills, so there an agent may still reach them on its own.

## It is working if

You leave with one skill to run next.
