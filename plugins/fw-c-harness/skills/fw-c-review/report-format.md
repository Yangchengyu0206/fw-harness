# Review report format

The severity language is adapted from `instructions/code-review-generic.instructions.md` and the self-verification pass from `skills/security-review/SKILL.md`, both in [github/awesome-copilot](https://github.com/github/awesome-copilot) (MIT). The two-axis structure and the rule-or-judgement label are adapted from `code-review` in [mattpocock/skills](https://github.com/mattpocock/skills) (MIT).

Write the report to `harness/reviews/FW-NNNN_<reviewer-slug>_<YYYY-MM-DD>.md`.

```markdown
# Review FW-NNNN

- Reviewer: <name> <email>
- Ticket: FW-NNNN, <title>
- Range: `git diff <fixed-point>...HEAD`, <how the fixed point was chosen>
- MISRA mode: <off|advisory|required>
- Left to the gates: <the checks harness/config.json already runs>
- Interfaces changed: <names, each with the number of callers checked, or "none">

| Severity | Standards | Spec |
|---|---|---|
| Critical | 0 | 0 |
| Important | 0 | 0 |
| Suggestion | 0 | 0 |

## Standards

### Critical: <one line naming the problem>

- Where: `src/drivers/uart.c:88`
- Kind: rule, <the checklist item, layering rule, or MISRA rule>
- Problem: <what the code does>
- Why it matters: <what happens on the device>
- Suggested fix: <the change, as a patch a human applies>
- Confidence: high

### Suggestion: <one line naming the judgement call>

- Where: `src/app/scheduler.c:40`
- Kind: judgement, <speculative generality, duplicated logic, bare number, shotgun surgery, or mysterious name>
- Problem: <what the code does>
- Suggested fix: <the change>
- Confidence: medium

## Spec

### Important: <requirement missing or partial>

- Ticket line: "<quoted from user_visible_behavior or verification_steps>"
- What the diff does: <what is there now>
- Suggested fix: <what would deliver it>
- Confidence: medium

## Summary

- Standards: <n> findings (<rules> rule, <judgements> judgement), worst: <severity>
- Spec: <n> findings, worst: <severity>
- Blocking: <the critical findings, or "none">
```

Rules this format carries:

- The counts table comes first, so a reader sees the shape before the detail.
- Every finding has a `path:line` a reader can open, and the cited line literally contains the thing named. A broken caller is cited at the caller.
- A judgement call is never above Suggestion, and a documented rule always overrides it.
- Nothing the gates already enforce appears as a finding.
- Each axis keeps its own worst finding. Pick no single winner across the two.
- Patches are proposed, and the author applies them.
