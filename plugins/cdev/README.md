# cdev

A markdown-first harness for one developer working in C and Python, for Claude Code and GitHub Copilot.

It gives an agent what it needs to know where it is and what to do next, and gives the code the domain rules general coding skills do not carry: firmware, Linux drivers, Windows drivers, plain C, and Python.

## Install

Adding a marketplace and installing a plugin are two steps.

**Claude Code**, from inside a session:

```
/plugin marketplace add Yangchengyu0206/fw-harness
/plugin install cdev@fw-harness
```

Or as one line in a shell:

```bash
claude plugin marketplace add Yangchengyu0206/fw-harness && claude plugin install cdev@fw-harness
```

**Copilot CLI**

```bash
copilot plugin marketplace add Yangchengyu0206/fw-harness
copilot plugin install cdev@fw-harness
```

Then, in your repository, run `cdev-init` once.

## What lands in your repository

```
AGENTS.md            entry point: domains, where to work, guardrails, the loop
CLAUDE.md            working rules, what done means, decisions and why
ARCHITECTURE.md      the map of the repository
<folder>/ARCHITECTURE.md
PROGRESS.md          where you are now, then a dated log
feature_list.json    what is being built, the single source of truth
tools/feature.py     keeps feature_list.json valid
docs/reviews/        review reports
```

`tools/feature.py` is the only script. Everything else is Markdown, and nothing blocks a commit.

## Tests are optional

A repository with no tests is a normal case, not a gap to fill. `cdev-init` then writes `Test: none` into AGENTS.md, and the skills add no test framework unless you ask. What they still do is run each change on a real input and show you the command and its output, because an agent that did not run its change is only guessing that it works. A feature's `verification` list is optional too, and `cdev-target-verify` matters only for firmware and drivers.

## The skills

Setting up: `cdev-init`.
A day of work: `cdev-session-start`, `cdev-implement`, `cdev-target-verify`, `cdev-done`, with `cdev-feature` underneath.
Looking at code: `cdev-review`, `cdev-test-gap`, `cdev-debug`.
When the structure changes: `cdev-architecture-sync`.
Router: `cdev-guide`.

One page per skill lives in [docs/skills](../../docs/skills).

## Domains

`cdev-init` detects which domains a repository belongs to, and a repository can belong to several. The implement, review, test-gap, and debug skills read one reference per domain from `skills/cdev-implement/references/`: rules, a review checklist, debugging anchors, and build and test commands.

## One difference between the two tools

Five of the skills are meant for you to type: `cdev-init`, `cdev-session-start`, `cdev-target-verify`, `cdev-done`, and `cdev-guide`. They carry `disable-model-invocation: true`, which Claude Code honours by keeping the agent from firing them. Copilot does not document that key for skills, so on Copilot an agent can still reach them on its own.

## How it differs from fw-c-harness

`fw-c-harness`, in the same marketplace, is for a firmware team: verification gates that block a bad commit, ticket state that records who changed what, and rules for review by another person. `cdev` drops all of that for one developer, and widens the domains from firmware to C and Python generally.

Install one of the two per repository.

## License

MIT. See [THIRD_PARTY_NOTICES.md](../../THIRD_PARTY_NOTICES.md) for the content adapted from other projects.
