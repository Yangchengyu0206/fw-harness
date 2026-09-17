---
name: fw-harness-init
description: "Generate the fw-c-harness in this firmware repository: entry documents, state folders, verification gates, git hooks, and an ARCHITECTURE.md for every folder of C sources."
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

### 3. Generate everything, with no questions in between

```bash
py -3 harness/scripts/arch_sync.py scan
py -3 harness/scripts/arch_sync.py docs
py -3 harness/scripts/check.py
```

Nothing here is committed, so the whole result is still a draft the user can change or throw away. Run all three and collect what they said: the module list with each kind, the dependencies the scan pushed into the grandfather list, any source file at the repository root that belongs to no module, and what `check` reported.

**Done when:** all three commands have run and you hold their output, including the failures.

### 4. Hand the whole result over for review

Now ask, once, with the finished work on screen rather than a plan for it. Give the user four things and one question.

The modules, as one table:

| Module | Kind | May include | Note |
|---|---|---|---|
| src/app | owned | src/drivers | |
| src/hal | owned | third_party/cmsis | also includes src/app, recorded as grandfathered |
| third_party/cmsis | vendor | none | read-only |

In the Note column, flag what a user most often wants changed: a folder classified `vendor` or `generated` from its name alone, every grandfathered dependency, and every root level source file.

Then: what `check` said, step by step; what was created and every `.harness-proposed` file; and what is left to a person, which is the responsibility line of each ARCHITECTURE.md, the budgets in `harness/config.json`, and the incident table in CLAUDE.md.

The question is one question: which rows are wrong? A single answer covering every row is the human approval these rules need, and asking row by row is not more approval, only more typing. `git status` and `git diff` are open to the user the whole time, so they can read the real files rather than your summary.

For each correction they name: edit `harness/architecture.json`, then re-run `arch_sync.py docs` and `check.py`, then show the difference that made.

**Done when:** the user has answered once on the whole table, every correction they named is applied and re-verified, and every `check` failure is either fixed or explained with the command that reproduces it.

### 5. Commit

**Done when:** the install and the generated documents are committed together in one commit whose message starts with `harness:`, after the user has said to commit.
