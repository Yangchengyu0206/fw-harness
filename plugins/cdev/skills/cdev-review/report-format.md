# Review report format

The severity language is adapted from `instructions/code-review-generic.instructions.md` and the self-verification pass from `skills/security-review/SKILL.md`, both in [github/awesome-copilot](https://github.com/github/awesome-copilot) (MIT). The two-axis structure is adapted from `code-review` in [mattpocock/skills](https://github.com/mattpocock/skills) (MIT).

Write the report to `docs/reviews/<YYYY-MM-DD>_F-NNN.md`.

```markdown
# Review F-NNN

- Feature: F-NNN, <title>
- Range: `git diff <fixed-point>...HEAD`
- Domains: <the Domains line from AGENTS.md>

| Severity | Standards | Spec |
|---|---|---|
| Critical | 0 | 0 |
| Important | 0 | 0 |
| Suggestion | 0 | 0 |

## Standards

### Critical: <one line naming the problem>

- Where: `src/drivers/uart.c:88`
- Checklist item: <the item from the domain reference, and which domain>
- Problem: <what the code does>
- Why it matters: <what happens when it runs>
- Suggested fix: <the change, as a patch>
- Confidence: high

## Spec

### Important: <requirement missing or partial>

- Feature line: "<quoted from behavior or verification>"
- What the diff does: <what is there now>
- Suggested fix: <what would deliver it>
- Confidence: medium

## Summary

- Standards: <n> findings, worst: <severity>
- Spec: <n> findings, worst: <severity>
- Critical findings still open: <list, or "none">
```

Rules this format carries:

- The counts table comes first, so a reader sees the shape before the detail.
- Every finding has a `path:line` a reader can open, and the cited line literally contains the thing named.
- Each axis keeps its own worst finding. Pick no single winner across the two.
- Patches are proposed, and the author applies them.
