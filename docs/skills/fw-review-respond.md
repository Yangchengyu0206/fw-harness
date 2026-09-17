# fw-review-respond

The agent reaches this one on its own.

## What it does

Takes the findings from a review of your change, from a report in `harness/reviews/`, pull request comments, or a message. Before touching code, it checks each finding against the repository and gives it a verdict: accept, decline with evidence, or leave for you to decide. It fixes the accepted ones one at a time with the host tests run after each, appends an Author response table to the report, and drafts the message asking the reviewer to review again.

## When to reach for it

A review of your ticket came back with findings.

## Common questions

**Why not just apply every finding?** A reviewer sees a diff; the code around it may already handle the case, a decision may explain it, or the suggested fix may break a caller the reviewer never saw. Checking first stops a correct design being undone by a plausible comment.

**What if a finding is unclear?** It asks you about the unclear ones before fixing any, because findings often touch the same code and a partial reading leads to the wrong fix.

**Can it mark the review done?** No. The Definition of Done counts only a review recorded by someone other than the assignee. It hands the fixes back, and the reviewer runs `fw-c-review` again.

**A MISRA finding the code has to keep breaking.** That becomes a deviation record through `fw-misra-deviation`, not a code change.

**Does it post pull request replies?** It drafts them. Posting is yours.

## It is working if

Every finding has a row in the Author response table, every decline cites something you can open, each fix is its own small change with the tests run after it, and the ticket's review evidence was left for the reviewer.
