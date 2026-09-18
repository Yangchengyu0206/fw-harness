# Installing cdev offline

This package is the whole cdev plugin. It needs no marketplace and no access to GitHub.

繁體中文: [INSTALL.zh-TW.md](INSTALL.zh-TW.md)

Python 3 is required (`py -3` on Windows).

## Which route

| Your situation | Route |
|---|---|
| You share one project with other people, and all of you want it | **Option 2**: the skills live in that repository. A later update reaches everyone through `git pull`, with no new package and no settings to change |
| You have several projects that want it | **Option 1**: install it as a plugin, and every workspace has it |

Both can coexist, though one repository should use one of them, so a skill is not loaded twice.

## Option 1: as a plugin, for every workspace

1. Unzip it somewhere that stays put, such as `C:\tools\cdev`. VS Code reads it from there every time, so keep it out of a downloads or temporary folder.

2. Print the setting to add:

   ```
   py -3 C:\tools\cdev\install_local.py
   ```

   It prints something like:

   ```json
   {
     "chat.pluginLocations": {
       "C:/tools/cdev": true
     }
   }
   ```

3. In VS Code, press Ctrl+Shift+P, run **Preferences: Open User Settings (JSON)**, and add that `chat.pluginLocations` entry (when the setting is already there, add the one line to it).

4. Restart VS Code. Typing `/` in agent chat now lists the `cdev-` commands.

## Option 2: inside one repository, travelling with it

This suits a team: everyone who clones the repository has the skills without touching their settings.

```
py -3 C:\tools\cdev\install_local.py --repo D:\work\my-project
```

The skills land in that repository's `.github/skills/`. Commit them, and a clone carries them.

For Claude Code, add `--tool claude`, which writes `.claude/skills/` instead.

## After installing

**The repository has no harness yet**: type `/cdev-init` once in agent chat. It detects the domains, writes AGENTS.md, the architecture documents, PROGRESS.md, and the feature list, then hands you the result to review.

**The repository already has an AGENTS.md**: skip init. The rules are already in the repository. When that harness came from an older version, run `/cdev-upgrade` once to add what is missing.

Read [README.md](README.md) for how the whole thing works.

## What you type day to day

**Most of the time, nothing.** The rules live in AGENTS.md, which Copilot loads on its own, so a new conversation opens with the agent reading `## Now` in PROGRESS.md, listing the features, running the document check, and asking which feature to take. While you work, it also keeps `## Now` and the architecture documents up to date.

These are the only commands you type, and each is occasional:

| Command | When |
|---|---|
| `/cdev-init` | once, the first time a repository uses cdev |
| `/cdev-upgrade` | once per repository, after the plugin is updated |
| `/cdev-checkpoint` | when the context usage runs high, or before a long break |
| `/cdev-done` | for a full wrap-up: the documents checked, the log written, a commit message drafted |
| `/cdev-session-start` | for the full opening pass, when the short one a new conversation already does is not enough |
| `/cdev-target-verify` | for a result from real hardware, at `Verification: full` |
| `/cdev-guide` | when you cannot remember which command fits |

`cdev-implement`, `cdev-review`, `cdev-debug`, `cdev-test-gap`, `cdev-architecture-sync`, and `cdev-feature` are reached by the agent itself, so they are nothing to remember.

One thing it leaves alone: when the build, test, or run command in AGENTS.md changes, you or the agent has to edit that line.

## Updating later

**On option 1**: unzip the new package over the old folder and restart VS Code.

**On option 2**: nothing to do. Whoever maintains it updates `.github/skills/` and commits, and `git pull` brings it to you.

Either way, when a repository's own harness files (AGENTS.md, the architecture documents) need the update too, run `/cdev-upgrade` in that repository. One person usually runs it and commits the result, so the others only pull.

## When something is wrong

- **`/` lists no cdev commands**: check that the path in `chat.pluginLocations` uses forward slashes (`C:/tools/cdev`), that the folder holds `plugin.json`, and that VS Code was restarted.
- **`py -3` is not found**: use `python`, or install Python 3 first.
- **The agent opens without reporting where the work stands**: the rule is in AGENTS.md and Copilot loads it, though following it is the model's call. Type `/cdev-session-start` for the full pass.
- **Skills start on their own**: `cdev-implement`, `cdev-review`, and `cdev-debug` are meant to.
