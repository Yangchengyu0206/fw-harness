# Testing cdev

For the first people trying it. Installing is in [INSTALL.md](INSTALL.md), and how it all works is in [README.md](README.md).

繁體中文: [TESTING.zh-TW.md](TESTING.zh-TW.md)

## What this package does

In one line: **it lets an agent know where the work stands, what the rules are, and where things live, and it keeps that knowledge when the conversation ends.**

It is not a model and it does not make one smarter. It moves what you would otherwise repeat every session into files the agent reads for itself.

What lands in a repository:

| File | What it carries |
|---|---|
| `AGENTS.md` | every rule. Copilot loads it in every conversation |
| `ARCHITECTURE.md` (root and per folder) | the map: what each file does, the flows through it, decisions with reasons, terms |
| `PROGRESS.md` | `## Now`: where the work is, the facts confirmed, what waits on you. `## Log`: the history |
| `feature_list.json` | what is being built, as next / active / verifying / done |
| four scripts in `tools/` | the feature list, document drift, the session hook, the MCP listing |
| `.vscode/settings.json` | vendor folders read-only, destructive commands held for your approval |
| `.github/hooks/`, `.github/agents/`, `.github/instructions/` | the state injected at session start, a read-only reading agent, a reminder while editing documented code |

Of the 14 skills, some the agent reaches on its own (`cdev-implement`, `cdev-review`, `cdev-debug`), and some you type (`/cdev-init`, `/cdev-grill`, `/cdev-done`).

## With it and without it

### Without

**What you keep**

- nothing to install or maintain, and no extra files in the repository
- every conversation starts clean, with no rules shaping it
- the lightest option when you only have one small question

**What it costs**

- every new conversation starts by explaining where the work stopped
- an architecture question means grepping from scratch, and the answer is as deep as that attempt happened to be
- the agent may edit the vendor SDK, or run a command you did not expect
- nothing is recorded. Why a decision was made is gone in three months
- when the conversation is summarised, the register value or timing you worked out goes with it

### With

**What you gain**

- a new conversation opens knowing where the work stands, injected by a hook rather than left to the model
- the architecture documents locate the code, and answers say which claims were checked against it
- decisions and their reasons live in the repository rather than in someone's chat history
- one standard for finished work, and a feature becomes `done` only when you say so
- a script reports where the documents no longer match the files
- vendor folders are read-only and destructive commands wait for you
- a question this repository cannot answer (another branch, a datasheet) sends the agent to the tools it holds rather than to "I do not know"
- `/cdev-grill` puts the assumptions under a plan on the table before the work starts

**What it costs**

- the first `/cdev-init` takes a few minutes and one large pass over the repository
- more documents to keep true. A stale document misleads, which is what `doc_check` and the rules are there to limit, at some cost
- the rules themselves take 3 to 4 KB of every conversation
- **most of the behaviour is rule-driven rather than guaranteed.** The model follows it most of the time, and a long conversation is where it slips
- one small question gains nothing here, and carries a little more weight

### Where it fits

**Worth it**: work that spans days, anything verified on a board, a project someone else will pick up, code you will come back to in three months.

**Not worth it**: a one-off edit, or a single question.

## What is guaranteed and what is not

This decides what to expect:

| Behaviour | How firm |
|---|---|
| the state injected at the start of a session | mechanism (a hook script). VS Code marks hooks as preview |
| document drift detected | mechanism (`doc_check.py`) |
| vendor read-only, destructive commands confirmed | editor settings. **Unverified so far: please confirm this one** |
| documents first, then verified in the code | rule |
| reach for a tool before answering "I do not know" | rule |
| `## Now` rewritten after each step | rule |
| documents updated with the code | rule plus detection |
| your confirmation before `done` | rule |

## Please try these

Most important first:

1. **Install.** After following INSTALL, type `/` in agent chat. Are the 14 `cdev-` commands listed?
2. **The opening.** In a repository that already has the harness, open a new conversation and ask anything. Does it say where the work stopped and what is next, without being asked? If not, is it silent, or partial?
3. **The settings.** Open a file in a vendor folder: is it read-only? Ask the agent to run `git push`: does it wait for you?
4. **An architecture question.** Ask something that spans a few files. Did it read ARCHITECTURE.md first? Does the answer say what was verified?
5. **`/cdev-init`.** Run it on a project with no harness. Does it finish? Is what it wrote true?
6. **`/cdev-upgrade`.** Run it on a repository set up by an older version. Is everything you wrote still there?
7. **A long session.** Work on something for a while, type `/cdev-checkpoint`, then open a new conversation and see whether it picks up.
8. **`/cdev-grill`.** Before starting a piece of work, let it interview you. Are the questions the right ones?

## When you report something

- the VS Code version (Help → About) and the GitHub Copilot Chat extension version
- which install route you used (the plugin folder, or the skills copied into the repository)
- the model selected at the time
- what you did, what you expected, and what happened
- for an error, what View → Output → `GitHub Copilot Chat` shows

Report in [GitHub issues](https://github.com/Yangchengyu0206/fw-harness/issues), or to whoever handed you the package.

## Known and unverified

- the VS Code read-only and command-approval settings are written from the documented settings, and nobody has confirmed them in a running editor yet
- agent hooks are in preview in VS Code, and their format may change
- the Linux and Windows driver references have not been reviewed by a driver engineer
- the commands are written for Windows (`py -3`); use `python3` on macOS and Linux
