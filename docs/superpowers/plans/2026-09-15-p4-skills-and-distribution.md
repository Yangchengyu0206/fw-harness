# Plan 4: Skills and Distribution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the plugin: thirteen skills, a manifest for each of the two tools, a marketplace manifest for each, a human-facing page per skill, both READMEs, third party notices, and a manual checklist for the loop no test can run.

**Architecture:** The scripts from plans 1 to 3 hold every rule; the skills are thin and point at them, so a rule lives in one place. Each skill is `plugins/fw-c-harness/skills/<name>/SKILL.md`, with material only some branches need pushed into sibling reference files. One git repository is a marketplace for both tools: `.claude-plugin/marketplace.json` and `.github/plugin/marketplace.json` at the repo root both point at `plugins/fw-c-harness`, which carries a manifest for each tool. A pytest module validates every skill and both manifests mechanically, so a rename or a missing page fails the suite instead of a user's install.

**Tech Stack:** Markdown with YAML frontmatter, JSON manifests, Python 3.9+ standard library, pytest.

**Spec:** `docs/superpowers/specs/2026-09-15-fw-c-harness-plugin-design.md`, sections 1, 2, 3, 7, 9, 10.

**Split (this plan is 4 of 4):**
1. Identity, tickets, and state scripts (done)
2. Verification gates (done)
3. Harness generation and templates (done)
4. Skills and distribution (this plan)

## Verified formats

These were checked against real repositories rather than assumed. Both CLIs are absent from this machine, so the manifests are verified by the tests in Task 1 and by the manual checklist at the end.

**Claude Code** (from `mattpocock/skills`): marketplace at `.claude-plugin/marketplace.json` with `name`, `owner`, `description`, and `plugins[]`, each entry carrying `name`, `source` (a repo-relative path), `description`, `category`, `keywords`. Plugin manifest at `<plugin>/.claude-plugin/plugin.json` with `name`, `version`, `description`, `author`, `homepage`, `repository`, `license`, `keywords`, and an explicit `skills` array of paths. Verified with `claude plugin validate . --strict`.

**Copilot** (from `github/awesome-copilot`): marketplace at `.github/plugin/marketplace.json` with `name`, `metadata` (`description`, `version`), `owner`, and `plugins[]`; a plugin that lives in this repository is one entry with `name`, `source` (a repo-relative path string), `description`, `version`. Plugin manifest at `<plugin>/plugin.json` following the Agent Plugins schema 1.0.0: `$schema` and `name` are required, `additionalProperties` is false, and the allowed keys are `$schema`, `name`, `version`, `description`, `author`, `homepage`, `repository`, `license`, `keywords`, `extensions`. Standard skills are discovered from the plugin's `skills/` folder, so no list is needed and no list is allowed at the top level. Installed with `copilot plugin marketplace add <owner>/<repo>` then `copilot plugin install fw-c-harness@fw-harness`.

**SKILL.md frontmatter that satisfies both**: `name` (lowercase letters, digits, and hyphens, at most 64 characters, equal to the folder name), `description` (10 to 1024 characters), and for a user-invoked skill `disable-model-invocation: true`. Claude Code honours that key. Copilot's own validator accepts unknown keys and ignores this one, so on Copilot the agent can still reach the skill by itself. The README says so plainly rather than pretending the two behave the same.

## Global Constraints

- English only in skills, manifests, code, and test data. Chinese appears only in `docs/**.zh-TW.md` and `README.zh-TW.md`.
- No em-dashes in any prose this repository ships. Tests enforce it.
- A rule lives in one place. A skill points at `harness/scripts/*.py`, `harness/review-checklist.json`, `harness/review-policy.json`, or `harness/architecture.json` instead of restating what they hold.
- A user-invoked skill sets `disable-model-invocation: true` and its `description` is one human-facing line with no trigger list. A model-invoked skill omits the key and its `description` front-loads distinct triggers, one per case, ending with a sentence that starts "Use when".
- Every step in a skill ends on a completion criterion the agent can check, worded to demand thorough work.
- Positive phrasing. A prohibition appears only as a hard guardrail, paired with the positive target.
- Content adapted from `github/awesome-copilot` or `mattpocock/skills` (both MIT) names its source in the file and in `THIRD_PARTY_NOTICES.md`.
- The plugin version is one value: `plugins/fw-c-harness/skills/fw-harness-init/templates/VERSION`. Both plugin manifests and the Copilot marketplace entry carry the same string.
- Commit messages in English, and each task ends with a commit.

## File Structure

`ROOT` = `C:\Users\YANG\Desktop\fw-harness`, `PLUGIN` = `plugins/fw-c-harness`, `SKILLS` = `PLUGIN/skills`.

| File | Responsibility |
|---|---|
| `.claude-plugin/marketplace.json` | Claude Code marketplace pointing at `PLUGIN` |
| `.github/plugin/marketplace.json` | Copilot marketplace pointing at `PLUGIN` |
| `PLUGIN/.claude-plugin/plugin.json` | Claude manifest, explicit `skills` array |
| `PLUGIN/plugin.json` | Copilot manifest, Agent Plugins schema |
| `PLUGIN/README.md` | Install and update steps for both tools |
| `SKILLS/<name>/SKILL.md` | One per skill, thirteen in total |
| `SKILLS/fw-c-implement/{embedded-c-rules,isr-concurrency,memory-budget,module-template}.md` | Disclosed reference for the implementation skill |
| `SKILLS/fw-c-review/report-format.md` | Disclosed reference for the review report |
| `docs/skills/<name>.md` | One human-facing page per skill |
| `docs/manual-checklist.md` | The loop run once by hand in each tool |
| `README.md`, `README.zh-TW.md` | Project readme and its translation |
| `THIRD_PARTY_NOTICES.md` | Attribution for adapted content |
| `tests/plugin/test_skills.py` | Frontmatter, invocation, links, and prose rules |
| `tests/plugin/test_manifests.py` | Both marketplaces, both manifests, versions |
| `tests/plugin/test_docs.py` | A page per skill, readme parity, notices |

The thirteen skill names, with their invocation:

| Skill | Invocation |
|---|---|
| `fw-harness-init` | user |
| `fw-harness-upgrade` | user |
| `fw-architecture-sync` | model |
| `fw-session-start` | user |
| `fw-ticket` | model |
| `fw-hil-verify` | user |
| `fw-done` | user |
| `fw-c-implement` | model |
| `fw-c-review` | model |
| `fw-c-test-gap` | model |
| `fw-c-debug` | model |
| `fw-misra-deviation` | model |
| `fw-guide` | user |

---

### Task 1: Validation tests and the four manifests

**Files:**
- Create: `tests/plugin/test_skills.py`, `tests/plugin/test_manifests.py`
- Create: `.claude-plugin/marketplace.json`, `.github/plugin/marketplace.json`
- Create: `plugins/fw-c-harness/.claude-plugin/plugin.json`, `plugins/fw-c-harness/plugin.json`
- Create: `SKILLS/fw-guide/SKILL.md` (a placeholder body, replaced in Task 7, so the suite has one real skill to validate from the start)

**Interfaces:**
- Consumes: `helpers.ROOT`, `helpers.TEMPLATES`
- Produces:
  - `tests/plugin/skilltools.py` with `PLUGIN`, `SKILLS`, `SKILL_NAMES` (the thirteen, in the table order), `USER_INVOKED` (a set), `frontmatter(path) -> dict`, `body(path) -> str`, `prose_files() -> list[Path]`
  - `frontmatter` parses the leading `---` block as one `key: value` per line, stripping one layer of matching single or double quotes. It raises `AssertionError` when a file has no frontmatter block.

- [ ] **Step 1: Write the test helper**

Create `tests/plugin/skilltools.py`:

```python
from pathlib import Path

from helpers import ROOT

PLUGIN = ROOT / "plugins" / "fw-c-harness"
SKILLS = PLUGIN / "skills"
DOCS = ROOT / "docs" / "skills"

SKILL_NAMES = (
    "fw-harness-init",
    "fw-harness-upgrade",
    "fw-architecture-sync",
    "fw-session-start",
    "fw-ticket",
    "fw-hil-verify",
    "fw-done",
    "fw-c-implement",
    "fw-c-review",
    "fw-c-test-gap",
    "fw-c-debug",
    "fw-misra-deviation",
    "fw-guide",
)
USER_INVOKED = {
    "fw-harness-init", "fw-harness-upgrade", "fw-session-start",
    "fw-hil-verify", "fw-done", "fw-guide",
}


def skill_path(name):
    return SKILLS / name / "SKILL.md"


def existing_skills():
    return [name for name in SKILL_NAMES if skill_path(name).is_file()]


def split(path):
    text = Path(path).read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path} has no frontmatter block"
    end = text.index("\n---\n", 3)
    return text[4:end], text[end + 5:]


def frontmatter(path):
    block, _ = split(path)
    fields = {}
    for line in block.splitlines():
        if not line.strip():
            continue
        key, _, value = line.partition(":")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        fields[key.strip()] = value
    return fields


def body(path):
    return split(path)[1]


def prose_files():
    """Every Markdown file this repository ships, minus the plans and specs."""
    found = [path for path in SKILLS.rglob("*.md")]
    found += [path for path in DOCS.glob("*.md")]
    found += [PLUGIN / "README.md", ROOT / "README.md", ROOT / "README.zh-TW.md",
              ROOT / "THIRD_PARTY_NOTICES.md", ROOT / "docs" / "manual-checklist.md"]
    return [path for path in found if path.is_file()]
```

- [ ] **Step 2: Write the failing skill tests**

Create `tests/plugin/test_skills.py`:

