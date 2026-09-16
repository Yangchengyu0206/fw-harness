# Third party notices

This project is MIT licensed. The files below adapt material from other MIT licensed projects. Each adapted file also names its source in its own text.

## github/awesome-copilot

https://github.com/github/awesome-copilot, MIT.

| Our file | Adapted from |
|---|---|
| `plugins/fw-c-harness/skills/fw-c-implement/embedded-c-rules.md` | `agents/expert-embedded-c-engineer.agent.md` |
| `plugins/fw-c-harness/skills/fw-c-implement/isr-concurrency.md` | `agents/expert-embedded-c-engineer.agent.md` |
| `plugins/fw-c-harness/skills/fw-c-implement/memory-budget.md` | `agents/expert-embedded-c-engineer.agent.md` |
| `plugins/fw-c-harness/skills/fw-c-implement/module-template.md` | `agents/expert-embedded-c-engineer.agent.md` |
| `plugins/fw-c-harness/skills/fw-misra-deviation/SKILL.md` | the deviation guidance in `agents/expert-embedded-c-engineer.agent.md` |
| `plugins/fw-c-harness/skills/fw-c-debug/SKILL.md` | `agents/debug.agent.md` |
| `plugins/fw-c-harness/skills/fw-c-test-gap/SKILL.md` | `skills/test-gap-audit/SKILL.md` |
| `plugins/fw-c-harness/skills/fw-c-review/report-format.md` | `instructions/code-review-generic.instructions.md` and `skills/security-review/SKILL.md` |

## mattpocock/skills

https://github.com/mattpocock/skills, MIT.

| Our file | Adapted from |
|---|---|
| `plugins/fw-c-harness/skills/fw-c-review/SKILL.md` | the two-axis split in `skills/engineering/code-review` |
| `plugins/fw-c-harness/skills/fw-guide/SKILL.md` | the router pattern in `skills/engineering/ask-matt` |
| The authoring conventions every SKILL.md follows | `skills/productivity/writing-for-agents` |

## Standards referenced, not included

MISRA C:2012 is a copyrighted standard. This project ships no rule text. It refers to rules by number, with our own one line summaries, and the mode is configured in `harness/review-policy.json`.
