# fw-c-harness

A harness and a set of skills for C firmware teams, for GitHub Copilot in VS Code and Claude Code.

## Install

Install for the repositories that use it, not for every project: wherever the plugin is active, the skills the agent reaches on its own are loaded too.

**GitHub Copilot in VS Code**

1. Add to your user settings JSON (**Preferences: Open User Settings (JSON)**):

   ```json
   "chat.plugins.enabled": true,
   "chat.plugins.marketplaces": ["Yangchengyu0206/fw-harness"]
   ```

2. In the Extensions view (Ctrl+Shift+X), search for `@agentPlugins` and install `fw-c-harness`.
3. VS Code can enable or disable a plugin globally or per workspace. Keep it enabled in the firmware workspaces only.

**Claude Code**, from a shell in the repository:

```bash
claude plugin marketplace add Yangchengyu0206/fw-harness
claude plugin install fw-c-harness@fw-harness --scope project
```

Inside a session, `/plugin install fw-c-harness@fw-harness` asks for the scope instead.

**Copilot CLI**

```bash
copilot plugin marketplace add Yangchengyu0206/fw-harness
copilot plugin install fw-c-harness@fw-harness
```

`fw-harness-init` writes the marketplace and the plugin into the repository's `.claude/settings.json`, which all three tools read. None installs from it silently: VS Code shows a notification on the first chat message and lists the plugin under `@agentPlugins @recommended`, and Claude Code prints the `claude plugin install` command to run.

## Use it

Run `fw-harness-init` once in the firmware repository, then start each session with `fw-session-start`. When you cannot remember which skill fits, run `fw-guide`.

## The skills

Lifecycle: `fw-harness-init`, `fw-harness-upgrade`, `fw-architecture-sync`.
Work loop: `fw-session-start`, `fw-ticket`, `fw-hil-verify`, `fw-done`.
Code: `fw-c-implement`, `fw-c-review`, `fw-review-respond`, `fw-c-test-gap`, `fw-c-debug`, `fw-misra-deviation`.
Router: `fw-guide`.

One page per skill lives in [docs/skills](../../docs/skills).

## One difference between the two tools

Six of the skills are meant for a human to type: `fw-harness-init`, `fw-harness-upgrade`, `fw-session-start`, `fw-hil-verify`, `fw-done`, and `fw-guide`. They carry `disable-model-invocation: true`, which GitHub Copilot in VS Code and Claude Code both document as keeping the agent from starting them; you start them with `/` in chat. Copilot CLI does not document the key, so there an agent may still reach them on its own. The guardrails that matter do not depend on it: moving a ticket to `done` needs a typed confirmation in a real terminal, and committing is left to you in both tools.

## Update

Run `fw-harness-upgrade` after the plugin updates. It replaces the files the plugin manages and proposes anything your team owns, one item at a time.

## License

MIT. See [THIRD_PARTY_NOTICES.md](../../THIRD_PARTY_NOTICES.md) for the content adapted from other projects.
