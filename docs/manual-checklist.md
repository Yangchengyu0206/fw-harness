# Manual checklist

Skills cannot be tested automatically, so this list is run by hand once in Claude Code and once in Copilot CLI before a release. Work through it on a scratch copy of a firmware repository, never on real work.

Record the date, the tool, its version, and who ran it in the table at the end.

## Install

- [ ] `/plugin marketplace add <owner>/fw-harness` in Claude Code, or `copilot plugin marketplace add <owner>/fw-harness` in Copilot CLI, succeeds.
- [ ] Installing the plugin succeeds, and all fourteen skills are listed.
- [ ] In Claude Code, `claude plugin validate . --strict` passes in a clone of this repository.
- [ ] In Copilot CLI, the skills are discovered from the plugin's `skills/` folder. If they are not, the plugin manifest needs an explicit list and this checklist item becomes a bug report.

## Generate the harness

- [ ] `fw-harness-init` in a scratch firmware repository creates the files, sets `core.hooksPath`, and writes `harness/.harness-version`.
- [ ] Running it a second time changes nothing and reports no proposals.
- [ ] With an existing `AGENTS.md`, the file is untouched and `AGENTS.md.harness-proposed` appears.
- [ ] The architecture draft lists the real modules, and the confirmation step asks before the rules are written.
- [ ] Every module folder has an ARCHITECTURE.md, and `check` reports the architecture gate as passed.

## The loop

- [ ] `fw-session-start` verifies the environment, reads the handoff, and stops for your answer before writing code.
- [ ] Creating a ticket records your git identity as `created_by`.
- [ ] `fw-c-implement` writes the failing test first and shows you the failure before implementing.
- [ ] `check --record FW-NNNN` refuses to run on a dirty working tree.
- [ ] `fw-c-review` produces two separate axes in `harness/reviews/`, and its counts match its findings.
- [ ] `fw-review-respond` shows a verdict per finding before editing, declines at least one wrong finding with evidence, appends an Author response table, and leaves the ticket's review evidence untouched.
- [ ] The agent declines to move a ticket to `done`, and `ticket.py move <id> done` asks for typed confirmation in a terminal.
- [ ] `fw-hil-verify` stores a log under `harness/evidence/` and records hil evidence.
- [ ] `fw-done` writes the handoff and the progress note, and hands you a commit message rather than committing.
- [ ] `fw-guide` names the skill you actually needed.

## Two people

- [ ] Two clones with different git identities each create a ticket; merging reports an add/add conflict rather than losing one.
- [ ] `ticket.py collisions` names the clash before the merge, and `renumber` frees the id and lists the commits still naming the old one.
- [ ] A review by the assignee does not satisfy the Definition of Done; a review by the other person does.

## Upgrade

- [ ] `fw-harness-upgrade --dry-run` reports the version change and the four groups without writing.
- [ ] After the real run, a locally edited script is untouched and its new version is a proposal.

## cdev

Run once in Claude Code and once in Copilot CLI, each on scratch repositories.

- [ ] Installing `cdev@fw-harness` succeeds, and all eleven skills are listed.
- [ ] `cdev-init` detects the right domain set on one repository per domain: plain C, firmware, Linux driver, Windows driver, Python.
- [ ] On a mixed repository (firmware with Python test tooling), the detected set holds both domains.
- [ ] `cdev-init` runs to the end without asking anything, then asks one question over the whole result.
- [ ] With an existing `AGENTS.md`, the file is untouched and `AGENTS.md.cdev-proposed` appears.
- [ ] No `{{` placeholder is left in any generated file.
- [ ] `cdev-session-start` proposes a feature and stops for your answer before writing code.
- [ ] `cdev-implement` writes a failing test first and uses the build and test commands from AGENTS.md.
- [ ] On a repository with no tests, `cdev-init` writes `Test: none`, and `cdev-implement` and `cdev-debug` add no test framework, yet still show a real run with its output.
- [ ] `cdev-debug` on a plain bug takes the shortcut and says so; on a hard one it shows a loop going red before any fix.
- [ ] `fw-c-review` and `cdev-review` list the changed interfaces with their callers, label each finding rule or judgement, and report nothing the formatter or linters already catch.
- [ ] `cdev-review` writes a report into `docs/reviews/` with the two axes kept separate.
- [ ] `cdev-target-verify` stores a log under `docs/evidence/` and records it on the feature.
- [ ] `cdev-done` updates `## Now` in PROGRESS.md and hands you a commit message rather than committing.
- [ ] `cdev-guide` names the skill you actually needed.
- [ ] `py -3 tools/feature.py check` fails loudly on a hand-broken `feature_list.json`.

## Record

| Date | Tool and version | Who | Result |
|---|---|---|---|
| | | | |