```python
import re

import pytest

from skilltools import SKILLS, SKILL_NAMES, USER_INVOKED, body, existing_skills, frontmatter, prose_files, skill_path

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def test_every_skill_folder_is_expected():
    folders = sorted(path.name for path in SKILLS.iterdir() if path.is_dir())
    assert folders == sorted(SKILL_NAMES)


@pytest.mark.parametrize("name", SKILL_NAMES)
def test_skill_exists(name):
    assert skill_path(name).is_file(), f"{name}/SKILL.md is missing"


@pytest.mark.parametrize("name", existing_skills())
def test_name_matches_the_folder(name):
    fields = frontmatter(skill_path(name))
    assert fields["name"] == name and NAME_RE.match(fields["name"])
    assert len(fields["name"]) <= 64


@pytest.mark.parametrize("name", existing_skills())
def test_description_length_suits_both_tools(name):
    description = frontmatter(skill_path(name))["description"]
    assert 10 <= len(description) <= 1024, f"{name}: description is {len(description)} characters"


@pytest.mark.parametrize("name", existing_skills())
def test_invocation_matches_the_plan(name):
    fields = frontmatter(skill_path(name))
    if name in USER_INVOKED:
        assert fields.get("disable-model-invocation") == "true"
        assert "Use when" not in fields["description"], "a user-invoked description carries no trigger list"
    else:
        assert "disable-model-invocation" not in fields
        assert "Use when" in fields["description"], "a model-invoked description names its triggers"


@pytest.mark.parametrize("name", existing_skills())
def test_skill_points_at_the_scripts_rather_than_restating_rules(name):
    text = body(skill_path(name))
    assert "TODO" not in text and "TBD" not in text


@pytest.mark.parametrize("name", existing_skills())
def test_relative_links_resolve(name):
    path = skill_path(name)
    for target in LINK_RE.findall(body(path)):
        if target.startswith(("http://", "https://", "#")):
            continue
        assert (path.parent / target.split("#")[0]).exists(), f"{name}: broken link {target}"


def test_no_em_dash_in_shipped_prose():
    offenders = [str(path) for path in prose_files() if "\u2014" in path.read_text(encoding="utf-8")]
    assert offenders == []
```

- [ ] **Step 3: Write the failing manifest tests**

Create `tests/plugin/test_manifests.py`:

```python
import json

import pytest

from helpers import ROOT, TEMPLATES
from skilltools import PLUGIN, SKILL_NAMES

CLAUDE_MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
CLAUDE_PLUGIN = PLUGIN / ".claude-plugin" / "plugin.json"
COPILOT_MARKETPLACE = ROOT / ".github" / "plugin" / "marketplace.json"
COPILOT_PLUGIN = PLUGIN / "plugin.json"
COPILOT_KEYS = {"$schema", "name", "version", "description", "author", "homepage",
                "repository", "license", "keywords", "extensions"}
PLUGIN_NAME = "fw-c-harness"
MARKETPLACE_NAME = "fw-harness"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def version():
    return (TEMPLATES / "VERSION").read_text(encoding="utf-8").strip()


def test_claude_marketplace_points_at_the_plugin():
    data = load(CLAUDE_MARKETPLACE)
    assert data["name"] == MARKETPLACE_NAME and data["owner"]["name"]
    entry, = data["plugins"]
    assert entry["name"] == PLUGIN_NAME
    assert (ROOT / entry["source"].lstrip("./")).is_dir()
    assert entry["description"] and entry["keywords"]


def test_claude_plugin_lists_every_skill_once():
    data = load(CLAUDE_PLUGIN)
    assert data["name"] == PLUGIN_NAME and data["license"] == "MIT"
    listed = data["skills"]
    assert listed == sorted(listed) and len(listed) == len(set(listed))
    assert sorted(path.rsplit("/", 1)[-1] for path in listed) == sorted(SKILL_NAMES)
    for path in listed:
        assert (PLUGIN / path.lstrip("./")).is_dir(), path


def test_copilot_marketplace_points_at_the_plugin():
    data = load(COPILOT_MARKETPLACE)
    assert data["name"] == MARKETPLACE_NAME and data["metadata"]["description"]
    entry, = data["plugins"]
    assert entry["name"] == PLUGIN_NAME and entry["version"] == version()
    assert (ROOT / entry["source"]).is_dir()


def test_copilot_plugin_uses_only_schema_keys():
    data = load(COPILOT_PLUGIN)
    assert data["$schema"] == "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
    assert data["name"] == PLUGIN_NAME
    assert set(data) <= COPILOT_KEYS, f"keys outside the schema: {set(data) - COPILOT_KEYS}"


def test_both_manifests_carry_the_template_version():
    assert load(CLAUDE_PLUGIN)["version"] == version()
    assert load(COPILOT_PLUGIN)["version"] == version()
```

- [ ] **Step 4: Run the tests and watch them fail**

Run: `py -3 -m pytest tests/plugin -q`
Expected: FAIL. `test_skills.py` cannot collect until `SKILLS/fw-guide/SKILL.md` exists, and every manifest test fails on a missing file.

- [ ] **Step 5: Create the placeholder skill so collection works**

Create `SKILLS/fw-guide/SKILL.md`:

```markdown
---
name: fw-guide
description: Ask which fw-harness skill fits your situation.
disable-model-invocation: true
---

# fw-guide

Task 7 of this plan replaces this body with the router.
```

- [ ] **Step 6: Create `.claude-plugin/marketplace.json`**

```json
{
  "name": "fw-harness",
  "owner": {
    "name": "fw-harness contributors",
    "url": "https://github.com/Yangchengyu0206/fw-harness"
  },
  "description": "A harness and skills for C firmware teams, for Claude Code and GitHub Copilot.",
  "plugins": [
    {
      "name": "fw-c-harness",
      "source": "./plugins/fw-c-harness",
      "description": "Generates a verification harness into a C firmware repository and adds skills for the whole work loop: session start, tickets, implementation, review, debugging, and wrap up.",
      "category": "engineering",
      "keywords": ["firmware", "embedded", "c", "misra", "code-review", "harness"]
    }
  ]
}
```

- [ ] **Step 7: Create `.github/plugin/marketplace.json`**

```json
{
  "name": "fw-harness",
  "metadata": {
    "description": "A harness and skills for C firmware teams, for Claude Code and GitHub Copilot.",
    "version": "1.0.0"
  },
  "owner": {
    "name": "fw-harness contributors",
    "url": "https://github.com/Yangchengyu0206/fw-harness"
  },
  "plugins": [
    {
      "name": "fw-c-harness",
      "source": "plugins/fw-c-harness",
      "description": "Generates a verification harness into a C firmware repository and adds skills for the whole work loop: session start, tickets, implementation, review, debugging, and wrap up.",
      "version": "0.1.0"
    }
  ]
}
```

- [ ] **Step 8: Create `plugins/fw-c-harness/.claude-plugin/plugin.json`**

```json
{
  "name": "fw-c-harness",
  "version": "0.1.0",
  "description": "A harness for C firmware teams: verification gates, ticket state with per-person identity, generated ARCHITECTURE.md, and skills for the whole work loop.",
  "author": {
    "name": "fw-harness contributors",
    "url": "https://github.com/Yangchengyu0206/fw-harness"
  },
  "homepage": "https://github.com/Yangchengyu0206/fw-harness",
  "repository": "https://github.com/Yangchengyu0206/fw-harness",
  "license": "MIT",
  "keywords": ["firmware", "embedded", "c", "misra", "code-review", "harness"],
  "skills": [
    "./skills/fw-architecture-sync",
    "./skills/fw-c-debug",
    "./skills/fw-c-implement",
    "./skills/fw-c-review",
    "./skills/fw-c-test-gap",
    "./skills/fw-done",
    "./skills/fw-guide",
    "./skills/fw-harness-init",
    "./skills/fw-harness-upgrade",
    "./skills/fw-hil-verify",
    "./skills/fw-misra-deviation",
    "./skills/fw-session-start",
    "./skills/fw-ticket"
  ]
}
```

- [ ] **Step 9: Create `plugins/fw-c-harness/plugin.json`**

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
  "name": "fw-c-harness",
  "version": "0.1.0",
  "description": "A harness for C firmware teams: verification gates, ticket state with per-person identity, generated ARCHITECTURE.md, and skills for the whole work loop.",
  "author": {
    "name": "fw-harness contributors",
    "url": "https://github.com/Yangchengyu0206/fw-harness"
  },
  "homepage": "https://github.com/Yangchengyu0206/fw-harness",
  "repository": "https://github.com/Yangchengyu0206/fw-harness",
  "license": "MIT",
  "keywords": ["firmware", "embedded", "c", "misra", "code-review", "harness"]
}
```

- [ ] **Step 10: Run the tests**

Run: `py -3 -m pytest tests/plugin -q`
Expected: the manifest tests PASS; `test_skill_exists` still fails for the twelve skills Tasks 2 to 7 create. That is the plan working: those failures are the remaining work, and they disappear one task at a time.

- [ ] **Step 11: Commit**

```bash
git add tests/plugin .claude-plugin .github/plugin plugins/fw-c-harness/.claude-plugin plugins/fw-c-harness/plugin.json plugins/fw-c-harness/skills/fw-guide
git commit -m "Add plugin and marketplace manifests for both tools, with validation tests"
```

---

### Task 2: Harness lifecycle skills

**Files:**
- Create: `SKILLS/fw-harness-init/SKILL.md`, `SKILLS/fw-harness-upgrade/SKILL.md`, `SKILLS/fw-architecture-sync/SKILL.md`

**Interfaces:**
- Consumes: `harness/scripts/install.py`, `upgrade.py`, `arch_sync.py` from plan 3
- Produces: the three lifecycle skills the tests in Task 1 check

Note: `SKILLS/fw-harness-init/` already holds `templates/`. Adding `SKILL.md` beside it completes the skill.

- [ ] **Step 1: Write `SKILLS/fw-harness-init/SKILL.md`**

```markdown
---
name: fw-harness-init
description: Generate the fw-c-harness in this firmware repository: entry documents, state folders, verification gates, git hooks, and an ARCHITECTURE.md for every folder of C sources.
disable-model-invocation: true
---

# fw-harness-init

Writes the harness into the repository you are standing in. It creates files, never overwrites them: an existing file keeps its content and the new version lands beside it as `<name>.harness-proposed`.

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

Fix what the gates report, or tell the user which gate needs a toolchain they have yet to install. Then list for the user what is left to them: filling in the responsibility line of each ARCHITECTURE.md, the incident table in CLAUDE.md, and the budgets in `harness/config.json`.

**Done when:** `check` passes or every failure is explained to the user with the command that reproduces it, and the install plus the generated documents are committed together in one commit whose message starts with `harness:`.
```

- [ ] **Step 2: Write `SKILLS/fw-harness-upgrade/SKILL.md`**

```markdown
---
name: fw-harness-upgrade
description: Update this repository's harness after a plugin update, applying managed files and reviewing team-owned changes one at a time.
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

