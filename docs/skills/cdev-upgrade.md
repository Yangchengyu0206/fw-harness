# cdev-upgrade

User-invoked. Type `/cdev-upgrade`.

## What it does

Brings a repository set up by an older version of the plugin up to the current shape: replaces the four scripts under `tools/`, adds the missing AGENTS.md sections (including `## When this repository cannot answer`) and refreshes the sentences an older version wrote differently (the hook-aware opening, the `## Terms` pointer, the explorer delegation), adds the `Verification:` line, the `## Now` fields, `## Terms`, NOTES.md with its section in AGENTS.md, the `## Files` and `## Flows` sections, the session hooks, the explorer agent, and the VS Code files, then hands you the whole diff. Sentences you wrote stay where they are.

## When to reach for it

After updating the plugin, once per repository.

## Common questions

**How does it know what my repository is missing?** It checks what the files hold, not a version number. Nothing records which version generated a repository, and running the skill twice changes nothing the second time.

**Will it overwrite my AGENTS.md?** It adds the sections that are missing and leaves your text alone. The four scripts under `tools/` belong to the plugin and are replaced. The tree starts clean, so `git diff` shows what changed; where the copy would remove a change of yours, your file is kept and the new version lands beside it as `.cdev-proposed`.

**Do I have to document every folder again?** No. The folders you work in are written in full; the rest get the stub line, which `doc_check` reports as waiting, and `cdev-architecture-sync` fills one when the work reaches it.

## It is working if

`py -3 tools/doc_check.py` runs, AGENTS.md carries a `Verification:` line, and the diff shows additions rather than rewrites of what you wrote.
