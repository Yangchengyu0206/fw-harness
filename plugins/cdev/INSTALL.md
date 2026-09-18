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

## Updating later

**On option 1**: unzip the new package over the old folder and restart VS Code.

**On option 2**: nothing to do. Whoever maintains it updates `.github/skills/` and commits, and `git pull` brings it to you.

Either way, when a repository's own harness files (AGENTS.md, the architecture documents) need the update too, run `/cdev-upgrade` in that repository. One person usually runs it and commits the result, so the others only pull.

## When something is wrong

- **`/` lists no cdev commands**: check that the path in `chat.pluginLocations` uses forward slashes (`C:/tools/cdev`), that the folder holds `plugin.json`, and that VS Code was restarted.
- **`py -3` is not found**: use `python`, or install Python 3 first.
- **Skills start on their own**: `cdev-implement`, `cdev-review`, and `cdev-debug` are meant to. The other seven wait for you to type `/`.
