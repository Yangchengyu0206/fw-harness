# fw-harness

Harnesses and skills for C and Python development, for GitHub Copilot in VS Code and Claude Code. Traditional Chinese: [README.zh-TW.md](README.zh-TW.md).

## Status: 0.1 preview

Both plugins are complete and their scripts are covered by automated tests, but the skills have not yet been run end to end by a real agent. Expect rough edges, and please report them in [GitHub issues](https://github.com/Yangchengyu0206/fw-harness/issues).

Known limits in this version:

- **Checked by structure, not yet by use.** The tests prove every skill is well formed, every link resolves, and every documented command parses. They cannot prove an agent follows a skill. [docs/manual-checklist.md](docs/manual-checklist.md) lists what still has to be tried by hand.
- **Not yet tried in the tools.** Installation and every skill follow the published formats for GitHub Copilot in VS Code, Claude Code, and Copilot CLI, and none has been run in them yet. VS Code is the primary target.
- **Commands are written for Windows.** The skills tell the agent to run Python as `py -3`. On macOS and Linux, use `python3` in its place; the scripts themselves run on all three.
- **The driver references are unreviewed.** The Linux and Windows driver material in `cdev` has not yet been checked by a driver engineer. Corrections are welcome.

## Two plugins

This marketplace holds two plugins. Install one per repository.

| | `fw-c-harness` | `cdev` |
|---|---|---|
| For | a firmware team sharing one repository | one developer |
| Languages and domains | C firmware | C and Python: plain C, firmware, Linux drivers, Windows drivers |
| Verification | seven gates in `check`, git hooks, ratchets | none enforced; the project's own build and tests when it has them, otherwise a real run with its output shown |
| State | one ticket file per feature, with who changed what | one `feature_list.json` and a `PROGRESS.md` |
| Review | by someone other than the author | self-review, with every finding re-verified |
| Scripts written into the repository | the gate and state scripts | one, `tools/feature.py` |
| Install | `fw-c-harness` from `@agentPlugins` in VS Code | `cdev` from `@agentPlugins` in VS Code |

`cdev` is described in [plugins/cdev/README.md](plugins/cdev/README.md), with a Traditional Chinese version at [plugins/cdev/README.zh-TW.md](plugins/cdev/README.zh-TW.md). The rest of this page describes `fw-c-harness`.

## fw-c-harness

One install gives a firmware team two things:

1. **A harness generated into their own repository**: entry documents, ticket state that records who changed what, verification gates, git hooks, and an ARCHITECTURE.md for every folder of C sources, derived from the real tree.
2. **Skills for the whole work loop**: starting a session, taking a ticket, implementing test first, reviewing, answering a review, debugging, and wrapping up.

## Why it looks like this

- **Several people share the repository.** Every state change records the person who made it, taken from `git config`. One file per ticket, so two people adding tickets in parallel get a conflict git can show instead of a silent overwrite.
- **The rules live in the repository, not in the plugin.** The gates are Python scripts committed to the firmware repository, so a person committing by hand, an agent, and CI all follow the same rules. The plugin carries only what should update with its version.
- **The gates ratchet.** The `cppcheck` suppression list and the architecture grandfather list may only shrink, measured against `origin/main`.
- **Written and done are different.** A ticket whose code passes `check` but still owes board verification or a review stays in `verifying`, with the debt written down.

## Install

Adding the marketplace and installing a plugin are two steps. Install for the repositories that use the harness rather than for every project: the skills the agent reaches on its own load wherever the plugin is active, and would answer a request for a review or a debug session in an unrelated project too.

**GitHub Copilot in VS Code**

1. Open your user settings as JSON (**Preferences: Open User Settings (JSON)**) and add:

   ```json
   "chat.plugins.enabled": true,
   "chat.plugins.marketplaces": ["Yangchengyu0206/fw-harness"]
   ```

2. Open the Extensions view (Ctrl+Shift+X), search for `@agentPlugins`, and install `fw-c-harness`.
3. VS Code can enable or disable a plugin globally or for one workspace. Keep it enabled only in the firmware workspaces.

**Claude Code**, from a shell in the firmware repository:

```bash
claude plugin marketplace add Yangchengyu0206/fw-harness
claude plugin install fw-c-harness@fw-harness --scope project
```

Inside a session, `/plugin install fw-c-harness@fw-harness` asks for the scope instead. `project` records the plugin in the repository for everyone; `local` keeps it to you in this repository; `user` turns it on in every project.

**Copilot CLI**

```bash
copilot plugin marketplace add Yangchengyu0206/fw-harness
copilot plugin install fw-c-harness@fw-harness
```

Then open agent chat in the firmware repository and type `/fw-harness-init` once.

### Joining a repository that already has the harness

`fw-harness-init` writes this marketplace and the plugin into the repository's `.claude/settings.json`. Claude Code, GitHub Copilot in VS Code, and Copilot CLI all read that file, and none of them installs a plugin from it silently:

- **VS Code** shows a notification the first time you send a chat message. Install from the Extensions view filtered by `@agentPlugins @recommended`.
- **Claude Code** adds the marketplace once you trust the folder, reports the plugin as not installed, and prints the `claude plugin install` command to run.

## What lands in your repository

```
AGENTS.md              short entry point for every tool
CLAUDE.md              the handbook: session, rules, Definition of Done, and why each gate exists
ARCHITECTURE.md        the module map, generated from harness/architecture.json
harness/
  config.json          every external command, as an argv array
  architecture.json    approved layering, the single source of the rules
  tickets/FW-NNNN.json one file per ticket
  scripts/             the only implementation of the gates
.githooks/             commit-msg, post-commit, post-merge
init.sh / init.ps1     thin wrappers, no flags of their own
```

`check` runs seven steps in order and stops at the first failure: format on changed C sources, `cppcheck`, the architecture gate, the ticket gate, the cross build, the host tests, and the size budget. Every external command comes from `harness/config.json`, so a team swaps toolchains without editing a script.

## Requirements

Python 3.9 or newer, git, and the toolchain your project names in `harness/config.json`. The defaults are `arm-none-eabi-gcc` with CMake, host `gcc` running Unity, `cppcheck`, and `clang-format`. MISRA C:2012 is a reference standard, advisory by default, configurable in `harness/review-policy.json`.

Windows, macOS, and Linux. On Windows the scripts run under `py -3` (use `python3` elsewhere), read and write UTF-8 whatever the console code page is, and the git hooks use the POSIX shell Git for Windows ships.

## The skills

| Skill | Invocation | What it is for |
|---|---|---|
| `fw-harness-init` | you type it | Generate the harness in a firmware repository |
| `fw-harness-upgrade` | you type it | Update the harness after a plugin release |
| `fw-architecture-sync` | the agent reaches it | Redraft the architecture and refresh the documents |
| `fw-session-start` | you type it | Open a session and agree on the ticket |
| `fw-ticket` | the agent reaches it | Every ticket write |
| `fw-hil-verify` | you type it | Pay off board verification with a captured log |
| `fw-done` | you type it | Handoff, progress note, ticket, commit message |
| `fw-c-implement` | the agent reaches it | Test-first implementation |
| `fw-c-review` | the agent reaches it | Two-axis review, Standards and Spec |
| `fw-review-respond` | the agent reaches it | Check, fix, or decline review findings, then hand back for re-review |
| `fw-c-test-gap` | the agent reaches it | What has no test, P0 to P3 |
| `fw-c-debug` | the agent reaches it | Make the defect show on demand, prove its cause, then fix |
| `fw-misra-deviation` | the agent reaches it | Record a deviation with an approver |
| `fw-guide` | you type it | Which skill fits your situation |

One page per skill is in [docs/skills](docs/skills). The design is in [the spec](docs/superpowers/specs/2026-09-15-fw-c-harness-plugin-design.md).

## Contributing

Run the tests with `py -3 -m pytest tests -q`, or `python3 -m pytest tests -q` on macOS and Linux. Skills cannot be tested automatically, so changes to them are checked against [docs/manual-checklist.md](docs/manual-checklist.md).

## License

MIT. Content adapted from other projects is credited in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
