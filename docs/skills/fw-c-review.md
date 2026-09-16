# fw-c-review

The agent reaches this one on its own.

## What it does

Reviews the diff along two axes in two separate sub-agents: Standards, against the checklist, the approved layering, and the MISRA mode; and Spec, against what the ticket actually asked for. It verifies each finding, writes the report into `harness/reviews/`, and records `review` evidence with the count of critical findings still open.

## When to reach for it

Before merging, and whenever someone asks for a review.

## Common questions

**Why keep the axes apart?** Code can follow every standard and implement the wrong thing, or deliver exactly the ticket while breaking the project's conventions. Merging the two lists lets one hide the other.

**Does reviewing my own work count?** Not at the Definition of Done. The gate counts only the latest review by someone other than the assignee, with no critical findings open.

**Will it fix what it finds?** It proposes patches and leaves applying them to a person.

## It is working if

The counts in the report's table match the findings below it, each finding names a line you can open, and the two axes are still separate.
