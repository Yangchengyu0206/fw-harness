# cdev

A markdown-first harness for one developer working in C and Python, for GitHub Copilot in VS Code and Claude Code.

It gives an agent what it needs to know where it is and what to do next, and gives the code the domain rules general coding skills do not carry: firmware, Linux drivers, Windows drivers, plain C, and Python.

## Install

Install for the repositories that use it, not for every project: wherever the plugin is active, the skills the agent reaches on its own are loaded too.

**GitHub Copilot in VS Code**

1. Add to your user settings JSON (**Preferences: Open User Settings (JSON)**):

   ```json
   "chat.plugins.enabled": true,
   "chat.plugins.marketplaces": ["Yangchengyu0206/fw-harness"]
   ```

2. In the Extensions view (Ctrl+Shift+X), search for `@agentPlugins` and install `cdev`.
3. VS Code can enable or disable a plugin globally or per workspace. Keep it enabled in the workspaces you develop with it only.

**Claude Code**, from a shell in the repository:

```bash
claude plugin marketplace add Yangchengyu0206/fw-harness
claude plugin install cdev@fw-harness --scope local
```

Inside a session, `/plugin install cdev@fw-harness` asks for the scope instead.

**Copilot CLI**

```bash
copilot plugin marketplace add Yangchengyu0206/fw-harness
copilot plugin install cdev@fw-harness
```

Then, in your repository, open agent chat and type `/cdev-init` once.

## What lands in your repository

```
AGENTS.md            every rule: domains, where to work, how to open a conversation,
                     how to answer questions, the feature loop, what done means
CLAUDE.md            one line, @AGENTS.md, so Claude Code reads the same rules
ARCHITECTURE.md      the map of the repository, and decisions with their reasons
<folder>/ARCHITECTURE.md
                     responsibility, one line per file, flows, entry points, dependencies
PROGRESS.md          ## Now (where the work is, confirmed facts, what waits on you), then a dated log
feature_list.json    what is being built, the single source of truth
tools/feature.py     keeps feature_list.json valid
tools/doc_check.py   reports where the architecture documents no longer match the files
.vscode/settings.json
                     read-only folders cannot be edited; destructive commands need your approval
.github/instructions/architecture.instructions.md
                     reaches Copilot whenever it works on documented code
docs/reviews/        review reports
```

The two scripts report; nothing blocks a commit.

## A day of work in GitHub Copilot

1. Open a conversation. The agent reads `## Now`, lists the features, runs `doc_check`, and asks which feature to take.
2. Questions about the code are answered from the architecture documents as a map, then checked in the code, with each claim marked verified or not.
3. While a feature is built, `## Now` is rewritten after every step, and confirmed facts go there as they are found, so a summarised conversation loses nothing.
4. When the build or flashing happens in a vendor IDE, the feature stops at `verifying` with a checklist for you in `## Now`. You run it and report the result, in the same conversation or a new one.
5. When the context usage runs high, type `/cdev-checkpoint`.
6. When verification has passed, the agent shows the evidence and the documents it changed, and the feature becomes `done` on your confirmation.

## Tests are optional

A repository with no tests is a normal case, not a gap to fill. `cdev-init` then writes `Test: none` into AGENTS.md, and the skills add no test framework unless you ask. What they still do is run each change on a real input and show you the command and its output, because an agent that did not run its change is only guessing that it works. A feature's `verification` list is optional too, and `cdev-target-verify` matters only for firmware and drivers.

## The skills

Setting up: `cdev-init`.
A day of work: `cdev-session-start`, `cdev-implement`, `cdev-target-verify`, `cdev-checkpoint`, `cdev-done`, with `cdev-feature` underneath.
Looking at code: `cdev-review`, `cdev-test-gap`, `cdev-debug`.
When the structure changes: `cdev-architecture-sync`.
Router: `cdev-guide`.

One page per skill lives in [docs/skills](../../docs/skills).

## Domains

`cdev-init` detects which domains a repository belongs to, and a repository can belong to several. The implement, review, test-gap, and debug skills read one reference per domain from `skills/cdev-implement/references/`: rules, a review checklist, debugging anchors, and build and test commands.

## One difference between the two tools

Six of the skills are meant for you to type: `cdev-init`, `cdev-session-start`, `cdev-target-verify`, `cdev-checkpoint`, `cdev-done`, and `cdev-guide`. They carry `disable-model-invocation: true`, which GitHub Copilot in VS Code and Claude Code both document as keeping the agent from starting them; you start them with `/` in chat. Copilot CLI does not document the key, so there an agent may still reach them on its own.

## How it differs from fw-c-harness

`fw-c-harness`, in the same marketplace, is for a firmware team: verification gates that block a bad commit, ticket state that records who changed what, and rules for review by another person. `cdev` drops all of that for one developer, and widens the domains from firmware to C and Python generally.

Install one of the two per repository.

## License

MIT. See [THIRD_PARTY_NOTICES.md](../../THIRD_PARTY_NOTICES.md) for the content adapted from other projects.
