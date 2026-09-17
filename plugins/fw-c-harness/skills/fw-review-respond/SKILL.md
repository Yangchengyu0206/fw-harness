---
name: fw-review-respond
description: Work through review findings on your own change. Check each one against the code, then fix it, decline it with evidence, or raise it with the user, and hand the result back for re-review. Use when a report in harness/reviews covers the user's ticket, when the user pastes review or pull request comments, or asks to address, fix, or answer review findings.
---

# fw-review-respond

Adapted from `skills/receiving-code-review` in [obra/superpowers](https://github.com/obra/superpowers) (MIT).

A finding is a claim about the code, not an order. The reviewer saw a diff; you can see the whole repository, the board, and the decisions behind the code. So every finding gets checked before anything changes, and the answer to each is a fix or a reason, never agreement for its own sake.

The author closes nothing on the ticket. `harness/review-policy.json` forbids self-review, and the Definition of Done reads only the latest review by someone other than the assignee. What this skill produces is a change set and a written answer for the reviewer, who then records the review that counts.

## Process

### 1. Collect the findings

Take them from where they arrived: the newest report for the ticket in `harness/reviews/`, pull request comments, or the user's message. Number them in one list, keeping each finding's severity, its `path:line`, and its words.

**Done when:** every finding is on one numbered list with its severity and location.

### 2. Understand all of them before changing any

Restate each finding in one sentence of your own. When one is unclear, ask about it before implementing anything, including the clear ones: findings often touch the same code, and a partial reading produces a wrong fix.

**Done when:** you can restate every finding, or the user has answered your questions about the ones you could not.

### 3. Check each finding against the code

For each, answer:

- **Is it true here?** Re-read the cited line and the path that reaches it. A check earlier on the path, a bound the caller guarantees, or a `volatile` already present makes it false.
- **Would the suggested fix break something?** Its callers (`git grep -n -w <name>`), the other build targets, the host tests, timing on the board.
- **Is there a reason the code is this way?** `git log -L <start>,<end>:<file>`, a record in `docs/deviations/`, the folder's ARCHITECTURE.md, the decisions table in CLAUDE.md.
- **Is it asking for something nothing uses?** When a finding asks to build out a feature properly, search for its users first. With none, the better answer may be to remove it.

Give each a verdict: **accept**, **decline** with the evidence, or **for the user** when it conflicts with a decision they made or you cannot settle it from the code. Show the user the table of verdicts. Start on the accepted ones; wait for the user's word on the rest.

**Done when:** every finding has a verdict, each decline cites the line, commit, or document that supports it, and the user has seen the table.

### 4. Fix the accepted findings one at a time

Order them: critical first, then the quick ones, then the ones that change logic. For each:

1. When the finding is a defect, write the Unity test that shows it before the fix, as `fw-c-implement` does.
2. Make the smallest change that answers this finding and nothing else. A cleanup you noticed on the way is a separate finding or a separate ticket.
3. Run the host tests before moving to the next finding.

When a required MISRA rule must stay broken, the answer is a deviation record through `fw-misra-deviation`, not a code change. When a fix turns out bigger than the ticket, stop and ask whether it belongs on a new ticket through `fw-ticket`.

After the last one:

```bash
py -3 harness/scripts/check.py
```

**Done when:** every accepted finding has its change, the host tests passed after each, and every gate passes.

### 5. Write the answer into the report

Append this to the review report, below the reviewer's summary:

```markdown
## Author response

| # | Finding | Decision | Where | Reason |
|---|---|---|---|---|
| 1 | Critical: unprotected read of rx_head | fixed | `src/drivers/uart.c:88`, commit abc1234 | |
| 2 | Suggestion: extract the retry loop | declined | | only one caller; `git grep -n -w uart_retry` finds none elsewhere |
| 3 | Important: timeout magic number | for the user | | CLAUDE.md fixes 50 ms by decision on 2026-08-02 |
```

State what changed or why not, in technical terms. Leave out thanks and praise; the change is the acknowledgement. When the findings came from pull request comments, draft one reply per comment thread in the same terms, and leave posting them to the user.

**Done when:** every finding has a row, and every `fixed` row names a location a reviewer can open.

### 6. Hand it back for re-review

Leave the ticket's `review` evidence alone: evidence recorded by the assignee counts as self-review and holds the ticket back. Draft a short message for the user to send the reviewer: the ticket, the new range, the fixed findings, and the declined ones with their reasons. The reviewer runs `fw-c-review` again and records the evidence.

**Done when:** the user has the message, and you have told them which findings still wait on their decision.
