# cdev

A markdown-first harness for one developer working in C and Python, for GitHub Copilot in VS Code and Claude Code.

It gives an agent what it needs to know where it is and what to do next, and gives the code the domain rules general coding skills do not carry: firmware, Linux drivers, Windows drivers, plain C, and Python.

繁體中文: [README.zh-TW.md](README.zh-TW.md)

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

Then, in your repository, open agent chat and type `/cdev-init` once. After a later plugin update, type `/cdev-upgrade` once per repository.

**Without a marketplace**, on a machine that cannot reach one, build a package from a checkout:

```bash
py -3 scripts/pack_cdev.py
```

It writes `dist/cdev-<version>.zip`, which holds the plugin, both READMEs, the licence, and an installer. Whoever receives it unzips it and follows [INSTALL.md](INSTALL.md): either registering the folder with the `chat.pluginLocations` setting, or copying the skills into one repository with `py -3 install_local.py --repo <path>`.

## What lands in your repository

```
AGENTS.md            every rule: domains, verification level, where to work, how to open
                     a conversation, how to answer questions, the feature loop, what done means
CLAUDE.md            one line, @AGENTS.md, so Claude Code reads the same rules
ARCHITECTURE.md      the map of the repository, and decisions with their reasons
<folder>/ARCHITECTURE.md
                     responsibility, one line per file, flows, entry points, dependencies
PROGRESS.md          ## Now (where the work is, confirmed facts, what waits on you), then a dated log
feature_list.json    what is being built, the single source of truth
tools/feature.py     keeps feature_list.json valid
tools/doc_check.py   reports where the architecture documents no longer match the files
tools/hooks.py       answers the session hooks
tools/mcp_list.py    lists the MCP servers configured here
.vscode/settings.json
                     read-only folders cannot be edited; destructive commands need your approval
.github/instructions/architecture.instructions.md
                     reaches Copilot whenever it works on documented code
.github/hooks/cdev.json
                     SessionStart puts ## Now, the features, and the document check in front of
                     the agent; Stop reports drift. Hooks are in preview in VS Code
.github/agents/cdev-explorer.agent.md
                     a read-only agent that reads code in its own context and returns citations
docs/reviews/        review reports
```

The two scripts report; nothing blocks a commit.

A large repository is not documented all at once: `cdev-init` writes the folders you work in in full and leaves the rest as stubs. `doc_check` reports a stub as waiting rather than as drift, and `cdev-architecture-sync` fills one when the work reaches that folder.

## A day of work in GitHub Copilot

1. Open a conversation. The session hook hands the agent `## Now`, the features, and the state of the documents, and it asks which feature to take. Where hooks are unavailable, AGENTS.md has it do the same by hand.
2. Questions about the code are answered from the architecture documents as a map, then checked in the code, with each claim marked verified or not. A question that means reading several files goes to the `cdev-explorer` agent, which reads in its own context and returns the answer with citations.
3. A question this repository cannot answer, such as one about another branch, a datasheet, or an application note, sends the agent to the tools it holds this session before it answers that it does not know. New MCP servers are picked up without editing anything, because the rule points at the tool list rather than at a list of servers.
3. While a feature is built, `## Now` is rewritten after every step, and confirmed facts go there as they are found, so a summarised conversation loses nothing.
4. When the build or flashing happens in a vendor IDE, the feature stops at `verifying` with a checklist for you in `## Now`. You run it and report the result, in the same conversation or a new one.
5. When the context usage runs high, type `/cdev-checkpoint`.
6. When verification has passed, the agent shows the evidence and the documents it changed, and the feature becomes `done` on your confirmation.

## Verification starts switched off

`AGENTS.md` carries one line, `Verification: off`, and `cdev-init` offers the other two levels when it hands you the result. `off` asks for no hardware results and no checklists: a feature closes on the build and a run, and each log entry says what was left unchecked on real hardware. `light` adds the one step still owed as the feature's next step. `full` adds the checklist for you, the logs under `docs/evidence/`, and `cdev-target-verify`.

Early work on a new chip rarely reaches hardware, so it starts at `off`. Changing the level is one word, and no reinstall.

What stays at every level: a feature becomes `done` only when you confirm it, and `## Log` records how it was checked.

## Tests are optional

A repository with no tests is a normal case, not a gap to fill. `cdev-init` then writes `Test: none` into AGENTS.md, and the skills add no test framework unless you ask. What they still do is run each change on a real input and show you the command and its output, because an agent that did not run its change is only guessing that it works. A feature's `verification` list is optional too, and `cdev-target-verify` matters only for firmware and drivers.

## The skills

Setting up: `cdev-init`, then `cdev-upgrade` after a plugin update.
A day of work: `cdev-session-start`, `cdev-implement`, `cdev-target-verify`, `cdev-checkpoint`, `cdev-done`, with `cdev-feature` underneath.
Looking at code: `cdev-review`, `cdev-test-gap`, `cdev-debug`.
When the structure changes: `cdev-architecture-sync`.
Router: `cdev-guide`.

One page per skill lives in [docs/skills](../../docs/skills).

## Domains

`cdev-init` detects which domains a repository belongs to, and a repository can belong to several. The implement, review, test-gap, and debug skills read one reference per domain from `skills/cdev-implement/references/`: rules, a review checklist, debugging anchors, and build and test commands.

## One difference between the two tools

Seven of the skills are meant for you to type: `cdev-init`, `cdev-upgrade`, `cdev-session-start`, `cdev-target-verify`, `cdev-checkpoint`, `cdev-done`, and `cdev-guide`. They carry `disable-model-invocation: true`, which GitHub Copilot in VS Code and Claude Code both document as keeping the agent from starting them; you start them with `/` in chat. Copilot CLI does not document the key, so there an agent may still reach them on its own.

## How it differs from fw-c-harness

`fw-c-harness`, in the same marketplace, is for a firmware team: verification gates that block a bad commit, ticket state that records who changed what, and rules for review by another person. `cdev` drops all of that for one developer, and widens the domains from firmware to C and Python generally.

Install one of the two per repository.

## License

MIT. See [THIRD_PARTY_NOTICES.md](../../THIRD_PARTY_NOTICES.md) for the content adapted from other projects.
