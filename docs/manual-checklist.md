# Manual checklist

Skills cannot be tested automatically, so this list is run by hand once in GitHub Copilot in VS Code and once in Claude Code before a release. Work through it on a scratch copy of a firmware repository, never on real work.

Record the date, the tool, its version, and who ran it in the table at the end.

## Install

- [ ] In VS Code, with `chat.plugins.marketplaces` naming `<owner>/fw-harness`, the plugins appear under `@agentPlugins` in the Extensions view. In Claude Code, `claude plugin marketplace add <owner>/fw-harness` succeeds.
- [ ] Installing the plugin succeeds, and all fourteen skills are listed.
- [ ] In Claude Code, `claude plugin validate . --strict` passes in a clone of this repository.
- [ ] In VS Code, typing `/` in agent chat lists the typed skills, and the skills are discovered from the plugin's `skills/` folder. If they are not, this item becomes a bug report.
- [ ] In VS Code, the plugin can be disabled globally and enabled for one workspace, and a skill the agent reaches on its own does not fire in a workspace where the plugin is disabled.
- [ ] Opening a repository after `fw-harness-init`, VS Code shows the recommendation notification on the first chat message, and the plugin is listed under `@agentPlugins @recommended`.

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

Run once in GitHub Copilot in VS Code and once in Claude Code, each on scratch repositories.

- [ ] Installing `cdev@fw-harness` succeeds, and all thirteen skills are listed.
- [ ] `cdev-init` detects the right domain set on one repository per domain: plain C, firmware, Linux driver, Windows driver, Python.
- [ ] On a mixed repository (firmware with Python test tooling), the detected set holds both domains.
- [ ] `cdev-init` runs to the end without asking anything, then asks one question over the whole result.
- [ ] With an existing `AGENTS.md`, the file is untouched and `AGENTS.md.cdev-proposed` appears.
- [ ] No `{{` placeholder is left in any generated file.
- [ ] Every folder ARCHITECTURE.md has `## Files` and `## Flows`, and `py -3 tools/doc_check.py` reports no drift right after `cdev-init`.
- [ ] In VS Code, a file in a read-only folder opens read-only, and `git push` asked for by the agent waits for your approval.
- [ ] Editing a file under a code folder attaches `architecture.instructions.md` to the Copilot request (visible in the references list).
- [ ] A new conversation, with no skill typed, opens by reporting `## Now`, the features, and `doc_check`, then asks which feature to take.
- [ ] The `SessionStart` hook runs: the opening report appears without the agent reading PROGRESS.md itself. Hooks are in preview, so note the VS Code version that was tried.
- [ ] The `Stop` hook reports drift after a session that renamed a file.
- [ ] `cdev-explorer` appears in the agents picker, answers a question with `path:line` citations, and edits nothing.
- [ ] With an MCP server configured, a question the repository cannot answer sends the agent to that server's tool without being told to, and the answer names the tool.
- [ ] `py -3 tools/mcp_list.py` lists the servers from `.vscode/mcp.json` and from the user configuration.
- [ ] `cdev-session-start` proposes a feature and stops for your answer before writing code.
- [ ] `cdev-init` writes `Verification: off` and offers `light` and `full` in the message that hands over the result.
- [ ] At `Verification: off`, no skill asks for a board result, and the log entry says what was left unchecked on hardware.
- [ ] At `Verification: full` on a project that builds in a vendor IDE, `cdev-implement` stops at `verifying` and writes a checklist under `Waiting on the user` in `## Now`.
- [ ] `cdev-checkpoint` writes the facts found in the conversation into `## Now`, and a new conversation continues from them.
- [ ] `cdev-implement` writes a failing test first and uses the build and test commands from AGENTS.md.
- [ ] On a repository with no tests, `cdev-init` writes `Test: none`, and `cdev-implement` and `cdev-debug` add no test framework, yet still show a real run with its output.
- [ ] `cdev-debug` on a plain bug takes the shortcut and says so; on a hard one it shows a loop going red before any fix.
- [ ] `fw-c-review` and `cdev-review` list the changed interfaces with their callers, label each finding rule or judgement, and report nothing the formatter or linters already catch.
- [ ] `cdev-review` writes a report into `docs/reviews/` with the two axes kept separate.
- [ ] `cdev-target-verify` stores a log under `docs/evidence/` and records it on the feature.
- [ ] `cdev-done` fixes document drift, asks before setting `done`, updates `## Now` in PROGRESS.md, and hands you a commit message rather than committing.
- [ ] On a large repository, `cdev-init` documents the folders you work in and leaves the rest as stubs, and `doc_check` lists those as waiting.
- [ ] `cdev-upgrade` on a repository generated by the previous version adds the missing sections, keeps every sentence you wrote, and ends with `doc_check` running.
- [ ] `cdev-upgrade` run twice in a row changes nothing the second time.
- [ ] `py -3 scripts/pack_cdev.py` builds a zip that installs on a second machine with `chat.pluginLocations` alone, and `/` then lists the cdev commands there.
- [ ] `py -3 install_local.py --repo <path>` puts the skills in `.github/skills/`, and Copilot finds them in that workspace.
- [ ] `cdev-guide` names the skill you actually needed.
- [ ] `py -3 tools/feature.py check` fails loudly on a hand-broken `feature_list.json`.

## Record

| Date | Tool and version | Who | Result |
|---|---|---|---|
| | | | |