Run the same command without `--dry-run`. A managed file the team edited locally is not overwritten: it is reported and its new version lands as `<name>.harness-proposed`.

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
```

- [ ] **Step 3: Write `SKILLS/fw-architecture-sync/SKILL.md`**

```markdown
---
name: fw-architecture-sync
description: Refresh harness/architecture.json and the generated block in every ARCHITECTURE.md from the real directory tree. Use when arch_check fails, when a new folder of C sources appears, when a generated architecture block disagrees with the json, or when the user asks to update the architecture documents.
---

# fw-architecture-sync

`harness/architecture.json` is the single source of approved rules. Each ARCHITECTURE.md renders that json inside a marked block; the human-written sections around the block stay untouched. This skill regenerates the block and drafts entries for what the tree has grown.

Approved rules are a human decision. This skill drafts, and a human approves.

## Process

### 1. Read the failure

Run `py -3 harness/scripts/arch_check.py` and read what it says. It names one of four situations: a folder with C sources belongs to no module, an include breaks an approved rule, a block disagrees with the json, or the grandfather list grew.

**Done when:** you can state which of the four the repository is in, quoting the line that says so.

### 2. Handle it

- **A folder belongs to no module**: run `py -3 harness/scripts/arch_sync.py scan`. On a repository whose json already holds approved rules, the draft lands at `harness/architecture.json.harness-proposed`. Compare it with the current file and carry over only the new module, with the kind and dependencies the user confirms.
- **An include breaks an approved rule**: removing the include is the fix. Propose the change that lets the module keep its layer, and reach for the grandfather list only when the user says the dependency stays.
- **A block disagrees with the json**: run `py -3 harness/scripts/arch_sync.py docs`.
- **The grandfather list grew**: the list may only shrink, so restore the removed entries or remove the new dependency. Show the user `git diff harness/architecture.json` and let them choose.

**Done when:** the situation you named in step 1 is addressed, with a human answer for every approved rule you changed.

### 3. Fill in what a script cannot

A newly created ARCHITECTURE.md carries a responsibility line written from the file listing. Replace it with the one sentence a new colleague needs, and fill in entry points and the ISR and memory notes from the code you can read.

**Done when:** every document you created in this run has a responsibility line that names what the module does, not how many files it holds.

### 4. Verify

```bash
py -3 harness/scripts/arch_check.py
```

**Done when:** `arch_check` passes, or its remaining failure is one the user has decided to answer another way.
```

- [ ] **Step 4: Run the tests**

Run: `py -3 -m pytest tests/plugin -q`
Expected: the three lifecycle skills now pass every check; the remaining failures are the nine skills Tasks 3 to 7 create.

- [ ] **Step 5: Commit**

```bash
git add plugins/fw-c-harness/skills/fw-harness-init/SKILL.md plugins/fw-c-harness/skills/fw-harness-upgrade plugins/fw-c-harness/skills/fw-architecture-sync
git commit -m "Add the harness lifecycle skills"
```

---

### Task 3: Work loop skills

**Files:**
- Create: `SKILLS/fw-session-start/SKILL.md`, `SKILLS/fw-ticket/SKILL.md`, `SKILLS/fw-hil-verify/SKILL.md`, `SKILLS/fw-done/SKILL.md`

**Interfaces:**
- Consumes: `harness/scripts/ticket.py`, `check.py`, `init_check.py`, `index.py` from plans 1 and 2
- Produces: the four work loop skills

- [ ] **Step 1: Write `SKILLS/fw-session-start/SKILL.md`**

```markdown
---
name: fw-session-start
description: Start a firmware session: verify the environment, read your handoff and the recent history, and agree with the user which ticket you are taking.
disable-model-invocation: true
---

# fw-session-start

Six steps, in order. The last one is a question for the user, not a decision for you.

## Process

### 1. Confirm where and who you are

Print the repository root, the current branch, and `git config user.name` and `user.email`. Every state write records that identity, so a wrong identity quietly attributes your work to someone else.

**Done when:** all four values are printed and the user has not corrected them.

### 2. Verify the environment

```bash
sh init.sh
```

On Windows PowerShell, run `.\init.ps1`. It checks Python, identity, `core.hooksPath`, the harness layout, the toolchain, and then runs `check` once.

**Done when:** `init` exits zero, or every `[FAIL]` line is reported to the user with the fix it names.

### 3. Read your handoff

Read `harness/handoff/<your-slug>.md`. It holds what the previous session of yours left behind.

**Done when:** you can state the goal, the blockers, and the suggested next step it records, or you have confirmed the file does not exist yet.

### 4. Read the recent history

Read the last three files in `harness/progress/` and run `git log --oneline -10`.

**Done when:** you can name what changed in the repository since your handoff was written.

### 5. List the candidates

Read `feature_list.json` (run `py -3 harness/scripts/index.py` first if it is missing). Present, in this order: your own `active` ticket, then `verifying` tickets that still owe work, then the `next` queue by priority.

**Done when:** the list is presented with each ticket's id, title, status, and assignee.

### 6. Agree on the ticket

Ask the user which ticket to take, and take that answer. When it is not already yours, claim it:

```bash
py -3 harness/scripts/ticket.py claim FW-NNNN
```

When you are taking over someone else's ticket, read their handoff at `harness/handoff/<their-slug>.md` first.

**Done when:** the user has named the ticket, it is `active` with you as the assignee, and you have read its `user_visible_behavior` and `verification_steps` back to the user before any code is written.
```

- [ ] **Step 2: Write `SKILLS/fw-ticket/SKILL.md`**

```markdown
---
name: fw-ticket
description: Create, claim, move, and add evidence to the tickets in harness/tickets. Use when the user asks for a new ticket, asks to claim or move one, mentions an FW-NNNN id, or when a check run or a review produces evidence that belongs on a ticket.
---

# fw-ticket

`harness/scripts/ticket.py` is the only way state changes. It fills in the identity and the time from git, and it enforces the transitions, so it is the tool for every write here. Editing a ticket file by hand skips the rules it exists to apply.

## Commands

```bash
py -3 harness/scripts/ticket.py new "<title>" --area <area> [--priority N] [--no-hil]
py -3 harness/scripts/ticket.py claim FW-NNNN
py -3 harness/scripts/ticket.py move FW-NNNN <status>
py -3 harness/scripts/ticket.py block FW-NNNN "<reason>"
py -3 harness/scripts/ticket.py unblock FW-NNNN
py -3 harness/scripts/ticket.py evidence FW-NNNN review --ref <path> --open-critical N
py -3 harness/scripts/ticket.py dod FW-NNNN
py -3 harness/scripts/ticket.py show FW-NNNN
```

`check` records its own evidence: `py -3 harness/scripts/check.py --record FW-NNNN`, on a clean working tree.

## Rules this skill follows

- **A new ticket names user visible behaviour.** Write `user_visible_behavior` as what the product does differently, and `verification_steps` as the checks that prove it, one host check and one board check where the ticket needs a board.
- **One active ticket per person.** When the user asks for a second one, say which ticket is already active and ask which one they want.
- **`done` belongs to a human.** Run `ticket.py dod FW-NNNN` to show what the ticket still owes, and leave the transition to the user: the command asks for typed confirmation in a terminal. Say so plainly rather than trying it.
- **Blocked tickets carry a reason.** `block` requires one, and unblocking returns the ticket to the status it came from.

**Done when:** the command exits zero, and you have read back the ticket's new status and what it still owes.
```

- [ ] **Step 3: Write `SKILLS/fw-hil-verify/SKILL.md`**

```markdown
---
name: fw-hil-verify
description: Pay off the board verification a ticket still owes: flash it, capture the serial log, and record the evidence.
disable-model-invocation: true
---

# fw-hil-verify

A human flashes the board and watches it. This skill supplies the commands, collects the log, and records the evidence, so the ticket can carry proof rather than a claim.

## Process

### 1. Read what the ticket owes

```bash
py -3 harness/scripts/ticket.py dod FW-NNNN
```

Read `verification_steps` and `dod_pending` and pick the board step you are about to run.

**Done when:** you can state, in one sentence, what the board must show for this step to pass.

### 2. Give the user the commands

Take the flash and serial commands from `harness/config.json` when the team has recorded them there, and otherwise ask the user for the ones they use. Present the exact commands, the expected output, and where the log will be written:

```
harness/evidence/FW-NNNN/<step>-<date>.log
```

**Done when:** the user has the commands and has confirmed which board and build they are running.

### 3. Capture the log

Ask the user to save the serial capture to that path, or save the output they paste. Keep the whole capture, including the timestamps and the failing lines.

**Done when:** the log file exists, and you can quote the lines in it that show the expected behaviour.

### 4. Record the evidence

```bash
py -3 harness/scripts/ticket.py evidence FW-NNNN hil --ref harness/evidence/FW-NNNN/<step>-<date>.log
```

Then remove the step you just paid off from `dod_pending`.

**Done when:** `ticket.py show FW-NNNN` lists the hil evidence, `dod_pending` no longer names this step, and you have told the user what the ticket still owes.
```

- [ ] **Step 4: Write `SKILLS/fw-done/SKILL.md`**

```markdown
---
name: fw-done
description: Wrap up a session: update your handoff, add a progress note, update the ticket, and draft the commit message for the user to run.
disable-model-invocation: true
---

# fw-done

Five steps. The last one hands a commit message to the user, because committing is theirs.

## Process

### 1. Read what changed

```bash
git status --porcelain
git diff
git log --oneline <session-start-commit>..HEAD
```

**Done when:** you can list every changed file and say, per file, why it changed.

### 2. Update your handoff

Overwrite `harness/handoff/<your-slug>.md` with: the goal, what was done, what is blocked and why, and the suggested next step. One file per person, overwritten each time, so it says where you are rather than where you have been.

**Done when:** the file names the ticket, the branch, and a next step specific enough to act on without this conversation.

### 3. Add a progress note

Create `harness/progress/<YYYY-MM-DD>_<your-slug>_<n>.md`, where `<n>` is the next unused number for you today. Record the author, the ticket id, the start and end commits, what was done, and the `check` summary as evidence.

**Done when:** the file exists with a header carrying author, ticket, and both commits.

### 4. Update the ticket

Record the evidence this session produced, on a clean working tree:

```bash
py -3 harness/scripts/check.py --record FW-NNNN
```

Move the ticket to `verifying` when the code is written and `check` passes, and list what it still owes in `dod_pending`. Leave `done` to the user.

