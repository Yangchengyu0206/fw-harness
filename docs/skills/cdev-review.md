# cdev-review

The agent reaches this one on its own.

## What it does

Reviews a diff along two axes in two separate sub-agents: Standards, against the review checklist of every domain the repository belongs to, and Spec, against what the feature asked for. It verifies each finding against the code and writes the report into `docs/reviews/`.

## When to reach for it

Before merging, and whenever you want a second look at your own changes.

## Common questions

**Is reviewing my own work worth anything?** Yes, with one change of emphasis. There is no second person, so every finding is re-read against the code before it is reported, and the checklists come from the domain references rather than from memory.

**Why keep the two axes apart?** Code can follow every rule and build the wrong thing, or build exactly the right thing and break the rules. Merging the lists lets one hide the other.

**Will it fix what it finds?** It proposes patches and leaves applying them to you.

## It is working if

The counts in the report match its findings, every finding names a line you can open, and every critical finding has a proposed fix.
