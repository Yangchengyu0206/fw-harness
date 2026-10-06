# Installing cdev offline

This package is the whole cdev plugin. It needs no marketplace and no access to GitHub.

繁體中文: [INSTALL.zh-TW.md](INSTALL.zh-TW.md)

Python 3 is required: `py -3` on Windows, `python3` on macOS and Linux. The scripts and the session hook that `/cdev-init` writes into a repository run on it.

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
     "chat.plugins.enabled": true,
     "chat.pluginLocations": {
       "C:/tools/cdev": true
     }
   }
   ```

3. In VS Code, press Ctrl+Shift+P, run **Preferences: Open User Settings (JSON)**, and add both entries (when `chat.pluginLocations` is already there, add the one line to it). Plugins stay off until `chat.plugins.enabled` is `true`.

4. Restart VS Code. Typing `/` in agent chat now lists the `cdev-` commands.

## Option 2: inside one repository, travelling with it

This suits a team: everyone who clones the repository has the skills without touching their settings. It is also the simplest route: copying needs no Python.

**Copy the folders:**

1. Make a `.github\skills` folder in your repository.
2. Copy every folder inside the unzipped `cdev\skills\` (`cdev-init`, `cdev-debug`, and the rest of the 14) into it.
3. Copy `LICENSE` and `THIRD_PARTY_NOTICES.md` in beside them, so the licence travels with the skills.
4. Restart VS Code and type `/` in agent chat to see the commands.
5. Commit them, and a clone carries them.

The result:

```
your-project\
└─ .github\skills\
   ├─ cdev-init\SKILL.md
   ├─ cdev-debug\SKILL.md
   └─ ... (14 in total)
```

**To do the same without copying by hand:**

```
py -3 C:\tools\cdev\install_local.py --repo D:\work\my-project
```

For Claude Code, add `--tool claude`, which writes `.claude/skills/` instead.

This step carries the skills only. The hooks, the explorer agent, and the VS Code settings are written by `/cdev-init`, described next.

## After installing

**The repository has no harness yet**: type `/cdev-init` once in agent chat. It detects the domains, writes AGENTS.md, the architecture documents, PROGRESS.md, and the feature list, then hands you the result to review.

**The repository already has an AGENTS.md**: skip init. The rules are already in the repository. When that harness came from an older version, run `/cdev-upgrade` once to add what is missing.

Read [README.md](README.md) for how the whole thing works.

## What you type day to day

**Most of the time, nothing.** In VS Code, a session hook hands the agent `## Now` from PROGRESS.md, the feature list, and the document check before its first answer, so a new conversation opens knowing where the work stands and asks which feature to take. Where hooks do not run (Claude Code, or with hooks turned off), the rules in AGENTS.md have the agent do the same itself. While you work, it also keeps `## Now` and the architecture documents up to date.

These are the only commands you type, and each is occasional:

| Command | When |
|---|---|
| `/cdev-init` | once, the first time a repository uses cdev |
| `/cdev-upgrade` | once per repository, after the plugin is updated |
| `/cdev-grill` | before a piece of work whose plan rests on assumptions nobody has said out loud |
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

- **`/` lists no cdev commands**: check that `chat.plugins.enabled` is `true`, that the path in `chat.pluginLocations` uses forward slashes (`C:/tools/cdev`), that the folder holds `plugin.json`, and that VS Code was restarted.
- **`py -3` is not found**: on Windows, install Python 3 from python.org with the `py` launcher; a bare `python` is often the Microsoft Store stub, and the session hook calls `py -3`. On macOS and Linux, use `python3`.
- **The agent opens without reporting where the work stands**: agent hooks are a preview feature in VS Code. Check that the repository has `.github/hooks/cdev.json` (written by `/cdev-init` or `/cdev-upgrade`) and that `py -3 tools/hooks.py session-start` prints JSON. Without the hook, the rule in AGENTS.md still asks for the opening, though following it is the model's call. Type `/cdev-session-start` for the full pass.
- **Skills start on their own**: `cdev-implement`, `cdev-review`, and `cdev-debug` are meant to.