**Done when:** `ticket.py show FW-NNNN` reflects this session, and `dod_pending` names every debt that is left.

### 5. Draft the commit message

Write the message in the language from `language` in `harness/config.json`. It names the ticket id, says what changed and why, and ends with the attribution line the team uses. Show it to the user and let them run the commit.

**Done when:** the message is shown, it contains the ticket id, and you have told the user that committing and pushing are theirs to run.
```

- [ ] **Step 5: Run the tests**

Run: `py -3 -m pytest tests/plugin -q`
Expected: the four work loop skills pass; five skills remain.

- [ ] **Step 6: Commit**

```bash
git add plugins/fw-c-harness/skills/fw-session-start plugins/fw-c-harness/skills/fw-ticket plugins/fw-c-harness/skills/fw-hil-verify plugins/fw-c-harness/skills/fw-done
git commit -m "Add the work loop skills"
```

---

### Task 4: `fw-c-implement` and its reference files

**Files:**
- Create: `SKILLS/fw-c-implement/SKILL.md`
- Create: `SKILLS/fw-c-implement/embedded-c-rules.md`, `isr-concurrency.md`, `memory-budget.md`, `module-template.md`

**Interfaces:**
- Consumes: `harness/scripts/check.py`, `ticket.py`, the module ARCHITECTURE.md files
- Produces: the implementation skill plus four disclosed references, each reached by a pointer that says when to read it

Source: adapted from `agents/expert-embedded-c-engineer.agent.md` in `github/awesome-copilot` (MIT). Each reference file names that source in its first lines.

- [ ] **Step 1: Write `SKILLS/fw-c-implement/SKILL.md`**

````markdown
---
name: fw-c-implement
description: Implement a firmware ticket in C, test first, inside the module's approved layering. Use when the user asks to implement a ticket, write or extend a driver, add a module, or change embedded C behaviour.
---

# fw-c-implement

Write the test before the code, keep the module inside its approved dependencies, and finish with evidence rather than a claim.

Read [embedded-c-rules.md](embedded-c-rules.md) before writing any C here. Read [isr-concurrency.md](isr-concurrency.md) when the change touches an interrupt handler or state a handler reaches. Read [memory-budget.md](memory-budget.md) when the change adds a buffer, a task stack, or an allocation. Read [module-template.md](module-template.md) when you are creating a module rather than editing one.

## Process

### 1. Read the ticket and the module

Read the ticket with `py -3 harness/scripts/ticket.py show FW-NNNN`, and the ARCHITECTURE.md of every folder you are about to touch. The approved dependencies in those documents are the layering you work inside.

**Done when:** you can state the ticket's `user_visible_behavior` in one sentence, list its `verification_steps`, and name which module owns the change and what it may include.

### 2. Write the failing test

Add a Unity test under `test/` that fails for the reason the ticket exists, and run it:

```bash
py -3 harness/scripts/check.py
```

A test that passes before the code is written proves nothing, so read the failure and confirm it is the one you intended.

**Done when:** the run fails, and the failure names the behaviour the ticket asked for.

### 3. Implement

Write the smallest change that makes the test pass. Add every new `.c` file to the CMake target as well as to disk.

**Done when:** the new test passes and no existing test changed its expectations to accommodate the new code.

### 4. Run every gate

```bash
py -3 harness/scripts/check.py
```

Fix what it reports. A new include that crosses a layer is a design question, so take it to the user rather than adding a grandfather entry.

**Done when:** all seven steps pass.

### 5. Record the evidence

On a clean working tree:

```bash
py -3 harness/scripts/check.py --record FW-NNNN
```

**Done when:** the ticket carries a `check` entry for this commit, and you have told the user what it still owes: board verification when `requires_hil` is true, and a review by someone else.
````

- [ ] **Step 2: Write `SKILLS/fw-c-implement/embedded-c-rules.md`**

````markdown
# Embedded C rules

Adapted from `agents/expert-embedded-c-engineer.agent.md` in [github/awesome-copilot](https://github.com/github/awesome-copilot) (MIT), trimmed to the rules this harness checks or a reviewer applies.

## Types and scope

- Use fixed-width integer types (`uint8_t`, `int16_t`, `uint32_t`) wherever a value's width matters, which in firmware is nearly everywhere.
- Give every function and variable the narrowest scope that works: `static` at file scope for anything the module does not export.
- Use `const` on pointers to read-only data, on parameters the function does not modify, and on file-scope constants.
- Prefer an `enum` over a group of related `#define` constants, because a debugger can show an enum's name.

## Functions and errors

- C has no exceptions, so every function that can fail returns a status the caller can act on, or writes it to an output parameter. Say which one in the header.
- Check every return value you receive. An ignored error code is a critical review finding.
- Validate inputs at the module boundary, meaning the functions the header exports. Inside the module, trust what the boundary already checked rather than paying for the check twice.
- Keep one job per function, and name the function after that job.

## Macros

- Wrap every macro parameter in parentheses, and wrap a multi-statement macro in `do { ... } while (0)`.
- Reach for a `static inline` function before a macro when the compiler allows it: the function keeps its types and gives a debugger something to step into.

## What to leave alone

- Generated code, vendor code, linker scripts, startup files, and compiler flags. Their ARCHITECTURE.md says where they come from and how they are upgraded.
- The naming convention of the module you are editing. Match it.

## MISRA

`harness/review-policy.json` holds the mode. In `advisory` a MISRA finding is a suggestion and never blocks a merge. In `required`, breaking a required rule needs a deviation record, which the `fw-misra-deviation` skill writes. Cite a rule as `Rule X.Y (required)` or `Rule X.Y (advisory)`, so the classification travels with the citation.
````

- [ ] **Step 3: Write `SKILLS/fw-c-implement/isr-concurrency.md`**

````markdown
# Interrupts and shared state

