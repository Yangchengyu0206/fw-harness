# Installing cdev offline

This package is the whole cdev plugin. It needs no marketplace and no access to GitHub.

繁體中文: [INSTALL.zh-TW.md](INSTALL.zh-TW.md)

Python 3 is required (`py -3` on Windows).

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

Unzip the new package over the old folder and restart VS Code. When a repository's own harness files need the update too, run `/cdev-upgrade` in that repository.

## When something is wrong

- **`/` lists no cdev commands**: check that the path in `chat.pluginLocations` uses forward slashes (`C:/tools/cdev`), that the folder holds `plugin.json`, and that VS Code was restarted.
- **`py -3` is not found**: use `python`, or install Python 3 first.
- **Skills start on their own**: `cdev-implement`, `cdev-review`, and `cdev-debug` are meant to. The other seven wait for you to type `/`.
