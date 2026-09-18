---
name: cdev-upgrade
description: "Bring a repository's harness up to the plugin's current shape after a plugin update, adding what is missing and leaving what the user wrote alone."
disable-model-invocation: true
---

# cdev-upgrade

`cdev-init` never overwrites, so a repository set up by an older version keeps the older shape. This skill adds what the current version expects, one item at a time, and leaves every sentence the user wrote in place.

There is no version file. The check is what the repository has, not what it was generated from, so running this on an already current repository changes nothing.

The templates sit in [the init skill](../cdev-init/templates).

## Process

### 1. Confirm the target

Confirm the repository root with the user, and that `git status --porcelain` is empty, so the whole upgrade reads as one diff.

**Done when:** the user has confirmed the path and the working tree is clean.

### 2. Replace the scripts

`tools/feature.py` and `tools/doc_check.py` belong to the plugin. Copy both from the templates over whatever is there, and add `tools/doc_check.py` when the repository has none.

When the user has edited one of them, do not overwrite it: copy the new version beside it as `<name>.cdev-proposed`, and say so in step 5.

**Done when:** both scripts run: `py -3 tools/feature.py check` and `py -3 tools/doc_check.py`.

### 3. Add what is missing

Check each item. Add only the missing ones, taking the wording from the templates and the repository's own facts from the files it already has.

| Item | How to check | What to add |
|---|---|---|
| Rules in AGENTS.md | AGENTS.md holds the sections `## Verification`, `## Opening a conversation`, `## Answering questions about the code`, `## Keeping the context small`, `## What done means` | the missing sections, in the template's order |
| Verification level | AGENTS.md has a `Verification:` line | `Verification: off`, and tell the user in step 5 that `light` and `full` exist |
| CLAUDE.md | it holds one line, `@AGENTS.md` | move any rule it still holds into the matching AGENTS.md section, then replace the file with `@AGENTS.md` |
| Decisions table | the root ARCHITECTURE.md has `## Decisions and why` | the table, carrying over any rows from CLAUDE.md |
| `## Now` fields | PROGRESS.md's `## Now` has `Confirmed facts` and `Waiting on the user` | the two fields, left as `none` |
| Folder documents | each folder ARCHITECTURE.md has `## Files` and `## Flows` | for the folders the user works in, read the code and write both; for the rest, the `## Files` line from [ARCHITECTURE.stub.md](../cdev-init/templates/ARCHITECTURE.stub.md), so `doc_check` reports them as waiting |
| Editor settings | `.vscode/settings.json` holds `files.readonlyInclude` and `chat.tools.terminal.autoApprove` | the template's entries, merged into the existing file rather than replacing it |
| Path instructions | `.github/instructions/architecture.instructions.md` exists | the template, with `applyTo` covering the editable folders AGENTS.md lists |

Ask the user which folders they work in when AGENTS.md does not already make it plain, and document those in full.

**Done when:** every row is either present or added, and no sentence the user wrote has been deleted.

### 4. Verify

```bash
py -3 tools/feature.py check
py -3 tools/doc_check.py
```

**Done when:** `feature.py check` passes and `doc_check` reports drift only where the documents were already behind the code, with the stubs listed as waiting.

### 5. Hand it over

One message: what was added, what was left as a stub and why, every `.cdev-proposed` file with the difference it holds, and the `Verification:` level the repository now carries with the other two named. Then ask what is wrong, and apply each correction.

The commit is the user's to run.

**Done when:** the user has answered once, every correction is applied, and they have the diff in front of them.