Adapted from `agents/expert-embedded-c-engineer.agent.md` in [github/awesome-copilot](https://github.com/github/awesome-copilot) (MIT).

Read this when the change adds or edits an interrupt handler, or touches a variable a handler writes.

## volatile

- Any variable written by a handler and read by the main loop is `volatile`, and so is every hardware register. Without it the compiler may cache the value in a register, and the loop reads a stale copy for ever.
- `volatile` orders nothing and makes nothing atomic. It only stops the compiler from optimising the access away.

## Sharing state with a handler

- A value wider than the target's atomic word is read and written under a critical section, or a reader can see half of the old value and half of the new one.
- Keep the critical section to the shortest sequence that must not be interrupted: copy the shared value out, then work on the copy outside the section.
- A single-producer, single-consumer ring buffer with one index owned by the handler and the other owned by the main loop needs no critical section. Write in a comment which side owns which index, because the design is safe only while that stays true.

## What a handler does not do

- Set a flag or push to a queue, and let the main loop do the rest. Long work belongs outside the handler.
- Keep it free of blocking calls, busy waits on another peripheral, and allocation.
- Use a logger inside a handler only when the team has a handler-safe one and its ARCHITECTURE.md says so.

## Review anchors

The critical findings a reviewer looks for here are shared state with no protection, a missing `volatile`, and work inside a handler that belongs in the main loop. They live in `harness/review-checklist.json`, which is the list `fw-c-review` applies.
````

- [ ] **Step 4: Write `SKILLS/fw-c-implement/memory-budget.md`**

````markdown
# Memory budget

Adapted from `agents/expert-embedded-c-engineer.agent.md` in [github/awesome-copilot](https://github.com/github/awesome-copilot) (MIT).

Read this when the change adds a buffer, a task stack, or an allocation.

## The budget is a gate

`check` runs the size tool on the ELF and compares the result with `flash_budget` and `ram_budget` in `harness/config.json`. Flash is `text + data`; RAM is `data + bss`. Exceeding either fails the run, so a large static buffer becomes a build failure instead of a surprise months later.

Run it before you commit:

```bash
py -3 harness/scripts/check.py
```

The size step prints the current numbers against the budget, so you can see what your change cost.

## Allocation

- Prefer static allocation with a fixed bound. A statically sized pool is visible in the size report; a heap is not.
- Where the team allows dynamic allocation at all, allocate during startup and keep it out of loops and handlers. Fragmentation on a device that runs for months is a fault that reproduces only in the field.
- Size every buffer from the protocol or the hardware rather than from a round number, and write the reason in a comment beside it.

## Stack

- A recursive function has no bound you can compute, so the bound becomes a runtime crash. Write it as a loop.
- Large locals live on the stack. Move anything sizeable into a static buffer owned by the module, or take it from the caller as a parameter.
- Record the stack a task needs in its ARCHITECTURE.md under the ISR and memory notes, so the next person sizing that task has your number.
````

- [ ] **Step 5: Write `SKILLS/fw-c-implement/module-template.md`**

`````markdown
# New module skeleton

Adapted from `agents/expert-embedded-c-engineer.agent.md` in [github/awesome-copilot](https://github.com/github/awesome-copilot) (MIT).

Read this when you are creating a module rather than editing one. A new folder of C sources also needs an entry in `harness/architecture.json` and an ARCHITECTURE.md, which `fw-architecture-sync` drafts.

## Header

```c
#ifndef UART_H
#define UART_H

#include <stdbool.h>
#include <stdint.h>

/* Status returned by every uart function that can fail. */
typedef enum {
    UART_OK = 0,
    UART_ERR_PARAM,
    UART_ERR_BUSY,
    UART_ERR_TIMEOUT
} uart_status_t;

/* Initialise the peripheral. Call once, before any other uart function. */
uart_status_t uart_init(uint32_t baud);

/* Queue len bytes for transmission. Returns UART_ERR_BUSY when the queue is full. */
uart_status_t uart_write(const uint8_t *data, uint16_t len);

#endif /* UART_H */
```

## Source

```c
#include "uart.h"

#include "hal_gpio.h"

#define UART_TX_BUFFER_LEN 256U

static uint8_t tx_buffer[UART_TX_BUFFER_LEN];
static volatile uint16_t tx_head; /* written by the ISR */
static uint16_t tx_tail;          /* written by the main loop */

static bool is_initialised(void);

uart_status_t uart_init(uint32_t baud)
{
    if (baud == 0U) {
        return UART_ERR_PARAM;
    }
    /* ... */
    return UART_OK;
}
```

## The checklist for a new module

- An include guard named after the file, one status enum for the module, and every exported function documented with what it returns when it fails.
- Everything not exported is `static`.
- The `.c` file is added to the CMake target.
- The module's includes stay inside the dependencies its ARCHITECTURE.md approves.
- A Unity test exists for the behaviour the ticket asked for, and it failed before the module existed.
`````

- [ ] **Step 6: Run the tests**

Run: `py -3 -m pytest tests/plugin -q`
Expected: `fw-c-implement` passes, including the link test, because all four reference files exist. Four skills remain.

- [ ] **Step 7: Commit**

```bash
git add plugins/fw-c-harness/skills/fw-c-implement
git commit -m "Add the C implementation skill with its embedded C references"
```

---

### Task 5: `fw-c-review` and its report format

**Files:**
- Create: `SKILLS/fw-c-review/SKILL.md`, `SKILLS/fw-c-review/report-format.md`

**Interfaces:**
- Consumes: `harness/review-checklist.json`, `harness/review-policy.json`, `harness/scripts/ticket.py`
- Produces: the two-axis review skill and the report format it writes into `harness/reviews/`

Sources: the two-axis split from `code-review` in `mattpocock/skills` (MIT); the severity language from `instructions/code-review-generic.instructions.md` and the self-verification pass from `skills/security-review/SKILL.md`, both in `github/awesome-copilot` (MIT).

- [ ] **Step 1: Write `SKILLS/fw-c-review/SKILL.md`**

````markdown
---
name: fw-c-review
description: Review changed C code along two axes, Standards and Spec, each in its own sub-agent, and write the report into harness/reviews. Use when the user asks for a code review, asks to review a branch or a ticket's changes, or wants a review before merging.
---

# fw-c-review

Two axes, each in its own sub-agent so neither pollutes the other, reported side by side:

- **Standards**: does the code follow the checklist, the approved layering, and the MISRA mode?
- **Spec**: does the code deliver what the ticket asked for?

A reviewer is someone other than the author. `harness/review-policy.json` sets `forbid_self_review`, and the Definition of Done counts only the latest review by another person, so a self-review buys the ticket nothing.

## Process

### 1. Pin the range

Capture the diff command once and run it before anything else:

```bash
git diff <fixed-point>...HEAD
```

Three dots, so the comparison is against the merge base. A bad ref or an empty diff fails here rather than inside two sub-agents.

**Done when:** the command prints a non-empty diff and you can name the ticket the range belongs to.

### 2. Load the rules

Read `harness/review-checklist.json` and `harness/review-policy.json`. The checklist is the severity list; the policy sets the MISRA mode and what blocks a merge. Read the ARCHITECTURE.md of every folder the diff touches, for its approved dependencies.

**Done when:** you can state the MISRA mode and list the folders the diff touches.

### 3. Dispatch the Standards sub-agent

Give it the diff command, the full checklist text from `harness/review-checklist.json`, the MISRA mode, and the approved dependencies of the touched modules. It has no other access to any of that.

Brief it to report, per file and hunk: every place the diff breaks a checklist item, with the severity that item carries; every include that leaves the module's approved dependencies; and, in `required` mode, every required MISRA rule broken with no deviation record. Ask for an exact `path:line`, the problem, why it matters, a suggested fix, and a confidence rating. Under 500 words.

**Done when:** the sub-agent has returned findings, each with a `path:line`.

### 4. Dispatch the Spec sub-agent

Give it the diff command and the ticket's `user_visible_behavior`, `verification_steps`, and `dod_pending`, from `py -3 harness/scripts/ticket.py show FW-NNNN`.

Brief it to report requirements that are missing or only partly delivered, behaviour in the diff nobody asked for, and requirements that look delivered but look wrong. Ask it to quote the ticket line behind each finding. Under 500 words.

When no ticket is known, skip this axis and say so in the report.

**Done when:** the sub-agent has returned findings, each quoting the ticket line it answers to.

### 5. Verify each finding

Re-read the code behind every finding and rule out the false positive: a check that already happened earlier on the path, a bound the caller guarantees, a `volatile` that is there after all. Drop what does not survive, and lower the confidence of anything that rests on thin evidence.

**Done when:** every finding left in the report has been re-read against the code, and you can say why each survivor is real.

### 6. Write the report

Follow [report-format.md](report-format.md). Write it to `harness/reviews/FW-NNNN_<your-slug>_<YYYY-MM-DD>.md`, in the language from `language` in `harness/config.json`. Keep the two axes under their own headings, in the words the sub-agents used. Merging or reranking them across axes undoes the separation, so present them side by side.

**Done when:** the file exists, the counts in its table match the findings below it, and the two axes are still separate.

### 7. Record the evidence

```bash
py -3 harness/scripts/ticket.py evidence FW-NNNN review --ref harness/reviews/<file> --open-critical <count>
```

The count is the number of critical findings still open. Propose patches and leave applying them to a human.

**Done when:** the ticket carries the review evidence, and you have told the user which findings block the merge.
````

- [ ] **Step 2: Write `SKILLS/fw-c-review/report-format.md`**

`````markdown
# Review report format

The severity language is adapted from `instructions/code-review-generic.instructions.md` and the self-verification pass from `skills/security-review/SKILL.md`, both in [github/awesome-copilot](https://github.com/github/awesome-copilot) (MIT). The two-axis structure is adapted from `code-review` in [mattpocock/skills](https://github.com/mattpocock/skills) (MIT).

Write the report to `harness/reviews/FW-NNNN_<reviewer-slug>_<YYYY-MM-DD>.md`.

```markdown
# Review FW-NNNN

- Reviewer: <name> <email>
- Ticket: FW-NNNN, <title>
- Range: `git diff <fixed-point>...HEAD`
- MISRA mode: <off|advisory|required>

| Severity | Standards | Spec |
|---|---|---|
| Critical | 0 | 0 |
| Important | 0 | 0 |
| Suggestion | 0 | 0 |

## Standards

### Critical: <one line naming the problem>

- Where: `src/drivers/uart.c:88`
- Problem: <what the code does>
- Why it matters: <what happens on the device>
- Suggested fix: <the change, as a patch a human applies>
- Confidence: high

## Spec

### Important: <requirement missing or partial>

- Ticket line: "<quoted from user_visible_behavior or verification_steps>"
- What the diff does: <what is there now>
- Suggested fix: <what would deliver it>
- Confidence: medium

## Summary

- Standards: <n> findings, worst: <severity>
- Spec: <n> findings, worst: <severity>
- Blocking: <the critical findings, or "none">
```

Rules this format carries:

- The counts table comes first, so a reader sees the shape before the detail.
- Every finding has a `path:line` a reader can open, and the cited line literally contains the thing named.
- Each axis keeps its own worst finding. Pick no single winner across the two.
- Patches are proposed, and the author applies them.
`````

- [ ] **Step 3: Run the tests**

Run: `py -3 -m pytest tests/plugin -q`
Expected: `fw-c-review` passes; three skills remain.

- [ ] **Step 4: Commit**

```bash
git add plugins/fw-c-harness/skills/fw-c-review
git commit -m "Add the two-axis C review skill and its report format"
```

---

### Task 6: `fw-c-test-gap` and `fw-c-debug`

**Files:**
- Create: `SKILLS/fw-c-test-gap/SKILL.md`, `SKILLS/fw-c-debug/SKILL.md`

**Interfaces:**
- Consumes: `harness/scripts/check.py`, `ticket.py`, `SKILLS/fw-c-implement/isr-concurrency.md`
- Produces: the audit skill and the debugging skill

Sources: `skills/test-gap-audit/SKILL.md` and `agents/debug.agent.md` in `github/awesome-copilot` (MIT).

- [ ] **Step 1: Write `SKILLS/fw-c-test-gap/SKILL.md`**

`````markdown
---
name: fw-c-test-gap
description: Audit which behaviour in this firmware has no test, ranked P0 to P3, read-only. Use when the user asks what is untested, whether coverage is enough, what regression test a fix needs, or how to prove a change is safe.
---

# fw-c-test-gap

Adapted from `skills/test-gap-audit/SKILL.md` in [github/awesome-copilot](https://github.com/github/awesome-copilot) (MIT), narrowed to C firmware and to this harness.

Read-only. Add tests only when the user asks, and then through `fw-c-implement`.

## Scope

When the user names a ticket, a module, or a branch, audit that and the code paths it reaches. When they name nothing, audit the modules marked `owned` in `harness/architecture.json`, breadth first, and say which ones you inspected deeply and which you only surveyed.

## Evidence standards

These are what make the report trustworthy:

- **The line you cite literally contains the thing you name.** Citing a function means citing the line its name is on, not the line above it and not a line inside its body.
- **Every number appears next to the command that produced it**, under Checks Run. A count with no visible command behind it is the easiest claim to get wrong, so evidence it or describe the pattern instead.
- **A negative claim needs more than one search.** Before reporting that nothing tests a function, search the test folder for the module name, for the header name, and for the behaviour's wording.
- Separate what you confirmed from what you inferred, and give an inferred gap a confidence rating.

## What to look for in firmware

- A driver's error paths: the peripheral timing out, the bus reporting an error, the buffer filling up.
- Boundary values on every parsed length, index, and count.
- The state machine's illegal transitions, not only its happy path.
- Behaviour only the board can show, which belongs in the ticket's `verification_steps`. Say so rather than proposing a host test that cannot prove it.
- A fixed bug with no regression test.

## Severity

- `P0`: untested code whose failure corrupts data, bricks the device, or drives an output unsafely.
- `P1`: untested common path, error return, or interface contract another module depends on.
- `P2`: untested edge case, validation, or state transition, or a test whose assertions do not prove what its name claims.
- `P3`: naming drift, redundant tests, fixture cleanup.

## Report

```markdown
**Test gap audit: <scope>**

No code changed. I reviewed <scope>, the existing tests under test/, and the ticket's verification steps.

1. **P1: <gap title>.**
   Gap: <behaviour not covered>
   Current coverage: <what exists, or where you looked and found nothing>
   Evidence: code `src/drivers/uart.c:142`; tests: no direct test found in `test/`
   Suggested test: <file, name, and the assertions that would prove it>

**Checks Run**
- `<command>`: <result>

**Not tested here**
- <what needs the board, and which verification step covers it>
```

**Done when:** every gap carries a `path:line` you re-read, every number has its command beside it, and board-only behaviour is named rather than quietly turned into a host test.
`````

- [ ] **Step 2: Write `SKILLS/fw-c-debug/SKILL.md`**

````markdown
---
name: fw-c-debug
description: Reproduce and then fix a firmware defect. Use when the user reports a hang, a reset loop, a HardFault, corrupted data, a peripheral that works intermittently, or asks to debug embedded C.
---

# fw-c-debug

Adapted from `agents/debug.agent.md` in [github/awesome-copilot](https://github.com/github/awesome-copilot) (MIT), with the firmware specifics this harness needs.

Reproduce before fixing. A fix for a defect you have not reproduced is a guess, and on a device the guess usually survives the test and fails in the field.

## Process

### 1. Reproduce

Get the defect to happen on demand: the exact build, the exact steps, and the output it produces. Capture the serial log or the debugger state into `harness/evidence/FW-NNNN/` when a board is involved.

**Done when:** you can name one command or one sequence on the board that shows the defect, and you have run it at least once and shown its output.

### 2. Shrink the reproduction

Remove everything not needed to make it happen: peripherals, tasks, inputs, the optimisation level. Keep removing until every remaining element is load bearing.

**Done when:** removing any remaining element makes the defect disappear.

### 3. Test one hypothesis at a time

Firmware anchors worth ruling in or out early:

- **HardFault**: decode the stacked registers. The stacked PC is the faulting instruction and the stacked LR is where it came from. `CFSR` says which fault fired, and `BFAR` or `MMFAR` holds the address when its valid bit is set.
- **Stack overflow**: paint the stack with a known pattern at startup and read how far it was consumed. A corrupted variable next to a task stack is this until proven otherwise.
- **An interrupt race**: state shared with a handler and no protection, or a missing `volatile`. Read [isr-concurrency.md](../fw-c-implement/isr-concurrency.md).
- **It appeared recently**: `git bisect`, with the shrunken reproduction as the test.

**Done when:** one hypothesis is confirmed by evidence you can show, rather than by the fix appearing to work.

### 4. Write the regression test first

Add a Unity test that fails for this defect. When the defect needs the board, add the check to the ticket's `verification_steps` instead and say so.

**Done when:** the test fails, and its failure is the defect.

### 5. Fix and verify

Make the smallest change that addresses the cause you confirmed, then:

```bash
py -3 harness/scripts/check.py
```

**Done when:** the regression test passes, every other gate passes, and you have told the user the root cause in one sentence plus where else the same pattern appears in this repository.
````

- [ ] **Step 3: Run the tests**

Run: `py -3 -m pytest tests/plugin -q`
Expected: both skills pass. The cross-skill link in `fw-c-debug` points at `../fw-c-implement/isr-concurrency.md`, which Task 4 created, so the link test passes. Two skills remain.

- [ ] **Step 4: Commit**

```bash
git add plugins/fw-c-harness/skills/fw-c-test-gap plugins/fw-c-harness/skills/fw-c-debug
git commit -m "Add the test gap audit and firmware debugging skills"
```

---

### Task 7: `fw-misra-deviation` and the `fw-guide` router

**Files:**
- Create: `SKILLS/fw-misra-deviation/SKILL.md`
- Modify: `SKILLS/fw-guide/SKILL.md` (replace the Task 1 placeholder)

**Interfaces:**
- Consumes: `harness/review-policy.json`, `docs/deviations/`
- Produces: the deviation skill and the router that names all thirteen

- [ ] **Step 1: Write `SKILLS/fw-misra-deviation/SKILL.md`**

`````markdown
---
name: fw-misra-deviation
description: Record a MISRA deviation in docs/deviations when a rule cannot be met. Use when the user says a MISRA rule must be broken, when a review finds a required-rule violation the code needs to keep, or when someone asks how to document a deviation.
---

# fw-misra-deviation

Adapted from the deviation guidance in `agents/expert-embedded-c-engineer.agent.md` in [github/awesome-copilot](https://github.com/github/awesome-copilot) (MIT).

A deviation is a decision with a name on it, not a suppression. Writing it down is how the next reader learns why the rule was broken here and what was done about the risk.

## Process

### 1. Check the mode

Read `harness/review-policy.json`. In `advisory` mode a MISRA finding never blocks a merge, so a record is usually unnecessary: say so and stop. Write one when the mode is `required`, or when the user asks for it anyway.

**Done when:** you can state the mode and why this case needs a record.

### 2. Rule out the alternative first

A deviation is the answer when the rule cannot be met, not when meeting it is inconvenient. Show the user the change that would comply and what it costs. Many required rules have a compliant form once the code is restructured.

**Done when:** the user has seen the compliant alternative and chosen the deviation over it.

### 3. Write the record

Create `docs/deviations/DEV-NNNN.md`, where `NNNN` is the next unused number in that folder:

```markdown
# DEV-NNNN: <one line>

- Rule: MISRA C:2012 Rule X.Y (required)
- Raised by: <name> <email>, <date>
- Ticket: FW-NNNN
- Scope: <the exact files, functions, or lines this covers>

## Why the rule cannot be met here

<the constraint: the hardware, the vendor header, the toolchain>

## Risk

<what the rule protects against, and what could go wrong here without it>

## What limits the risk

<the review, the test, the assertion, or the runtime check that covers it>

## Approver

<name>, <date>
```

**Done when:** the file exists, its scope names exact files rather than a whole module, and the risk section says what could go wrong rather than that nothing will.

### 4. Get an approver who is not the author

The approver is someone other than whoever wrote the code. Leave that line for them and tell the user who needs to sign it.

**Done when:** the user knows the record needs another person's approval before the ticket can reach `done`, and a comment in the code names `DEV-NNNN` where the deviation applies.
`````

- [ ] **Step 2: Replace `SKILLS/fw-guide/SKILL.md`**

````markdown
---
name: fw-guide
description: Ask which fw-harness skill fits your situation.
disable-model-invocation: true
---

# fw-guide

Thirteen skills is more than anyone remembers, so ask here instead. The ones marked "the agent reaches on its own" fire without you typing them; the rest you type.

## Setting the repository up

- **`/fw-harness-init`**: run once in a firmware repository. It writes the harness, drafts the architecture, and generates the ARCHITECTURE.md files.
- **`/fw-harness-upgrade`**: run after the plugin updates. Managed files are replaced, and anything your team owns is proposed for you to review one at a time.

## A day of work

1. **`/fw-session-start`**: begin here every session. It verifies the environment, reads your handoff, and ends by agreeing with you on the ticket.
2. **`fw-c-implement`** (the agent reaches on its own): the test-first loop, inside the module's approved layering.
3. **`/fw-hil-verify`**: when the ticket owes board verification, this collects the log and records it as evidence.
4. **`/fw-done`**: close the session. Handoff, progress note, ticket update, and a commit message for you to run.

**`fw-ticket`** (the agent reaches on its own) handles every ticket write underneath those steps, so you rarely call it yourself.

## Looking at code

- **`fw-c-review`** (the agent reaches on its own): the two-axis review, Standards and Spec, written into `harness/reviews/`. Reach for it before merging, and remember that a review by the author counts for nothing at the Definition of Done.
- **`fw-c-test-gap`** (the agent reaches on its own): what has no test, ranked P0 to P3, read-only. Reach for it when the question is coverage rather than correctness.
- **`fw-c-debug`** (the agent reaches on its own): reproduce, shrink, then fix. Reach for it for a hang, a HardFault, or anything intermittent.

## When a rule gets in the way

- **`fw-architecture-sync`** (the agent reaches on its own): `arch_check` failed, or a new folder of C sources appeared.
- **`fw-misra-deviation`** (the agent reaches on its own): a MISRA rule cannot be met and the decision needs a name on it.

## Where the rules actually live

The skills are thin on purpose. `harness/scripts/` holds the gates, `harness/architecture.json` holds the approved layering, `harness/review-checklist.json` holds the review severities, and `CLAUDE.md` holds the Definition of Done. When a skill and a script disagree, the script is right.
````

- [ ] **Step 3: Run the tests**

Run: `py -3 -m pytest tests/plugin -q`
Expected: PASS. All thirteen skills exist and satisfy every rule.

- [ ] **Step 4: Run the whole suite**

Run: `py -3 -m pytest tests -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/fw-c-harness/skills/fw-misra-deviation plugins/fw-c-harness/skills/fw-guide
git commit -m "Add the MISRA deviation skill and the fw-guide router"
```

---

### Task 8: A page per skill, and the plugin README

**Files:**
- Create: `docs/skills/<name>.md` for all thirteen
- Create: `plugins/fw-c-harness/README.md`
- Create: `tests/plugin/test_docs.py`

**Interfaces:**
- Consumes: `skilltools.SKILL_NAMES`, `skilltools.USER_INVOKED`
- Produces: one human-facing page per skill, each with the four headings the spec names, and the plugin README with install steps for both tools

- [ ] **Step 1: Write the failing test**

Create `tests/plugin/test_docs.py`:

```python
import pytest

from skilltools import DOCS, PLUGIN, SKILL_NAMES

HEADINGS = ("## What it does", "## When to reach for it", "## Common questions", "## It is working if")


@pytest.mark.parametrize("name", SKILL_NAMES)
def test_every_skill_has_a_page(name):
    page = DOCS / f"{name}.md"
    assert page.is_file(), f"docs/skills/{name}.md is missing"
    text = page.read_text(encoding="utf-8")
    assert text.startswith(f"# {name}\n")
    for heading in HEADINGS:
        assert heading in text, f"{name}: {heading} is missing"


def test_no_page_without_a_skill():
    pages = sorted(path.stem for path in DOCS.glob("*.md") if path.name != "README.md")
    assert pages == sorted(SKILL_NAMES)


def test_plugin_readme_covers_both_tools():
    text = (PLUGIN / "README.md").read_text(encoding="utf-8")
    assert "/plugin marketplace add" in text and "copilot plugin marketplace add" in text
    assert "disable-model-invocation" in text, "the invocation difference between the tools is stated"
    for name in SKILL_NAMES:
        assert name in text, f"{name} is not listed in the plugin README"
```

- [ ] **Step 2: Run it and watch it fail**

Run: `py -3 -m pytest tests/plugin/test_docs.py -q`
Expected: FAIL, thirteen missing pages and a missing README.

- [ ] **Step 3: Write the pages**

Every page uses this shape. Here is `docs/skills/fw-session-start.md` in full, as the pattern:

```markdown
# fw-session-start

User-invoked. Type `/fw-session-start`.

## What it does

Runs the six steps that open a firmware session: confirms the repository and your git identity, runs `init` to verify the environment, reads your handoff and the recent progress notes, lists the tickets you could take, and ends by agreeing with you on one.

## When to reach for it

At the start of every session, before any code. Reach for it again after a long break in the same session, when you no longer trust what the working tree contains.

## Common questions

**It stops at a `[FAIL]` line. What now?** Each line names its own fix. A missing `core.hooksPath` is one command; a missing toolchain is an install `init` deliberately will not do for you.

**Can it pick the ticket for me?** No. It presents candidates and takes your answer, because the ticket decides what the rest of the session means.

**Someone else is the assignee.** It reads their handoff before you take over, so you start from what they left rather than from the code alone.

## It is working if

You end the six steps with one `active` ticket that is yours, and you can say in one sentence what the ticket must make the product do.
```

Write the other twelve to the same shape, with this content:

| Page | What it does | When to reach for it | The questions worth answering | It is working if |
|---|---|---|---|---|
| `fw-harness-init` | Writes the harness into a firmware repository, drafts the architecture, and generates the ARCHITECTURE.md files | Once per repository, on a clean working tree | Why did nothing get overwritten; what is a `.harness-proposed` file; what is left for a human to fill in | `check` runs, and the install plus generated documents are one commit |
| `fw-harness-upgrade` | Replaces managed files and proposes changes to the files your team owns | After the plugin updates, before starting work on the new version | What counts as managed versus team-owned; what happens to a script you edited locally | No `.harness-proposed` file is left and `check` passes |
| `fw-architecture-sync` | Drafts `harness/architecture.json` from the tree and refreshes every generated block | When `arch_check` fails, or a new folder of C sources appears | Why approved rules still need a person; why the grandfather list may only shrink | `arch_check` passes without a rule a human did not approve |
| `fw-ticket` | Creates, claims, moves, and adds evidence to tickets, with your identity filled in from git | Whenever ticket state changes; usually another skill reaches it for you | Why you cannot mark a ticket `done`; why editing the JSON by hand is worse | The ticket's status and evidence match what actually happened |
| `fw-hil-verify` | Guides flashing and serial capture, stores the log, and records `hil` evidence | When a `verifying` ticket still owes board verification | Where the log goes; what happens to `dod_pending` | The ticket carries a log a reader can open, and the board debt is gone |
| `fw-done` | Handoff, progress note, ticket update, and a drafted commit message | At the end of every session, before you commit | Why it does not commit for you; which language the message uses | The next person can pick up your ticket from the handoff alone |
| `fw-c-implement` | The test-first implementation loop inside the module's approved layering | When you are writing or changing C for a ticket | Why the test comes first; what to do when an include crosses a layer | A test that failed first now passes, and all seven gates pass |
| `fw-c-review` | Two-axis review in separate sub-agents, written into `harness/reviews/` | Before merging, or whenever someone asks for a review | Why Standards and Spec stay separate; why a self-review does not count | The report's counts match its findings, and every finding has a line you can open |
| `fw-c-test-gap` | A read-only audit of what has no test, ranked P0 to P3 | When the question is coverage rather than correctness | Why a number needs its command beside it; what belongs on the board instead of a host test | Every gap names a line you can open, and nothing is claimed without evidence |
| `fw-c-debug` | Reproduce, shrink, confirm one hypothesis, then fix with a regression test | For a hang, a HardFault, corrupted data, or anything intermittent | Why reproduction comes first; how to read a HardFault's stacked registers | The defect is reproduced before the fix, and a test now fails for it |
| `fw-misra-deviation` | Writes a deviation record with rule, rationale, risk, scope, and approver | When a required MISRA rule cannot be met | Why `advisory` mode usually needs no record; why the approver is someone else | The record names exact files and a real risk, and another person signs it |
| `fw-guide` | Names every other skill and when to reach for it | When you cannot remember which skill fits | Why some skills are typed and others fire on their own | You leave with one skill to run next |

**Done when:** each of the thirteen pages carries the four headings and says, in its own words, what the table names.

- [ ] **Step 4: Write `plugins/fw-c-harness/README.md`**

```markdown
# fw-c-harness

A harness and a set of skills for C firmware teams, for Claude Code and GitHub Copilot.

## Install

**Claude Code**

```
/plugin marketplace add Yangchengyu0206/fw-harness
/plugin install fw-c-harness@fw-harness
```

**Copilot CLI**

```
copilot plugin marketplace add Yangchengyu0206/fw-harness
copilot plugin install fw-c-harness@fw-harness
```

After `fw-harness-init` runs in a firmware repository, that repository carries `.claude/settings.json` and `.github/copilot-settings.json` naming this marketplace, so the next person who clones it is prompted to install the plugin.

## Use it

Run `fw-harness-init` once in the firmware repository, then start each session with `fw-session-start`. When you cannot remember which skill fits, run `fw-guide`.

## The skills

Lifecycle: `fw-harness-init`, `fw-harness-upgrade`, `fw-architecture-sync`.
Work loop: `fw-session-start`, `fw-ticket`, `fw-hil-verify`, `fw-done`.
Code: `fw-c-implement`, `fw-c-review`, `fw-c-test-gap`, `fw-c-debug`, `fw-misra-deviation`.
Router: `fw-guide`.

One page per skill lives in [docs/skills](../../docs/skills).

## One difference between the two tools

Six of the skills are meant for a human to type: `fw-harness-init`, `fw-harness-upgrade`, `fw-session-start`, `fw-hil-verify`, `fw-done`, and `fw-guide`. They carry `disable-model-invocation: true`, which Claude Code honours by keeping the agent from firing them. Copilot does not document that key for skills, so on Copilot an agent can still reach them on its own. The guardrails that matter do not depend on it: moving a ticket to `done` needs a typed confirmation in a real terminal, and committing is left to you in both tools.

## Update

Run `fw-harness-upgrade` after the plugin updates. It replaces the files the plugin manages and proposes anything your team owns, one item at a time.

## License

MIT. See [THIRD_PARTY_NOTICES.md](../../THIRD_PARTY_NOTICES.md) for the content adapted from other projects.
```

- [ ] **Step 5: Run the tests**

Run: `py -3 -m pytest tests/plugin -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add docs/skills plugins/fw-c-harness/README.md tests/plugin/test_docs.py
git commit -m "Add a page per skill and the plugin README"
```

---

### Task 9: Project README, translation, and notices

**Files:**
- Create: `README.md`, `README.zh-TW.md`, `THIRD_PARTY_NOTICES.md`
- Modify: `tests/plugin/test_docs.py`

**Interfaces:**
- Consumes: `skilltools.SKILL_NAMES`
- Produces: the repository's front page in English and Traditional Chinese, and the attribution file

- [ ] **Step 1: Write the failing test**

Append to `tests/plugin/test_docs.py`:

```python
from helpers import ROOT

README = ROOT / "README.md"
README_ZH = ROOT / "README.zh-TW.md"
NOTICES = ROOT / "THIRD_PARTY_NOTICES.md"


def test_readme_pair_covers_the_same_sections():
    english = README.read_text(encoding="utf-8")
    chinese = README_ZH.read_text(encoding="utf-8")
    for fragment in ("fw-c-harness", "/plugin marketplace add", "copilot plugin marketplace add", "MIT"):
        assert fragment in english and fragment in chinese, fragment
    assert "README.zh-TW.md" in english and "README.md" in chinese


def test_readme_is_english_and_the_translation_is_not():
    assert not any("一" <= ch <= "鿿" for ch in README.read_text(encoding="utf-8"))
    assert any("一" <= ch <= "鿿" for ch in README_ZH.read_text(encoding="utf-8"))


def test_notices_credit_every_adapted_source():
    text = NOTICES.read_text(encoding="utf-8")
    for source in ("github/awesome-copilot", "mattpocock/skills", "MIT"):
        assert source in text
    for path in ("expert-embedded-c-engineer.agent.md", "debug.agent.md", "test-gap-audit",
                 "security-review", "code-review-generic.instructions.md", "code-review"):
        assert path in text, f"{path} is adapted but not credited"
```

- [ ] **Step 2: Run it and watch it fail**

Run: `py -3 -m pytest tests/plugin/test_docs.py -q`
Expected: FAIL with `FileNotFoundError` for `README.md`.

- [ ] **Step 3: Write `README.md`**

```markdown
# fw-harness

A harness and a set of skills for C firmware teams, for Claude Code and GitHub Copilot. Traditional Chinese: [README.zh-TW.md](README.zh-TW.md).

One install gives a firmware team two things:

1. **A harness generated into their own repository**: entry documents, ticket state that records who changed what, verification gates, git hooks, and an ARCHITECTURE.md for every folder of C sources, derived from the real tree.
2. **Skills for the whole work loop**: starting a session, taking a ticket, implementing test first, reviewing, debugging, and wrapping up.

## Why it looks like this

- **Several people share the repository.** Every state change records the person who made it, taken from `git config`. One file per ticket, so two people adding tickets in parallel get a conflict git can show instead of a silent overwrite.
- **The rules live in the repository, not in the plugin.** The gates are Python scripts committed to the firmware repository, so a person committing by hand, an agent, and CI all follow the same rules. The plugin carries only what should update with its version.
- **The gates ratchet.** The `cppcheck` suppression list and the architecture grandfather list may only shrink, measured against `origin/main`.
- **Written and done are different.** A ticket whose code passes `check` but still owes board verification or a review stays in `verifying`, with the debt written down.

## Install

**Claude Code**

```
/plugin marketplace add Yangchengyu0206/fw-harness
/plugin install fw-c-harness@fw-harness
```

**Copilot CLI**

```
copilot plugin marketplace add Yangchengyu0206/fw-harness
copilot plugin install fw-c-harness@fw-harness
```

Then, in your firmware repository, run `fw-harness-init` once.

## What lands in your repository

```
AGENTS.md              short entry point for every tool
CLAUDE.md              the handbook: session, rules, Definition of Done, and why each gate exists
ARCHITECTURE.md        the module map, generated from harness/architecture.json
harness/
  config.json          every external command, as an argv array
  architecture.json    approved layering, the single source of the rules
  tickets/FW-NNNN.json one file per ticket
  scripts/             the only implementation of the gates
.githooks/             commit-msg, post-commit, post-merge
init.sh / init.ps1     thin wrappers, no flags of their own
```

`check` runs seven steps in order and stops at the first failure: format on changed C sources, `cppcheck`, the architecture gate, the ticket gate, the cross build, the host tests, and the size budget. Every external command comes from `harness/config.json`, so a team swaps toolchains without editing a script.

## Requirements

Python 3.9 or newer, git, and the toolchain your project names in `harness/config.json`. The defaults are `arm-none-eabi-gcc` with CMake, host `gcc` running Unity, `cppcheck`, and `clang-format`. MISRA C:2012 is a reference standard, advisory by default, configurable in `harness/review-policy.json`.

Windows, macOS, and Linux. On Windows the scripts run under `py -3`, read and write UTF-8 whatever the console code page is, and the git hooks use the POSIX shell Git for Windows ships.

## The skills

| Skill | Invocation | What it is for |
|---|---|---|
| `fw-harness-init` | you type it | Generate the harness in a firmware repository |
| `fw-harness-upgrade` | you type it | Update the harness after a plugin release |
| `fw-architecture-sync` | the agent reaches it | Redraft the architecture and refresh the documents |
| `fw-session-start` | you type it | Open a session and agree on the ticket |
| `fw-ticket` | the agent reaches it | Every ticket write |
| `fw-hil-verify` | you type it | Pay off board verification with a captured log |
| `fw-done` | you type it | Handoff, progress note, ticket, commit message |
| `fw-c-implement` | the agent reaches it | Test-first implementation |
| `fw-c-review` | the agent reaches it | Two-axis review, Standards and Spec |
| `fw-c-test-gap` | the agent reaches it | What has no test, P0 to P3 |
| `fw-c-debug` | the agent reaches it | Reproduce, then fix |
| `fw-misra-deviation` | the agent reaches it | Record a deviation with an approver |
| `fw-guide` | you type it | Which skill fits your situation |

One page per skill is in [docs/skills](docs/skills). The design is in [the spec](docs/superpowers/specs/2026-09-15-fw-c-harness-plugin-design.md).

## Contributing

Run the tests with `py -3 -m pytest tests -q`. Skills cannot be tested automatically, so changes to them are checked against [docs/manual-checklist.md](docs/manual-checklist.md).

## License

MIT. Content adapted from other projects is credited in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
```

- [ ] **Step 4: Write `README.zh-TW.md`**

A translation of the same sections, in the same order, with the commands and file names left in English. English is the source of truth, so a later change edits `README.md` first and the translation follows. Open it with:

```markdown
# fw-harness

給 C 韌體團隊的 harness 與技能組，同時支援 Claude Code 與 GitHub Copilot。English: [README.md](README.md)。
```

Keep the skill table, the install commands, and the repository layout block identical to the English version, so a reader can compare them line by line.

**Done when:** every heading in `README.md` has its counterpart here, and the commands are byte for byte the same.

- [ ] **Step 5: Write `THIRD_PARTY_NOTICES.md`**

```markdown
# Third party notices

This project is MIT licensed. The files below adapt material from other MIT licensed projects. Each adapted file also names its source in its own text.

## github/awesome-copilot

https://github.com/github/awesome-copilot, MIT.

| Our file | Adapted from |
|---|---|
| `plugins/fw-c-harness/skills/fw-c-implement/embedded-c-rules.md` | `agents/expert-embedded-c-engineer.agent.md` |
| `plugins/fw-c-harness/skills/fw-c-implement/isr-concurrency.md` | `agents/expert-embedded-c-engineer.agent.md` |
| `plugins/fw-c-harness/skills/fw-c-implement/memory-budget.md` | `agents/expert-embedded-c-engineer.agent.md` |
| `plugins/fw-c-harness/skills/fw-c-implement/module-template.md` | `agents/expert-embedded-c-engineer.agent.md` |
| `plugins/fw-c-harness/skills/fw-misra-deviation/SKILL.md` | the deviation guidance in `agents/expert-embedded-c-engineer.agent.md` |
| `plugins/fw-c-harness/skills/fw-c-debug/SKILL.md` | `agents/debug.agent.md` |
| `plugins/fw-c-harness/skills/fw-c-test-gap/SKILL.md` | `skills/test-gap-audit/SKILL.md` |
| `plugins/fw-c-harness/skills/fw-c-review/report-format.md` | `instructions/code-review-generic.instructions.md` and `skills/security-review/SKILL.md` |

## mattpocock/skills

https://github.com/mattpocock/skills, MIT.

| Our file | Adapted from |
|---|---|
| `plugins/fw-c-harness/skills/fw-c-review/SKILL.md` | the two-axis split in `skills/engineering/code-review` |
| `plugins/fw-c-harness/skills/fw-guide/SKILL.md` | the router pattern in `skills/engineering/ask-matt` |
| The authoring conventions every SKILL.md follows | `skills/productivity/writing-for-agents` |

## Standards referenced, not included

MISRA C:2012 is a copyrighted standard. This project ships no rule text. It refers to rules by number, with our own one line summaries, and the mode is configured in `harness/review-policy.json`.
```

- [ ] **Step 6: Run the tests**

Run: `py -3 -m pytest tests/plugin -q`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add README.md README.zh-TW.md THIRD_PARTY_NOTICES.md tests/plugin/test_docs.py
git commit -m "Add the project readme, its translation, and third party notices"
```

---

### Task 10: The manual checklist and the final pass

**Files:**
- Create: `docs/manual-checklist.md`
- Modify: `tests/plugin/test_docs.py`

**Interfaces:**
- Consumes: everything above
- Produces: the checklist for what no test can run, plus a green suite

- [ ] **Step 1: Write the failing test**

Append to `tests/plugin/test_docs.py`:

```python
CHECKLIST = ROOT / "docs" / "manual-checklist.md"


def test_checklist_covers_both_tools_and_every_user_invoked_skill():
    from skilltools import USER_INVOKED
    text = CHECKLIST.read_text(encoding="utf-8")
    assert "Claude Code" in text and "Copilot" in text
    for name in sorted(USER_INVOKED):
        assert name in text, f"{name} is typed by a human and is not in the checklist"
```

- [ ] **Step 2: Run it and watch it fail**

Run: `py -3 -m pytest tests/plugin/test_docs.py -q`
Expected: FAIL with `FileNotFoundError` for `docs/manual-checklist.md`.

- [ ] **Step 3: Write `docs/manual-checklist.md`**

```markdown
# Manual checklist

Skills cannot be tested automatically, so this list is run by hand once in Claude Code and once in Copilot CLI before a release. Work through it on a scratch copy of a firmware repository, never on real work.

Record the date, the tool, its version, and who ran it at the bottom.

## Install

- [ ] `/plugin marketplace add <owner>/fw-harness` (Claude Code) or `copilot plugin marketplace add <owner>/fw-harness` (Copilot) succeeds.
- [ ] Installing the plugin succeeds, and the thirteen skills are listed.
- [ ] In Claude Code, `claude plugin validate . --strict` passes in a clone of this repository.

## Generate the harness

- [ ] `fw-harness-init` in a scratch firmware repository creates the files, sets `core.hooksPath`, and writes `harness/.harness-version`.
- [ ] Running it a second time changes nothing and reports no proposals.
- [ ] With an existing `AGENTS.md`, the file is untouched and `AGENTS.md.harness-proposed` appears.
- [ ] The architecture draft lists the real modules, and the confirmation step asks before the rules are written.
- [ ] Every module folder has an ARCHITECTURE.md, and `check` reports the architecture gate as passed.

## The loop

- [ ] `fw-session-start` verifies the environment, reads the handoff, and stops for your answer before writing code.
- [ ] Creating a ticket records your git identity as `created_by`.
- [ ] `fw-c-implement` writes the failing test first and shows you the failure before implementing.
- [ ] `check --record FW-NNNN` refuses to run on a dirty working tree.
- [ ] `fw-c-review` produces two separate axes in `harness/reviews/`, and its counts match its findings.
- [ ] The agent declines to move a ticket to `done`, and `ticket.py move <id> done` asks for typed confirmation in a terminal.
- [ ] `fw-hil-verify` stores a log under `harness/evidence/` and records hil evidence.
- [ ] `fw-done` writes the handoff and the progress note, and hands you a commit message rather than committing.
- [ ] `fw-guide` names the skill you actually needed.

## Two people

- [ ] Two clones with different git identities each create a ticket; merging reports an add/add conflict rather than losing one.
- [ ] `ticket.py collisions` names the clash before the merge, and `renumber` frees the id and lists the commits still naming the old one.
- [ ] A review by the assignee does not satisfy the Definition of Done; a review by the other person does.

## Upgrade

- [ ] `fw-harness-upgrade --dry-run` reports the version change and the four groups without writing.
- [ ] After the real run, a locally edited script is untouched and its new version is a proposal.

## Record

| Date | Tool and version | Who | Result |
|---|---|---|---|
| | | | |
```

- [ ] **Step 4: Run the whole suite**

Run: `py -3 -m pytest tests -q`
Expected: PASS, with the same skips as before (`make` and `sh` when they are not on PATH).

- [ ] **Step 5: Check the version in every place it appears**

Run:

```bash
py -3 -c "import json,pathlib; v=pathlib.Path('plugins/fw-c-harness/skills/fw-harness-init/templates/VERSION').read_text(encoding='utf-8').strip(); print(v, json.loads(pathlib.Path('plugins/fw-c-harness/.claude-plugin/plugin.json').read_text(encoding='utf-8'))['version'], json.loads(pathlib.Path('plugins/fw-c-harness/plugin.json').read_text(encoding='utf-8'))['version'], json.loads(pathlib.Path('.github/plugin/marketplace.json').read_text(encoding='utf-8'))['plugins'][0]['version'])"
```

Expected: the same string four times.

- [ ] **Step 6: Commit**

```bash
git add docs/manual-checklist.md tests/plugin/test_docs.py
git commit -m "Add the manual checklist for the loop no test can run"
```

---

## What this plan does not do

- Run the manual checklist. Neither CLI is installed on the development machine, so the first person with one runs it and records the result in the table.
- Test `check` against a real GCC and CMake toolchain.
- Publish the repository or tag a release. That is step 3 of the spec's rollout, after the pilot.
- Handle two people whose email local parts collide, which would give them the same slug.
