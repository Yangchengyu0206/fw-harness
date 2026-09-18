# cdev-upgrade

User-invoked. Type `/cdev-upgrade`.

## What it does

Brings a repository set up by an older version of the plugin up to the current shape: replaces the two scripts, adds the AGENTS.md sections, the `Verification:` line, the `## Now` fields, the `## Files` and `## Flows` sections, and the VS Code files, then hands you the whole diff. Sentences you wrote stay where they are.

## When to reach for it

After updating the plugin, once per repository.

## Common questions

**How does it know what my repository is missing?** It checks what the files hold, not a version number. Nothing records which version generated a repository, and running the skill twice changes nothing the second time.

**Will it overwrite my AGENTS.md?** It adds the sections that are missing and leaves your text alone. The two scripts under `tools/` belong to the plugin and are replaced, unless you edited one, in which case the new version lands beside it as `.cdev-proposed`.

**Do I have to document every folder again?** No. The folders you work in are written in full; the rest get the stub line, which `doc_check` reports as waiting, and `cdev-architecture-sync` fills one when the work reaches it.

## It is working if

`py -3 tools/doc_check.py` runs, AGENTS.md carries a `Verification:` line, and the diff shows additions rather than rewrites of what you wrote.
