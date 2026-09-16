---
name: fw-harness-init
description: Generate the fw-c-harness in this firmware repository: entry documents, state folders, verification gates, git hooks, and an ARCHITECTURE.md for every folder of C sources.
disable-model-invocation: true
---

# fw-harness-init

Writes the harness into the repository you are standing in. It creates files and never overwrites them: an existing file keeps its content, and the new version lands beside it as `<name>.harness-proposed`.

Run this once per repository. `fw-harness-upgrade` handles every later plugin version.

## Process

### 1. Confirm the target

Confirm with the user: the repository root, that the working tree is clean, and that `git config user.name` and `user.email` are set. A dirty tree makes the install hard to review, and missing identity breaks every state write later.

**Done when:** the user has confirmed the path, `git status --porcelain` is empty, and both git identity values print.

### 2. Install the files

Run the installer with the plugin's templates folder, which sits beside this skill:

```bash
py -3 "<this skill>/templates/harness/scripts/install.py" --templates "<this skill>/templates"
```

Report its summary to the user: how many files were created, which settings files were merged, and every proposal it wrote.

**Done when:** the summary is shown and every `.harness-proposed` file is named to the user, with the reason it exists.

### 3. Draft the architecture

```bash
py -3 harness/scripts/arch_sync.py scan
```

Show the user the module list, each module's kind, and every dependency the scan pushed into the grandfather list. Ask them to confirm or correct the kinds and the layer order, then edit `harness/architecture.json` to match their answer. Approved rules are a human decision, so take the answer from the user rather than from the draft.

**Done when:** every module has a kind the user confirmed, and every grandfathered dependency is one the user knows about.

### 4. Write the documents

```bash
py -3 harness/scripts/arch_sync.py docs
```

**Done when:** every module folder holds an ARCHITECTURE.md and the repository root holds the map.

### 5. Verify and hand back

```bash
py -3 harness/scripts/check.py
```

Fix what the gates report, or tell the user which gate needs a toolchain they have yet to install. Then list what is left to them: the responsibility line of each ARCHITECTURE.md, the incident table in CLAUDE.md, and the budgets in `harness/config.json`.

**Done when:** `check` passes or every failure is explained to the user with the command that reproduces it, and the install plus the generated documents are committed together in one commit whose message starts with `harness:`.
