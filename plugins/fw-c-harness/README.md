# fw-c-harness

A harness and a set of skills for C firmware teams, for Claude Code and GitHub Copilot.

## Install

**Claude Code**

```
/plugin marketplace add Yangchengyu0206/fw-harness
/plugin install fw-c-harness@fw-harness
```

**Copilot CLI**

```
copilot plugin marketplace add Yangchengyu0206/fw-harness
copilot plugin install fw-c-harness@fw-harness
```

After `fw-harness-init` runs in a firmware repository, that repository carries `.claude/settings.json` and `.github/copilot-settings.json` naming this marketplace, so the next person who clones it is prompted to install the plugin.

## Use it

Run `fw-harness-init` once in the firmware repository, then start each session with `fw-session-start`. When you cannot remember which skill fits, run `fw-guide`.

## The skills

Lifecycle: `fw-harness-init`, `fw-harness-upgrade`, `fw-architecture-sync`.
Work loop: `fw-session-start`, `fw-ticket`, `fw-hil-verify`, `fw-done`.
Code: `fw-c-implement`, `fw-c-review`, `fw-c-test-gap`, `fw-c-debug`, `fw-misra-deviation`.
Router: `fw-guide`.

One page per skill lives in [docs/skills](../../docs/skills).

## One difference between the two tools

Six of the skills are meant for a human to type: `fw-harness-init`, `fw-harness-upgrade`, `fw-session-start`, `fw-hil-verify`, `fw-done`, and `fw-guide`. They carry `disable-model-invocation: true`, which Claude Code honours by keeping the agent from firing them. Copilot does not document that key for skills, so on Copilot an agent can still reach them on its own. The guardrails that matter do not depend on it: moving a ticket to `done` needs a typed confirmation in a real terminal, and committing is left to you in both tools.

## Update

Run `fw-harness-upgrade` after the plugin updates. It replaces the files the plugin manages and proposes anything your team owns, one item at a time.

## License

MIT. See [THIRD_PARTY_NOTICES.md](../../THIRD_PARTY_NOTICES.md) for the content adapted from other projects.
