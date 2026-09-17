---
name: fw-harness-upgrade
description: "Update this repository's harness after a plugin update, applying managed files and reviewing team-owned changes one at a time."
disable-model-invocation: true
---

# fw-harness-upgrade

Managed files (the scripts, the git hooks, the wrappers) belong to the plugin, so the upgrade replaces them. Team-owned files (AGENTS.md, CLAUDE.md, the config and policy files) belong to the repository, so the upgrade proposes and never replaces.

## Process

### 1. Show what would change

```bash
py -3 harness/scripts/upgrade.py --templates "<this plugin>/skills/fw-harness-init/templates" --dry-run
```

**Done when:** the user has seen the version it moves from and to, and the count in each group.

### 2. Apply it

Run the same command without `--dry-run`. A managed file the team edited locally is not overwritten: it is reported, and its new version lands as `<name>.harness-proposed`.

**Done when:** the command exits zero and every proposal is listed.

### 3. Walk the proposals one at a time

For each `.harness-proposed` file, show the user the difference and ask what to keep:

```bash
git diff --no-index <name> <name>.harness-proposed
```

Apply the user's answer, then delete the proposal file. A team-owned file is theirs, so the decision is theirs to make item by item.

**Done when:** no `.harness-proposed` file remains and the user has answered for each one.

### 4. Verify

```bash
py -3 harness/scripts/check.py
```

**Done when:** `check` passes and the upgrade is committed with a message that starts with `harness:`.
