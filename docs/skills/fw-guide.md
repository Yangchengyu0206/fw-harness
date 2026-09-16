# fw-guide

User-invoked. Type `/fw-guide`.

## What it does

Names every other skill and when to reach for it, grouped by what you are doing: setting the repository up, a day of work, looking at code, and getting past a rule.

## When to reach for it

When you cannot remember which skill fits, which is most of the time until the loop becomes habit.

## Common questions

**Why are some skills typed and others not?** A skill the agent can reach on its own carries a description that stays loaded in every conversation. That is worth paying for a skill the agent needs to find by itself, and not worth paying for one only a person ever starts.

**Does it run the skill it names?** No. It tells you which one to run, and you run it.

**One difference between the two tools:** the typed skills are marked `disable-model-invocation: true`, which Claude Code honours. Copilot does not document that key for skills, so there an agent may still reach them on its own.

## It is working if

You leave with one skill to run next.
