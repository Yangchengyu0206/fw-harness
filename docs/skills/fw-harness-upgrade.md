# fw-harness-upgrade

User-invoked. Type `/fw-harness-upgrade`.

## What it does

Compares the repository against the templates of the installed plugin version. Managed files are replaced; files your team owns are left alone, with the new version offered as a proposal you walk through one at a time.

## When to reach for it

After the plugin updates, before starting work on the new version.

## Common questions

**What counts as managed?** The scripts under `harness/scripts/`, the git hooks, and the thin wrappers. Team-owned means AGENTS.md, CLAUDE.md, and the config, architecture, policy, and checklist files.

**I edited a script. Is it lost?** No. The upgrade compares the file with the hash recorded at install time, sees your edit, leaves your version in place, and writes the new one as a proposal.

**Can I see what would happen first?** Yes, `--dry-run` reports the version change and the four groups without writing anything.

## It is working if

No `.harness-proposed` file is left behind, `check` passes, and `harness/.harness-version` names the new version.
