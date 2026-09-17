# cdev-checkpoint

User-invoked. Type `/cdev-checkpoint`.

## What it does

Writes what the conversation holds into `## Now` in PROGRESS.md: the step in progress, the steps finished, every fact confirmed so far, the hypotheses still open, the next step, and what waits on you. It makes the feature's next step agree, then shows you the result.

## When to reach for it

When the context usage indicator runs high, before you close the editor, or before a long step outside the editor such as a build and flash in a vendor IDE.

## Common questions

**Does the agent not update `## Now` already?** After every step, yes. Facts found in the middle of a step, such as a register value read during debugging, can still live only in the conversation. This collects them.

**Why does a summary lose things?** When the context fills, the tool summarises earlier turns to make room, and details go first. What is written in PROGRESS.md is read again from the file.

**Will `## Now` grow without end?** Facts that only mattered to a finished step move to the `## Log` entry when the feature closes.

## It is working if

A new conversation, reading only `## Now`, takes the next step without asking you what was found.
