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
| `plugins/fw-c-harness/skills/fw-c-debug/SKILL.md` | the defect record in `skills/bug-reproduction-brief/SKILL.md` and the stopping rule in `agents/gem-debugger.agent.md` |
| `plugins/fw-c-harness/skills/fw-c-test-gap/SKILL.md` | `skills/test-gap-audit/SKILL.md` |
| `plugins/fw-c-harness/skills/fw-c-review/SKILL.md` | the self-verification pass in `skills/security-review/SKILL.md` and the caller check in `agents/gem-reviewer.agent.md` |
| `plugins/fw-c-harness/skills/fw-c-review/report-format.md` | `instructions/code-review-generic.instructions.md` and `skills/security-review/SKILL.md` |
| `plugins/cdev/skills/cdev-implement/references/firmware.md` | `agents/expert-embedded-c-engineer.agent.md` |
| `plugins/cdev/skills/cdev-debug/SKILL.md` | the defect record in `skills/bug-reproduction-brief/SKILL.md` and the stopping rule in `agents/gem-debugger.agent.md` |
| `plugins/cdev/skills/cdev-test-gap/SKILL.md` | `skills/test-gap-audit/SKILL.md` |
| `plugins/cdev/skills/cdev-review/SKILL.md` | the self-verification pass in `skills/security-review/SKILL.md` and the caller check in `agents/gem-reviewer.agent.md` |
| `plugins/cdev/skills/cdev-review/report-format.md` | `instructions/code-review-generic.instructions.md` and `skills/security-review/SKILL.md` |

## mattpocock/skills

https://github.com/mattpocock/skills, MIT.

| Our file | Adapted from |
|---|---|
| `plugins/fw-c-harness/skills/fw-c-review/SKILL.md` and `report-format.md` | the two-axis split and the judgement-call baseline in `skills/engineering/code-review` |
| `plugins/fw-c-harness/skills/fw-c-debug/SKILL.md` | the diagnosis phases in `skills/engineering/diagnosing-bugs` |
| `plugins/fw-c-harness/skills/fw-c-debug/scripts/hitl_loop.py` | `skills/engineering/diagnosing-bugs/scripts/hitl-loop.template.sh`, rewritten in Python |
| `plugins/fw-c-harness/skills/fw-guide/SKILL.md` | the router pattern in `skills/engineering/ask-matt` |
| `plugins/cdev/skills/cdev-review/SKILL.md` and `report-format.md` | the two-axis split and the judgement-call baseline in `skills/engineering/code-review` |
| `plugins/cdev/skills/cdev-debug/SKILL.md` | the diagnosis phases in `skills/engineering/diagnosing-bugs` |
| `plugins/cdev/skills/cdev-debug/scripts/hitl_loop.py` | `skills/engineering/diagnosing-bugs/scripts/hitl-loop.template.sh`, rewritten in Python |
| `plugins/cdev/skills/cdev-guide/SKILL.md` | the router pattern in `skills/engineering/ask-matt` |
| The authoring conventions every SKILL.md follows | `skills/productivity/writing-for-agents` |

## obra/superpowers

https://github.com/obra/superpowers, MIT.

| Our file | Adapted from |
|---|---|
| `plugins/fw-c-harness/skills/fw-review-respond/SKILL.md` | `skills/receiving-code-review` |
| `plugins/fw-c-harness/skills/fw-c-debug/SKILL.md` | the comparison with working code, the trace back to the source, and the three-fix limit in `skills/systematic-debugging` |
| `plugins/cdev/skills/cdev-debug/SKILL.md` | the comparison with working code, the trace back to the source, and the three-fix limit in `skills/systematic-debugging` |

## Standards referenced, not included

MISRA C:2012 is a copyrighted standard. This project ships no rule text. It refers to rules by number, with our own one line summaries, and the mode is configured in `harness/review-policy.json`.
