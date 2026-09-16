# Plan 3: Harness Generation and Templates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate a complete harness inside a firmware repository: scan the tree into `harness/architecture.json`, write ARCHITECTURE.md documents with a generated block, install every entry document and template without overwriting anything, and upgrade a previously installed harness.

**Architecture:** Three new script groups next to the plan 1 and plan 2 scripts. `arch_scan.py` turns the real directory tree into a draft `architecture.json`; `arch_docs.py` renders the marked block that `arch_check` verifies, and `arch_sync.py` is the CLI behind the `fw-architecture-sync` skill. `manifest.py` names every file the harness owns, split into managed files (the plugin updates them) and team-owned files (created once, never overwritten); `install.py` and `upgrade.py` are the two CLIs behind `fw-harness-init` and `fw-harness-upgrade`. `review_docs.py` renders the Copilot review instructions from `harness/review-checklist.json`, so the checklist has one source. Everything stays standard library and every external command still comes from `harness/config.json`.

**Tech Stack:** Python 3.9+ standard library, git CLI, pytest (plugin development only).

**Spec:** `docs/superpowers/specs/2026-09-15-fw-c-harness-plugin-design.md`, sections 3.1, 4, 4.1, 6.1, 6.2, 6.3, 7, 8, 9.

**Split (this plan is 3 of 4):**
1. Identity, tickets, and state scripts (done)
2. Verification gates (done)
3. Harness generation and templates (this plan)
4. Skill files, both marketplace manifests, README, manual checklist

## Global Constraints

- English only in code, comments, messages, templates, and test data. Chinese appears only in `docs/**.zh-TW.md`.
- Python standard library only; Python 3.9 or newer. `Path.write_text` has no `newline` parameter on 3.9, so text writes go through `jsonio.write_text_atomic`.
- All reads and writes use UTF-8 with LF line endings; CLIs call `console.use_utf8_stdio()` first.
- Every failure message names the check, the file, and the fix (`... Fix: ...`).
- No em-dashes in prose, including generated documents.
- Scripts are flat modules in `SCRIPTS` and import each other by module name.
- Generated harness files never overwrite an existing file. The new content goes to `<name>.harness-proposed` and the report lists it (spec section 8).
- `harness/architecture.json` holds the approved rules. Documents render from it; nothing renders back into it.
- Commit messages in English, and each task ends with a commit.

## File Structure

`SCRIPTS` = `plugins/fw-c-harness/skills/fw-harness-init/templates/harness/scripts`
`TEMPLATES` = `plugins/fw-c-harness/skills/fw-harness-init/templates`

| File | Responsibility |
|---|---|
| `SCRIPTS/arch_scan.py` | Scan the tree: module folders, kinds, include dirs, observed dependencies, draft architecture |
| `SCRIPTS/arch_docs.py` | Render and apply the generated ARCHITECTURE.md block, create new documents |
| `SCRIPTS/arch_sync.py` | CLI: `scan` writes the draft architecture, `docs` refreshes every ARCHITECTURE.md |
| `SCRIPTS/arch_check.py` | Add the block consistency rule (spec section 6.3) |
| `SCRIPTS/review_docs.py` | Validate `harness/review-checklist.json` and render the Copilot instructions file |
| `SCRIPTS/manifest.py` | Managed, team-owned, generated, and executable file lists, plus content hashes |
| `SCRIPTS/install.py` | `fw-harness-init`: place files, create folders, merge settings, set `core.hooksPath`, write `.harness-version` |
| `SCRIPTS/upgrade.py` | `fw-harness-upgrade`: managed files update, team-owned files get proposals |
| `SCRIPTS/harness_config.py` | Add the optional `architecture` section |
| `SCRIPTS/jsonio.py` | Add `write_text_atomic` |
| `TEMPLATES/VERSION` | Plugin version, read by install and upgrade |
| `TEMPLATES/AGENTS.md`, `TEMPLATES/CLAUDE.md` | Entry documents (spec section 4.1) |
| `TEMPLATES/.github/copilot-instructions.md` | One pointer at AGENTS.md |
| `TEMPLATES/.clang-format`, `TEMPLATES/.gitignore` | Formatting and ignore defaults |
| `TEMPLATES/harness/review-policy.json`, `TEMPLATES/harness/review-checklist.json` | Review policy and the single checklist source |
| `TEMPLATES/docs/references/README.md`, `TEMPLATES/docs/deviations/README.md` | Folder purpose notes |
| `tests/fixtures/sample-fw/**/ARCHITECTURE.md` | Updated with generated blocks |
| `tests/scripts/test_arch_scan.py`, `test_arch_docs.py`, `test_arch_sync.py`, `test_review_docs.py`, `test_install.py`, `test_upgrade.py`, `test_end_to_end.py` | New test modules |

All commands run from `C:\Users\YANG\Desktop\fw-harness` with `py -3 -m pytest tests -q` unless a step says otherwise.

---

### Task 1: Scan settings, module folders, and kinds

**Files:**
- Modify: `SCRIPTS/harness_config.py`
- Create: `SCRIPTS/arch_scan.py`
- Test: `tests/scripts/test_arch_scan.py`
- Modify: `tests/scripts/test_harness_config.py`

**Interfaces:**
- Consumes: `arch_check.source_files`, `arch_check.module_of`, `harness_config.load_config`
- Produces:
  - `harness_config.validate_config` accepts an optional `architecture` object with `max_depth`, `deep_file_threshold` (positive integers), `vendor_patterns`, `test_patterns` (arrays of strings, possibly empty). Absent means defaults.
  - `arch_scan.DEFAULTS = {"max_depth": 2, "deep_file_threshold": 30, "vendor_patterns": [...], "test_patterns": [...]}`
  - `arch_scan.scan_settings(config) -> dict` (DEFAULTS merged with `config["architecture"]`)
  - `arch_scan.folder_counts(files) -> dict[str, int]` (C files directly in each folder, `""` for repo root)
  - `arch_scan.module_paths(files, settings) -> list[str]` (sorted repo-relative module folders, root files excluded)
  - `arch_scan.classify(repo, folder, files, settings) -> str` (one of `arch_check.KINDS`)

- [ ] **Step 1: Write the failing tests**

Create `tests/scripts/test_arch_scan.py`:

```python
import pytest

from arch_scan import DEFAULTS, classify, folder_counts, module_paths, scan_settings
from helpers import make_fixture_repo


@pytest.fixture
def fw(tmp_path):
    return make_fixture_repo(tmp_path / "fw")


def test_scan_settings_merges_over_defaults():
    assert scan_settings({}) == DEFAULTS
    settings = scan_settings({"architecture": {"max_depth": 3}})
    assert settings["max_depth"] == 3 and settings["vendor_patterns"] == DEFAULTS["vendor_patterns"]


def test_folder_counts_groups_by_folder():
    counts = folder_counts(["src/app/main.c", "src/app/app_config.h", "src/hal/hal.c", "boot.c"])
    assert counts == {"src/app": 2, "src/hal": 1, "": 1}


def test_module_paths_stop_at_max_depth():
    files = ["src/app/main.c", "src/drivers/uart/uart.c", "src/drivers/spi/spi.c", "boot.c"]
    assert module_paths(files, scan_settings({})) == ["src/app", "src/drivers"]


def test_module_paths_go_deeper_for_large_folders():
    files = [f"src/drivers/uart/f{n}.c" for n in range(20)] + [f"src/drivers/spi/f{n}.c" for n in range(20)]
    settings = scan_settings({"architecture": {"deep_file_threshold": 30}})
    assert module_paths(files, settings) == ["src/drivers/spi", "src/drivers/uart"]


def test_classify_by_pattern_and_generated_marker(fw):
    settings = scan_settings({})
    assert classify(fw, "src/drivers", ["src/drivers/uart.c"], settings) == "owned"
    assert classify(fw, "third_party/cmsis", ["third_party/cmsis/Include/core_cm4.h"], settings) == "vendor"
    assert classify(fw, "test", ["test/test_uart.c"], settings) == "test"
    generated = fw / "src" / "gen"
    generated.mkdir()
    (generated / "registers.h").write_text("/* @generated by svd2c, do not edit */\n", encoding="utf-8")
    assert classify(fw, "src/gen", ["src/gen/registers.h"], settings) == "generated"
```

Add to `tests/scripts/test_harness_config.py`:

```python
def test_architecture_section_is_optional_and_validated():
    config = fake_config()
    assert validate_config(config) == []
    config["architecture"] = {"max_depth": 2, "vendor_patterns": []}
    assert validate_config(config) == []
    config["architecture"] = {"max_depth": 0, "vendor_patterns": "third_party"}
    errors = validate_config(config)
    assert any("architecture.max_depth" in error for error in errors)
    assert any("architecture.vendor_patterns" in error for error in errors)
```

The existing test module already imports `validate_config` and `fake_config`; add the function at the end of the file.

- [ ] **Step 2: Run the tests and watch them fail**

Run: `py -3 -m pytest tests/scripts/test_arch_scan.py tests/scripts/test_harness_config.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'arch_scan'` and one failure in `test_architecture_section_is_optional_and_validated`.

- [ ] **Step 3: Accept the `architecture` section in `harness_config.py`**

Insert before `return errors` at the end of `validate_config`:

```python
    architecture = config.get("architecture")
    if architecture is not None:
        if not isinstance(architecture, dict):
            errors.append("architecture must be an object")
        else:
            for key in ("max_depth", "deep_file_threshold"):
                if key in architecture and not _is_positive(architecture[key]):
                    errors.append(f"architecture.{key} must be a positive integer")
            for key in ("vendor_patterns", "test_patterns"):
                if key in architecture and not _is_str_list(architecture[key], allow_empty=True):
                    errors.append(f"architecture.{key} must be an array of folder patterns")
```

- [ ] **Step 4: Write `SCRIPTS/arch_scan.py`**

```python
"""Scan a firmware tree and draft harness/architecture.json (spec section 6.1)."""
import fnmatch
import posixpath
import re
from pathlib import Path

DEFAULTS = {
    "max_depth": 2,
    "deep_file_threshold": 30,
    "vendor_patterns": ["third_party", "vendor", "external", "*cmsis*", "drivers/stm32*", "lib/*"],
    "test_patterns": ["test", "tests", "unit_test", "unittest", "*_test", "test_*"],
}
GENERATED_RE = re.compile(r"@generated|generated by|do not edit", re.IGNORECASE)
GENERATED_SCAN_LINES = 20


def scan_settings(config):
    settings = dict(DEFAULTS)
    settings.update(config.get("architecture") or {})
    return settings


def _matches(path, patterns):
    parts = path.lower().split("/")
    candidates = ["/".join(parts[:index + 1]) for index in range(len(parts))] + parts
    return any(fnmatch.fnmatchcase(candidate, pattern.lower())
               for candidate in candidates for pattern in patterns)


def folder_counts(files):
    counts = {}
    for name in files:
        folder = posixpath.dirname(name)
        counts[folder] = counts.get(folder, 0) + 1
    return counts


def subtree_count(counts, folder):
    return sum(count for path, count in counts.items()
               if path == folder or path.startswith(folder + "/"))


def module_paths(files, settings):
    counts = folder_counts(files)
    depth = settings["max_depth"]
    chosen = set()
    for folder in counts:
        if not folder:
            continue
        parts = folder.split("/")
        if len(parts) <= depth:
            chosen.add(folder)
            continue
        ancestor = "/".join(parts[:depth])
        if subtree_count(counts, ancestor) > settings["deep_file_threshold"]:
            chosen.add(folder)
        else:
            chosen.add(ancestor)
    return sorted(chosen)


def classify(repo, folder, files, settings):
    if _matches(folder, settings["vendor_patterns"]):
        return "vendor"
    if _matches(folder, settings["test_patterns"]):
        return "test"
    for name in files:
        text = (Path(repo) / name).read_text(encoding="utf-8", errors="replace")
        head = "\n".join(text.splitlines()[:GENERATED_SCAN_LINES])
        if GENERATED_RE.search(head):
            return "generated"
    return "owned"
```

- [ ] **Step 5: Run the tests and watch them pass**

Run: `py -3 -m pytest tests/scripts/test_arch_scan.py tests/scripts/test_harness_config.py -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add plugins/fw-c-harness/skills/fw-harness-init/templates/harness/scripts/arch_scan.py plugins/fw-c-harness/skills/fw-harness-init/templates/harness/scripts/harness_config.py tests/scripts/test_arch_scan.py tests/scripts/test_harness_config.py
git commit -m "Add architecture scan settings, module discovery, and kind classification"
```

---

### Task 2: Include dirs, observed dependencies, and the draft architecture

**Files:**
- Modify: `SCRIPTS/arch_scan.py`
- Test: `tests/scripts/test_arch_scan.py`

**Interfaces:**
- Consumes: `arch_check.dependencies`, `arch_check.module_of`, `arch_check.source_files`, Task 1 functions
- Produces:
  - `arch_scan.include_dirs(files, modules) -> list[str]` (folders holding headers, owned modules first)
  - `arch_scan.back_edges(edges) -> list[tuple[str, str]]` (edges that close a cycle, found by a deterministic depth-first search)
  - `arch_scan.draft_architecture(repo, config) -> (arch, report)` where `arch` matches the schema `arch_check.validate_architecture` accepts, and `report` is `{"observed": [(source, target), ...], "reverse": [...], "root_sources": [...]}`

- [ ] **Step 1: Write the failing tests**

Append to `tests/scripts/test_arch_scan.py`:

```python
from arch_scan import back_edges, draft_architecture, include_dirs
from arch_check import validate_architecture
from helpers import fake_config


def test_include_dirs_put_owned_folders_first():
    files = ["third_party/cmsis/Include/core_cm4.h", "src/app/app_config.h", "src/app/main.c"]
    modules = {"src/app": {"kind": "owned"}, "third_party/cmsis": {"kind": "vendor"}}
    assert include_dirs(files, modules) == ["src/app", "third_party/cmsis/Include"]


def test_back_edges_finds_the_edge_that_closes_a_cycle():
    assert back_edges([("a", "b"), ("b", "c")]) == []
    assert back_edges([("a", "b"), ("b", "a")]) == [("b", "a")]


def test_draft_architecture_of_the_sample_tree(fw):
    arch, report = draft_architecture(fw, fake_config())
    assert validate_architecture(arch) == []
    assert sorted(arch["modules"]) == ["src/app", "src/drivers", "src/hal", "test", "third_party/cmsis"]
    assert arch["modules"]["third_party/cmsis"]["kind"] == "vendor"
    assert arch["modules"]["test"]["kind"] == "test"
    assert arch["modules"]["src/app"]["allowed_deps"] == ["src/drivers"]
    assert arch["grandfathered"] == ["src/hal -> src/app"]
    assert ("src/hal", "src/app") in report["observed"] and report["root_sources"] == []
```

- [ ] **Step 2: Run the tests and watch them fail**

Run: `py -3 -m pytest tests/scripts/test_arch_scan.py -q`
Expected: FAIL with `ImportError: cannot import name 'include_dirs' from 'arch_scan'`.

- [ ] **Step 3: Extend `SCRIPTS/arch_scan.py`**

Add to the import block at the top:

```python
from arch_check import dependencies, module_of, source_files
```

Append to the module:

```python
def include_dirs(files, modules):
    headers = sorted({posixpath.dirname(name) for name in files
                      if name.endswith(".h") and posixpath.dirname(name)})
    owned, rest = [], []
    for folder in headers:
        module = module_of(folder, modules)
        target = owned if module and modules[module]["kind"] == "owned" else rest
        target.append(folder)
    return owned + rest


def back_edges(edges):
    graph = {}
    for source, target in edges:
        graph.setdefault(source, []).append(target)
    state, found = {}, set()

    def visit(node):
        state[node] = "open"
        for target in sorted(graph.get(node, [])):
            if state.get(target) == "open":
                found.add((node, target))
            elif target not in state:
                visit(target)
        state[node] = "done"

    for node in sorted({source for source, _ in edges} | {target for _, target in edges}):
        if node not in state:
            visit(node)
    return sorted(found)


def draft_architecture(repo, config):
    settings = scan_settings(config)
    files = source_files(repo)
    paths = module_paths(files, settings)
    grouped = {path: [] for path in paths}
    for name in files:
        module = module_of(name, grouped)
        if module is not None:
            grouped[module].append(name)
    modules = {path: {"kind": classify(repo, path, grouped[path], settings), "allowed_deps": []}
               for path in paths}
    arch = {"version": 1, "include_dirs": include_dirs(files, modules),
            "modules": modules, "grandfathered": []}

    observed = sorted(dependencies(repo, arch, files))
    reverse = set(back_edges(observed))
    for source, target in observed:
        if (source, target) in reverse:
            arch["grandfathered"].append(f"{source} -> {target}")
        else:
            modules[source]["allowed_deps"].append(target)
    arch["grandfathered"].sort()
    for module in modules.values():
        module["allowed_deps"].sort()
    report = {"observed": observed, "reverse": sorted(reverse),
              "root_sources": sorted(name for name in files if "/" not in name)}
    return arch, report
```

- [ ] **Step 4: Run the tests and watch them pass**

Run: `py -3 -m pytest tests/scripts/test_arch_scan.py -q`
Expected: PASS. If `test_draft_architecture_of_the_sample_tree` reports `src/hal -> src/app` as an allowed dependency instead of a grandfathered one, the fixture no longer contains the deliberate reverse dependency; restore `#include "app_config.h"` at `tests/fixtures/sample-fw/src/hal/hal_gpio.c:2`.

- [ ] **Step 5: Commit**

```bash
git add plugins/fw-c-harness/skills/fw-harness-init/templates/harness/scripts/arch_scan.py tests/scripts/test_arch_scan.py
git commit -m "Draft architecture.json from the real tree, grandfathering reverse dependencies"
```

---

### Task 3: The generated ARCHITECTURE.md block

**Files:**
- Modify: `SCRIPTS/jsonio.py`
- Create: `SCRIPTS/arch_docs.py`
- Test: `tests/scripts/test_arch_docs.py`

**Interfaces:**
- Consumes: nothing from the other new modules
- Produces:
  - `jsonio.write_text_atomic(path, text)` (UTF-8, LF, temporary file plus rename)
  - `arch_docs.BEGIN = "<!-- fw-harness:architecture:begin -->"`, `arch_docs.END = "<!-- fw-harness:architecture:end -->"`
  - `arch_docs.render_block(path, arch) -> str`
  - `arch_docs.render_root(arch) -> str`
  - `arch_docs.block_of(text) -> str | None`
  - `arch_docs.apply_block(text, block) -> str`
  - `arch_docs.summary_for(path, files) -> str`
  - `arch_docs.new_document(path, summary, block) -> str`
  - `arch_docs.new_root_document(block) -> str`

- [ ] **Step 1: Write the failing tests**

Create `tests/scripts/test_arch_docs.py`:

```python
from arch_docs import (BEGIN, END, apply_block, block_of, new_document, new_root_document,
                       render_block, render_root, summary_for)
from jsonio import write_text_atomic

ARCH = {
    "version": 1,
    "include_dirs": ["src/app"],
    "modules": {
        "src/app": {"kind": "owned", "allowed_deps": ["src/hal"]},
        "src/hal": {"kind": "owned", "allowed_deps": []},
        "third_party/cmsis": {"kind": "vendor", "allowed_deps": []},
    },
    "grandfathered": ["src/hal -> src/app"],
}


def test_render_block_lists_kind_and_approved_dependencies():
    block = render_block("src/app", ARCH)
    assert block.startswith(BEGIN) and block.endswith(END)
    assert "- Kind: owned" in block
    assert "- Approved dependencies: src/hal" in block
    assert "Grandfathered" not in block


def test_render_block_marks_vendor_read_only_and_names_grandfathered_edges():
    assert "Read-only" in render_block("third_party/cmsis", ARCH)
    assert "- Approved dependencies: none" in render_block("src/hal", ARCH)
    assert "Grandfathered dependencies (remove them, do not add more): src/app" in render_block("src/hal", ARCH)


def test_render_root_tabulates_every_module():
    root = render_root(ARCH)
    assert "| src/app | owned | src/hal |" in root
    assert "- src/hal -> src/app" in root


def test_block_of_and_apply_block_round_trip():
    block = render_block("src/app", ARCH)
    document = new_document("src/app", "Holds 1 .c and 1 .h files.", block)
    assert block_of(document) == block
    changed = render_block("src/hal", ARCH)
    updated = apply_block(document, changed)
    assert block_of(updated) == changed
    assert "# src/app" in updated


def test_apply_block_appends_when_the_document_has_no_block():
    assert apply_block("# src/app\n\nHand written notes.\n", "BLOCK") == "# src/app\n\nHand written notes.\n\nBLOCK\n"
    assert block_of("# src/app\n") is None


def test_summary_for_counts_files_and_names_headers():
    summary = summary_for("src/app", ["src/app/main.c", "src/app/app_config.h"])
    assert summary == "Holds 1 .c and 1 .h files. Public headers: app_config.h."


def test_new_root_document_contains_the_block_and_human_sections():
    document = new_root_document(render_root(ARCH))
    assert document.startswith("# Repository architecture")
    assert "## How to read this map" in document and END in document


def test_write_text_atomic_uses_lf(tmp_path):
    target = tmp_path / "notes.md"
    write_text_atomic(target, "a\nb\n")
    assert target.read_bytes() == b"a\nb\n"
```

- [ ] **Step 2: Run the tests and watch them fail**

Run: `py -3 -m pytest tests/scripts/test_arch_docs.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'arch_docs'`.

- [ ] **Step 3: Add `write_text_atomic` to `SCRIPTS/jsonio.py`**

Change the module docstring to:

```python
"""UTF-8 file I/O. Writes go through a temporary file and a rename, so a crash never leaves a half-written file."""
```

Append:

```python
def write_text_atomic(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
```

- [ ] **Step 4: Write `SCRIPTS/arch_docs.py`**

```python
"""Render the generated block in ARCHITECTURE.md from harness/architecture.json (spec section 6.2)."""
import posixpath

BEGIN = "<!-- fw-harness:architecture:begin -->"
END = "<!-- fw-harness:architecture:end -->"
NOTICE = "<!-- Generated from harness/architecture.json. Run fw-architecture-sync after changing it. -->"
READ_ONLY = ("Read-only. Upgrade this folder from its upstream source instead of editing it here, "
             "and record the version in the section above.")


def _grandfathered_from(path, arch):
    prefix = path + " -> "
    return [entry[len(prefix):] for entry in sorted(arch["grandfathered"]) if entry.startswith(prefix)]


def render_block(path, arch):
    module = arch["modules"][path]
    lines = [BEGIN, NOTICE, "", f"- Kind: {module['kind']}"]
    if module["kind"] in ("vendor", "generated"):
        lines.append(f"- {READ_ONLY}")
    lines.append("- Approved dependencies: " + (", ".join(module["allowed_deps"]) or "none"))
    owed = _grandfathered_from(path, arch)
    if owed:
        lines.append("- Grandfathered dependencies (remove them, do not add more): " + ", ".join(owed))
    lines += ["", END]
    return "\n".join(lines)


def render_root(arch):
    lines = [BEGIN, NOTICE, "",
             "| Module | Kind | Approved dependencies |",
             "|---|---|---|"]
    for path in sorted(arch["modules"]):
        module = arch["modules"][path]
        lines.append(f"| {path} | {module['kind']} | {', '.join(module['allowed_deps']) or 'none'} |")
    if arch["grandfathered"]:
        lines += ["", "Grandfathered dependencies (the list may only shrink):"]
        lines += [f"- {entry}" for entry in sorted(arch["grandfathered"])]
    lines += ["", END]
    return "\n".join(lines)


def block_of(text):
    start = text.find(BEGIN)
    end = text.find(END)
    if start < 0 or end < start:
        return None
    return text[start:end + len(END)]


def apply_block(text, block):
    current = block_of(text)
    if current is not None:
        return text.replace(current, block)
    body = text.rstrip("\n")
    return (body + "\n\n" if body else "") + block + "\n"


def summary_for(path, files):
    sources = sum(1 for name in files if name.endswith(".c"))
    headers = sorted(name for name in files if name.endswith(".h"))
    shown = ", ".join(posixpath.basename(name) for name in headers[:3]) if headers else "none"
    return f"Holds {sources} .c and {len(headers)} .h files. Public headers: {shown}."


def new_document(path, summary, block):
    return "\n".join([
        f"# {path}",
        "",
        "## Responsibility",
        "",
        f"{summary} Written by fw-harness from the file listing, so replace this line with the "
        "one sentence a new colleague needs.",
        "",
        "## Entry points",
        "",
        "List the functions other modules are meant to call, and where the module is initialised.",
        "",
        "## ISR and memory notes",
        "",
        "List interrupt handlers, state shared with the main loop, buffers, and who owns them.",
        "",
        "## Approved dependencies",
        "",
        block,
        "",
    ])


def new_root_document(block):
    return "\n".join([
        "# Repository architecture",
        "",
        "## How to read this map",
        "",
        "Each module below has its own ARCHITECTURE.md next to the code. Read that one before "
        "changing a file. A module may include headers only from its approved dependencies; "
        "`check` enforces the table.",
        "",
        "## Modules",
        "",
        block,
        "",
        "## Adding a module",
        "",
        "Create the folder, run fw-architecture-sync, then have a human approve the new "
        "dependencies in harness/architecture.json.",
        "",
    ])
```

- [ ] **Step 5: Run the tests and watch them pass**

Run: `py -3 -m pytest tests/scripts/test_arch_docs.py -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add plugins/fw-c-harness/skills/fw-harness-init/templates/harness/scripts/arch_docs.py plugins/fw-c-harness/skills/fw-harness-init/templates/harness/scripts/jsonio.py tests/scripts/test_arch_docs.py
git commit -m "Render the generated ARCHITECTURE.md block and document skeletons"
```

---

### Task 4: `arch_check` verifies the generated block

**Files:**
- Modify: `SCRIPTS/arch_check.py`
- Modify: `tests/fixtures/sample-fw/src/app/ARCHITECTURE.md`, `src/drivers/ARCHITECTURE.md`, `src/hal/ARCHITECTURE.md`, `test/ARCHITECTURE.md`, `third_party/cmsis/ARCHITECTURE.md`
- Create: `tests/fixtures/sample-fw/ARCHITECTURE.md`
- Test: `tests/scripts/test_arch_check.py`

**Interfaces:**
- Consumes: `arch_docs.block_of`, `arch_docs.render_block`, `arch_docs.render_root`
- Produces: `arch_check.check_architecture` gains two errors: a module document whose block differs from `architecture.json`, and a root `ARCHITECTURE.md` (when present) whose block differs.

- [ ] **Step 1: Write the failing test**

Append to `tests/scripts/test_arch_check.py`:

```python
def test_block_must_agree_with_the_json(fw):
    errors, _ = check_architecture(fw)
    assert errors == []
    doc = fw / "src" / "app" / "ARCHITECTURE.md"
    doc.write_text(doc.read_text(encoding="utf-8").replace("Approved dependencies: src/drivers",
                                                          "Approved dependencies: src/hal"), encoding="utf-8")
    errors, _ = check_architecture(fw)
    assert len(errors) == 1
    assert "src/app/ARCHITECTURE.md" in errors[0] and "fw-architecture-sync" in errors[0]


def test_root_document_block_is_checked_when_present(fw):
    root = fw / "ARCHITECTURE.md"
    root.write_text(root.read_text(encoding="utf-8").replace("| test | test | none |", ""), encoding="utf-8")
    errors, _ = check_architecture(fw)
    assert len(errors) == 1 and errors[0].startswith("ARCHITECTURE.md")
```

The module already imports `check_architecture` and defines the `fw` fixture; reuse them.

- [ ] **Step 2: Run the tests and watch them fail**

Run: `py -3 -m pytest tests/scripts/test_arch_check.py -q`
Expected: FAIL. Both new tests fail because no block rule exists yet and the fixture documents carry no block.

- [ ] **Step 3: Add the rule to `SCRIPTS/arch_check.py`**

Add the import:

```python
import arch_docs
```

Replace the module loop inside `check_architecture`:

```python
    for path in sorted(modules):
        if not (Path(repo) / path).is_dir():
            warnings.append(f"{path}: listed in {ARCH_PATH} but the folder no longer exists. Fix: remove it from modules")
            continue
        doc = Path(repo) / path / "ARCHITECTURE.md"
        if not doc.is_file():
            errors.append(f"{path}: missing ARCHITECTURE.md. Fix: run fw-architecture-sync")
        elif arch_docs.block_of(doc.read_text(encoding="utf-8", errors="replace")) != arch_docs.render_block(path, arch):
            errors.append(f"{path}/ARCHITECTURE.md: the generated block disagrees with {ARCH_PATH}. "
                          "Fix: run fw-architecture-sync")
```

Add the root document rule right after that loop:

```python
    root_doc = Path(repo) / "ARCHITECTURE.md"
    if root_doc.is_file() and arch_docs.block_of(root_doc.read_text(encoding="utf-8", errors="replace")) != arch_docs.render_root(arch):
        errors.append(f"ARCHITECTURE.md: the generated block disagrees with {ARCH_PATH}. "
                      "Fix: run fw-architecture-sync")
```

- [ ] **Step 4: Put the generated blocks into the fixture documents**

`tests/fixtures/sample-fw/src/app/ARCHITECTURE.md`:

```markdown
# src/app

Application layer of the sample firmware used by the fw-harness tests.

<!-- fw-harness:architecture:begin -->
<!-- Generated from harness/architecture.json. Run fw-architecture-sync after changing it. -->

- Kind: owned
- Approved dependencies: src/drivers

<!-- fw-harness:architecture:end -->
```

`tests/fixtures/sample-fw/src/drivers/ARCHITECTURE.md`:

```markdown
# src/drivers

Peripheral drivers for the sample firmware used by the fw-harness tests.

<!-- fw-harness:architecture:begin -->
<!-- Generated from harness/architecture.json. Run fw-architecture-sync after changing it. -->

- Kind: owned
- Approved dependencies: src/hal

<!-- fw-harness:architecture:end -->
```

`tests/fixtures/sample-fw/src/hal/ARCHITECTURE.md`:

```markdown
# src/hal

Hardware abstraction layer for the sample firmware used by the fw-harness tests.

<!-- fw-harness:architecture:begin -->
<!-- Generated from harness/architecture.json. Run fw-architecture-sync after changing it. -->

- Kind: owned
- Approved dependencies: third_party/cmsis
- Grandfathered dependencies (remove them, do not add more): src/app

<!-- fw-harness:architecture:end -->
```

`tests/fixtures/sample-fw/test/ARCHITECTURE.md`:

```markdown
# test

Unity tests for the sample firmware used by the fw-harness tests.

<!-- fw-harness:architecture:begin -->
<!-- Generated from harness/architecture.json. Run fw-architecture-sync after changing it. -->

- Kind: test
- Approved dependencies: none

<!-- fw-harness:architecture:end -->
```

`tests/fixtures/sample-fw/third_party/cmsis/ARCHITECTURE.md`:

```markdown
# third_party/cmsis

Vendor headers for the sample firmware used by the fw-harness tests.

<!-- fw-harness:architecture:begin -->
<!-- Generated from harness/architecture.json. Run fw-architecture-sync after changing it. -->

- Kind: vendor
- Read-only. Upgrade this folder from its upstream source instead of editing it here, and record the version in the section above.
- Approved dependencies: none

<!-- fw-harness:architecture:end -->
```

Create `tests/fixtures/sample-fw/ARCHITECTURE.md`:

```markdown
# Repository architecture

Sample firmware tree used by the fw-harness tests.

<!-- fw-harness:architecture:begin -->
<!-- Generated from harness/architecture.json. Run fw-architecture-sync after changing it. -->

| Module | Kind | Approved dependencies |
|---|---|---|
| src/app | owned | src/drivers |
| src/drivers | owned | src/hal |
| src/hal | owned | third_party/cmsis |
| test | test | none |
| third_party/cmsis | vendor | none |

Grandfathered dependencies (the list may only shrink):
- src/hal -> src/app

<!-- fw-harness:architecture:end -->
```

- [ ] **Step 5: Run the whole suite**

Run: `py -3 -m pytest tests -q`
Expected: PASS. Every module that builds a repo from the fixture now also exercises the block rule, so a failure elsewhere means a fixture document and `harness/architecture.json` disagree; compare them line by line rather than relaxing the rule.

- [ ] **Step 6: Commit**

```bash
git add plugins/fw-c-harness/skills/fw-harness-init/templates/harness/scripts/arch_check.py tests/fixtures/sample-fw tests/scripts/test_arch_check.py
git commit -m "Fail arch_check when a generated ARCHITECTURE.md block drifts from the json"
```

---

### Task 5: `arch_sync.py`, the CLI behind `fw-architecture-sync`

**Files:**
- Create: `SCRIPTS/arch_sync.py`
- Test: `tests/scripts/test_arch_sync.py`

**Interfaces:**
- Consumes: `arch_scan.draft_architecture`, `arch_docs.*`, `arch_check.load_architecture`, `arch_check.module_of`, `arch_check.source_files`, `harness_config.load_config`, `jsonio.write_json_atomic`, `jsonio.write_text_atomic`
- Produces:
  - `arch_sync.PROPOSED_SUFFIX = ".harness-proposed"`
  - `arch_sync.is_skeleton(path) -> bool` (missing file or empty `modules`)
  - `arch_sync.scan(repo, force=False) -> (written_path, arch, report)`
  - `arch_sync.docs(repo) -> list[str]` (repo-relative documents created or changed)
  - `arch_sync.main(argv=None, cwd=None) -> int` for `scan [--force]` and `docs`

- [ ] **Step 1: Write the failing tests**

Create `tests/scripts/test_arch_sync.py`:

```python
import json

import pytest

import arch_sync
from arch_check import check_architecture
from arch_docs import block_of, render_block
from helpers import fake_config, make_fixture_repo, make_repo, write_config


@pytest.fixture
def fw(tmp_path):
    repo = make_fixture_repo(tmp_path / "fw")
    write_config(repo, fake_config())
    return repo


@pytest.fixture
def bare(tmp_path):
    """A repo with the sample sources but no architecture.json and no documents."""
    repo = make_fixture_repo(tmp_path / "bare")
    (repo / "harness" / "architecture.json").unlink()
    (repo / "ARCHITECTURE.md").unlink()
    for folder in ("src/app", "src/drivers", "src/hal", "test", "third_party/cmsis"):
        (repo / folder / "ARCHITECTURE.md").unlink()
    write_config(repo, fake_config())
    return repo


def test_scan_writes_the_architecture_when_none_exists(bare):
    written, arch, report = arch_sync.scan(bare)
    assert written == "harness/architecture.json"
    assert json.loads((bare / written).read_text(encoding="utf-8"))["modules"] == arch["modules"]
    assert report["reverse"] == [("src/hal", "src/app")]


def test_scan_proposes_instead_of_overwriting_an_approved_architecture(fw):
    written, _, _ = arch_sync.scan(fw)
    assert written == "harness/architecture.json.harness-proposed"
    assert (fw / written).is_file()
    assert json.loads((fw / "harness" / "architecture.json").read_text(encoding="utf-8"))["grandfathered"] == [
        "src/hal -> src/app"]


def test_scan_force_overwrites(fw):
    written, _, _ = arch_sync.scan(fw, force=True)
    assert written == "harness/architecture.json"


def test_docs_creates_every_missing_document_and_passes_arch_check(bare):
    arch_sync.scan(bare)
    written = arch_sync.docs(bare)
    assert "ARCHITECTURE.md" in written and "src/app/ARCHITECTURE.md" in written
    errors, _ = check_architecture(bare)
    assert errors == []


def test_docs_keeps_human_text_and_refreshes_only_the_block(fw):
    doc = fw / "src" / "app" / "ARCHITECTURE.md"
    doc.write_text(doc.read_text(encoding="utf-8") + "\n## Notes\n\nKeep me.\n", encoding="utf-8")
    arch = json.loads((fw / "harness" / "architecture.json").read_text(encoding="utf-8"))
    arch["modules"]["src/app"]["allowed_deps"] = ["src/drivers", "src/hal"]
    (fw / "harness" / "architecture.json").write_text(json.dumps(arch, indent=2), encoding="utf-8")
    assert "src/app/ARCHITECTURE.md" in arch_sync.docs(fw)
    text = doc.read_text(encoding="utf-8")
    assert "Keep me." in text and block_of(text) == render_block("src/app", arch)


def test_docs_is_idempotent(fw):
    assert arch_sync.docs(fw) == []


def test_main_reports_what_it_wrote(bare, capsys):
    assert arch_sync.main(["scan"], cwd=bare) == 0
    assert arch_sync.main(["docs"], cwd=bare) == 0
    output = capsys.readouterr().out
    assert "harness/architecture.json" in output and "ARCHITECTURE.md" in output


def test_main_without_sources_explains_the_problem(tmp_path, capsys):
    repo = make_repo(tmp_path / "empty", "Alice Chen", "alice@example.com")
    write_config(repo, fake_config())
    assert arch_sync.main(["scan"], cwd=repo) == 1
    assert "no C sources" in capsys.readouterr().err
```

- [ ] **Step 2: Run the tests and watch them fail**

Run: `py -3 -m pytest tests/scripts/test_arch_sync.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'arch_sync'`.

- [ ] **Step 3: Write `SCRIPTS/arch_sync.py`**

```python
"""fw-architecture-sync helper: draft harness/architecture.json and refresh ARCHITECTURE.md (spec section 6.1)."""
import argparse
import sys
from pathlib import Path

import arch_docs
from arch_check import ARCH_PATH, ArchitectureError, load_architecture, module_of, source_files
from arch_scan import draft_architecture
from console import use_utf8_stdio
from gitutil import repo_root
from harness_config import ConfigError, load_config
from jsonio import read_json, write_json_atomic, write_text_atomic

PROPOSED_SUFFIX = ".harness-proposed"
DOC_NAME = "ARCHITECTURE.md"


def is_skeleton(path):
    path = Path(path)
    if not path.is_file():
        return True
    try:
        return not read_json(path).get("modules")
    except (ValueError, UnicodeDecodeError):
        return False


def scan(repo, force=False):
    config = load_config(repo)
    arch, report = draft_architecture(repo, config)
    if not arch["modules"]:
        raise ArchitectureError("found no C sources to scan. "
                                "Fix: run this from a repository that has .c or .h files committed or untracked")
    target = Path(repo) / ARCH_PATH
    written = ARCH_PATH
    if not (force or is_skeleton(target)):
        target = target.with_name(target.name + PROPOSED_SUFFIX)
        written = ARCH_PATH + PROPOSED_SUFFIX
    write_json_atomic(target, arch)
    return written, arch, report


def _sync(doc, block, build_new):
    text = doc.read_text(encoding="utf-8") if doc.is_file() else None
    updated = arch_docs.apply_block(text, block) if text is not None else build_new(block)
    if updated == text:
        return False
    write_text_atomic(doc, updated)
    return True


def docs(repo):
    repo = Path(repo)
    arch = load_architecture(repo)
    grouped = {path: [] for path in arch["modules"]}
    for name in source_files(repo):
        module = module_of(name, grouped)
        if module is not None:
            grouped[module].append(name)

    written = []
    for path in sorted(arch["modules"]):
        folder = repo / path
        if not folder.is_dir():
            continue
        block = arch_docs.render_block(path, arch)
        summary = arch_docs.summary_for(path, grouped[path])
        if _sync(folder / DOC_NAME, block, lambda b, p=path, s=summary: arch_docs.new_document(p, s, b)):
            written.append(f"{path}/{DOC_NAME}")
    if _sync(repo / DOC_NAME, arch_docs.render_root(arch), arch_docs.new_root_document):
        written.append(DOC_NAME)
    return written


def main(argv=None, cwd=None):
    use_utf8_stdio()
    parser = argparse.ArgumentParser(prog="arch_sync", description="Draft architecture.json and refresh ARCHITECTURE.md")
    sub = parser.add_subparsers(dest="command", required=True)
    scan_parser = sub.add_parser("scan", help="write a draft architecture.json from the tree")
    scan_parser.add_argument("--force", action="store_true", help="overwrite an approved architecture.json")
    sub.add_parser("docs", help="create or refresh every ARCHITECTURE.md")
    args = parser.parse_args(argv)

    repo = repo_root(cwd or Path.cwd())
    try:
        if args.command == "scan":
            written, arch, report = scan(repo, force=args.force)
            print(f"arch_sync: wrote {written} with {len(arch['modules'])} modules")
            for source, target in report["reverse"]:
                print(f"arch_sync: grandfathered reverse dependency {source} -> {target}. "
                      "Fix it or have a human confirm it stays")
            for name in report["root_sources"]:
                print(f"arch_sync: {name} sits at the repository root and belongs to no module. "
                      "Fix: move it into a folder")
            if written.endswith(PROPOSED_SUFFIX):
                print(f"arch_sync: {ARCH_PATH} already holds approved rules, so the draft went to {written}. "
                      "Fix: compare them and copy over the parts a human approves")
        else:
            for name in docs(repo) or []:
                print(f"arch_sync: wrote {name}")
            print("arch_sync: documents match harness/architecture.json")
    except (ArchitectureError, ConfigError) as exc:
        print(f"arch_sync failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 4: Run the tests and watch them pass**

Run: `py -3 -m pytest tests/scripts/test_arch_sync.py -q`
Expected: PASS.

- [ ] **Step 5: Run the whole suite**

Run: `py -3 -m pytest tests -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add plugins/fw-c-harness/skills/fw-harness-init/templates/harness/scripts/arch_sync.py tests/scripts/test_arch_sync.py
git commit -m "Add arch_sync CLI for drafting architecture.json and writing documents"
```

---

### Task 6: Review checklist source and the generated Copilot instructions

**Files:**
- Create: `TEMPLATES/harness/review-checklist.json`
- Create: `TEMPLATES/harness/review-policy.json`
- Create: `SCRIPTS/review_docs.py`
- Test: `tests/scripts/test_review_docs.py`

**Interfaces:**
- Consumes: `jsonio.read_json`
- Produces:
  - `review_docs.CHECKLIST_PATH = "harness/review-checklist.json"`, `POLICY_PATH = "harness/review-policy.json"`, `INSTRUCTIONS_PATH = ".github/instructions/c-fw-review.instructions.md"`
  - `review_docs.ReviewDocsError(ValueError)`
  - `review_docs.validate_checklist(checklist) -> list[str]`, `validate_policy(policy) -> list[str]`
  - `review_docs.load_checklist(repo) -> dict`, `load_policy(repo) -> dict`
  - `review_docs.render_instructions(checklist, policy) -> str`

- [ ] **Step 1: Write the failing tests**

Create `tests/scripts/test_review_docs.py`:

```python
import json

import pytest

from helpers import TEMPLATES, make_repo
from review_docs import (CHECKLIST_PATH, POLICY_PATH, ReviewDocsError, load_checklist, load_policy,
                         render_instructions, validate_checklist, validate_policy)

CHECKLIST = json.loads((TEMPLATES / "harness" / "review-checklist.json").read_text(encoding="utf-8"))
POLICY = json.loads((TEMPLATES / "harness" / "review-policy.json").read_text(encoding="utf-8"))


@pytest.fixture
def repo(tmp_path):
    fw = make_repo(tmp_path / "fw", "Alice Chen", "alice@example.com")
    for name in (CHECKLIST_PATH, POLICY_PATH):
        (fw / name).write_text((TEMPLATES / name).read_text(encoding="utf-8"), encoding="utf-8")
    return fw


def test_shipped_checklist_and_policy_are_valid():
    assert validate_checklist(CHECKLIST) == [] and validate_policy(POLICY) == []


def test_validate_checklist_names_the_broken_key():
    broken = {"version": 1, "axes": [], "severities": [{"level": "critical"}]}
    errors = validate_checklist(broken)
    assert any("axes" in error for error in errors)
    assert any("severities[0]" in error for error in errors)


def test_validate_policy_rejects_an_unknown_misra_mode():
    policy = json.loads(json.dumps(POLICY))
    policy["misra"]["mode"] = "strict"
    assert any("misra.mode" in error for error in validate_policy(policy))


def test_load_reports_a_missing_file_with_a_fix(tmp_path):
    empty = make_repo(tmp_path / "empty", "Alice Chen", "alice@example.com")
    with pytest.raises(ReviewDocsError, match="fw-harness-init"):
        load_checklist(empty)


def test_render_instructions_covers_every_axis_and_severity(repo):
    text = render_instructions(load_checklist(repo), load_policy(repo))
    assert text.startswith('---\napplyTo: "**/*.{c,h}"\n---\n')
    assert "harness/review-checklist.json" in text
    for axis in CHECKLIST["axes"]:
        assert f"## {axis['title']}" in text
    for severity in CHECKLIST["severities"]:
        assert severity["label"] in text
        for item in severity["items"]:
            assert item in text
    assert "MISRA C:2012" in text and "advisory" in text


def test_render_instructions_is_deterministic(repo):
    checklist, policy = load_checklist(repo), load_policy(repo)
    assert render_instructions(checklist, policy) == render_instructions(checklist, policy)
```

- [ ] **Step 2: Run the tests and watch them fail**

Run: `py -3 -m pytest tests/scripts/test_review_docs.py -q`
Expected: FAIL while collecting, because `TEMPLATES/harness/review-checklist.json` does not exist yet.

- [ ] **Step 3: Create `TEMPLATES/harness/review-checklist.json`**

```json
{
  "version": 1,
  "axes": [
    {
      "key": "standards",
      "title": "Standards",
      "question": "Does the code follow the C and firmware checklist, the approved layering in harness/architecture.json, and the MISRA mode in harness/review-policy.json?"
    },
    {
      "key": "spec",
      "title": "Spec",
      "question": "Does the code deliver the ticket's user_visible_behavior and verification_steps? Report missing requirements, partial requirements, behaviour nobody asked for, and requirements that look implemented incorrectly."
    }
  ],
  "severities": [
    {
      "level": "critical",
      "icon": "\ud83d\udd34",
      "label": "Critical (blocks merge)",
      "items": [
        "undefined behaviour, including signed overflow, misaligned access, and use after free",
        "an array or pointer access that can leave its object",
        "an integer overflow or truncation that changes the result",
        "state shared between an interrupt handler and the main loop without protection",
        "a missing volatile on a register or on state an interrupt handler writes",
        "an ignored error return code",
        "an external length or index used without validation",
        "a debug port left open, or a key or password in the source",
        "a layering violation that is not in the grandfather list"
      ]
    },
    {
      "level": "important",
      "icon": "\ud83d\udfe1",
      "label": "Important",
      "items": [
        "new logic with no test",
        "a resource acquired and not released on every path",
        "a blocking call on a time critical path",
        "a magic number standing in for a register address or a timeout"
      ]
    },
    {
      "level": "suggestion",
      "icon": "\ud83d\udfe2",
      "label": "Suggestion",
      "items": [
        "naming that does not match the module it lives in",
        "a comment that explains what the code does instead of why",
        "readability: deep nesting, a function doing several jobs",
        "a MISRA advisory rule, while the mode is advisory"
      ]
    }
  ],
  "finding_fields": ["severity", "path:line", "problem", "why it matters", "suggested fix", "confidence"]
}
```

- [ ] **Step 4: Create `TEMPLATES/harness/review-policy.json`**

```json
{
  "misra": {"standard": "MISRA C:2012", "mode": "advisory"},
  "block_on": ["critical"],
  "forbid_self_review": true
}
```

- [ ] **Step 5: Write `SCRIPTS/review_docs.py`**

```python
"""Review checklist source and the Copilot instructions generated from it (spec section 7)."""
import json
from pathlib import Path

from jsonio import read_json

CHECKLIST_PATH = "harness/review-checklist.json"
POLICY_PATH = "harness/review-policy.json"
INSTRUCTIONS_PATH = ".github/instructions/c-fw-review.instructions.md"
MISRA_MODES = ("off", "advisory", "required")
MODE_NOTES = {
    "off": "MISRA is not part of this review.",
    "advisory": "MISRA findings rank at most the lowest severity and never block a merge.",
    "required": "Breaking a required MISRA rule without a record in docs/deviations/ is a critical finding.",
}


class ReviewDocsError(ValueError):
    pass


def _is_str_list(value):
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item for item in value)


def validate_checklist(checklist):
    if not isinstance(checklist, dict):
        return ["checklist must be a JSON object"]
    errors = []
    if checklist.get("version") != 1:
        errors.append("version must be 1")
    axes = checklist.get("axes")
    if not (isinstance(axes, list) and axes):
        errors.append("axes must be a non-empty array")
    else:
        for index, axis in enumerate(axes):
            if not (isinstance(axis, dict) and all(isinstance(axis.get(key), str) and axis.get(key)
                                                   for key in ("key", "title", "question"))):
                errors.append(f"axes[{index}] must have key, title, and question")
    severities = checklist.get("severities")
    if not (isinstance(severities, list) and severities):
        errors.append("severities must be a non-empty array")
    else:
        for index, severity in enumerate(severities):
            if not isinstance(severity, dict):
                errors.append(f"severities[{index}] must be an object")
                continue
            if not all(isinstance(severity.get(key), str) and severity.get(key)
                       for key in ("level", "icon", "label")):
                errors.append(f"severities[{index}] must have level, icon, and label")
            if not _is_str_list(severity.get("items")):
                errors.append(f"severities[{index}].items must be a non-empty array of strings")
    if not _is_str_list(checklist.get("finding_fields")):
        errors.append("finding_fields must be a non-empty array of strings")
    return errors


def validate_policy(policy):
    if not isinstance(policy, dict):
        return ["policy must be a JSON object"]
    errors = []
    misra = policy.get("misra")
    if not isinstance(misra, dict):
        errors.append("misra must be an object with standard and mode")
    else:
        if not isinstance(misra.get("standard"), str) or not misra.get("standard"):
            errors.append("misra.standard must be the standard name")
        if misra.get("mode") not in MISRA_MODES:
            errors.append(f"misra.mode must be one of {', '.join(MISRA_MODES)}")
    if not _is_str_list(policy.get("block_on")):
        errors.append("block_on must be a non-empty array of severity levels")
    if not isinstance(policy.get("forbid_self_review"), bool):
        errors.append("forbid_self_review must be true or false")
    return errors


def _load(repo, relative, validator):
    path = Path(repo) / relative
    if not path.is_file():
        raise ReviewDocsError(f"{relative} not found. Fix: run fw-harness-init to create it")
    try:
        data = read_json(path)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ReviewDocsError(f"{relative} is not valid JSON ({exc}). Fix: repair it or restore it from git") from exc
    errors = validator(data)
    if errors:
        raise ReviewDocsError(f"{relative} is invalid:\n- " + "\n- ".join(errors))
    return data


def load_checklist(repo):
    return _load(repo, CHECKLIST_PATH, validate_checklist)


def load_policy(repo):
    return _load(repo, POLICY_PATH, validate_policy)


def render_instructions(checklist, policy):
    mode = policy["misra"]["mode"]
    lines = ['---', 'applyTo: "**/*.{c,h}"', '---', "",
             "# C firmware review",
             "",
             f"Generated from {CHECKLIST_PATH} and {POLICY_PATH}. Edit those files, not this one.",
             "",
             "Review every changed C file along the axes below and report them separately, "
             "without merging or reranking them.",
             ""]
    for axis in checklist["axes"]:
        lines += [f"## {axis['title']}", "", axis["question"], ""]
    lines += ["## Severity", ""]
    for severity in checklist["severities"]:
        lines += [f"### {severity['icon']} {severity['label']}", ""]
        lines += [f"- {item}" for item in severity["items"]]
        lines.append("")
    lines += ["## MISRA", "",
              f"Standard: {policy['misra']['standard']}. Mode: {mode}. {MODE_NOTES[mode]}",
              "",
              "## Reporting", "",
              "Each finding carries: " + ", ".join(checklist["finding_fields"]) + ".",
              "",
              "Verify each finding before reporting it: re-read the code and rule out a problem "
              "that is already handled before this point. Propose a patch and leave applying it to a human.",
              ""]
    return "\n".join(lines)
```

- [ ] **Step 6: Run the tests and watch them pass**

Run: `py -3 -m pytest tests/scripts/test_review_docs.py -q`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add plugins/fw-c-harness/skills/fw-harness-init/templates/harness/review-checklist.json plugins/fw-c-harness/skills/fw-harness-init/templates/harness/review-policy.json plugins/fw-c-harness/skills/fw-harness-init/templates/harness/scripts/review_docs.py tests/scripts/test_review_docs.py
git commit -m "Add the review checklist source and render the Copilot review instructions from it"
```

---

### Task 7: Entry documents, remaining templates, and the manifest

**Files:**
- Create: `TEMPLATES/VERSION`, `TEMPLATES/AGENTS.md`, `TEMPLATES/CLAUDE.md`, `TEMPLATES/.github/copilot-instructions.md`, `TEMPLATES/.clang-format`, `TEMPLATES/.gitignore`, `TEMPLATES/docs/references/README.md`, `TEMPLATES/docs/deviations/README.md`
- Create: `SCRIPTS/manifest.py`
- Test: `tests/scripts/test_manifest.py`

**Interfaces:**
- Consumes: nothing
- Produces:
  - `manifest.MANAGED`, `manifest.TEAM_OWNED`, `manifest.DIRS`, `manifest.EXECUTABLE` (tuples of repo-relative paths, forward slashes)
  - `manifest.GENERATED = (review_docs.INSTRUCTIONS_PATH,)`
  - `manifest.VERSION_PATH = "harness/.harness-version"`, `manifest.PROPOSED_SUFFIX = ".harness-proposed"`
  - `manifest.managed_files(templates) -> list[str]` (MANAGED plus every `harness/scripts/*.py` in the templates folder)
  - `manifest.read_version(templates) -> str`
  - `manifest.digest(data: bytes) -> str` (sha256 hex)

- [ ] **Step 1: Write the failing tests**

Create `tests/scripts/test_manifest.py`:

```python
import manifest
from helpers import TEMPLATES


def test_every_listed_template_exists():
    for path in list(manifest.MANAGED) + list(manifest.TEAM_OWNED):
        assert (TEMPLATES / path).is_file(), path


def test_managed_files_include_every_script():
    files = manifest.managed_files(TEMPLATES)
    assert "harness/scripts/check.py" in files and "harness/scripts/install.py" not in manifest.MANAGED
    assert files == sorted(set(files))
    assert all(not path.endswith(".pyc") for path in files)


def test_generated_files_are_not_also_managed_or_team_owned():
    listed = set(manifest.MANAGED) | set(manifest.TEAM_OWNED)
    assert not listed & set(manifest.GENERATED)


def test_read_version_and_digest():
    assert manifest.read_version(TEMPLATES).count(".") == 2
    assert manifest.digest(b"abc") == manifest.digest(b"abc") != manifest.digest(b"abd")


def test_executables_are_managed():
    assert set(manifest.EXECUTABLE) <= set(manifest.MANAGED)
```

- [ ] **Step 2: Run the test and watch it fail**

Run: `py -3 -m pytest tests/scripts/test_manifest.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'manifest'`.

- [ ] **Step 3: Create `TEMPLATES/VERSION`**

```
0.1.0
```

- [ ] **Step 4: Create `TEMPLATES/AGENTS.md`**

```markdown
# AGENTS.md

Entry point for everyone working in this repository, human or agent. Read this file first, then [CLAUDE.md](CLAUDE.md).

## Where to work

- Edit code in folders marked `owned` in `harness/architecture.json`.
- Folders marked `vendor` or `generated` are read-only. Their ARCHITECTURE.md says where the code comes from and how to upgrade it.
- Every folder holding C sources has an ARCHITECTURE.md. Read the one next to the code before changing that code.

## Guardrails

Ask a human before any of these:

- `git clean`, `git push`, `git commit --no-verify`, force pushes, and history rewrites
- editing linker scripts, startup files, or compiler flags
- editing approved rules in `harness/architecture.json`
- adding a line to `harness/cppcheck-suppressions.txt` or to the grandfather list, because both lists may only shrink
- moving a ticket to `done`

## The loop

1. Verify the environment: `sh init.sh`, or `.\init.ps1` in PowerShell. It checks and installs nothing.
2. Claim one ticket: `py -3 harness/scripts/ticket.py claim FW-NNNN`. One active ticket per person.
3. Write a failing test, implement, and run `py -3 harness/scripts/check.py` until every step passes.
4. Record evidence on a clean working tree: `py -3 harness/scripts/check.py --record FW-NNNN`.
5. Wrap up with the `fw-done` skill: handoff, progress note, and a commit message naming the ticket.

## Identity

Every state change records `git config user.name` and `user.email`, so set both before your first commit. No command takes someone else's identity.

## Windows notes

- Run Python as `py -3`. A bare `python` can be the Microsoft Store stub, which exits without running anything.
- Console code pages such as cp950 cannot print every character. The scripts force UTF-8 on their own output, and every file in the repository is UTF-8.
- The git hooks are POSIX shell scripts. Git for Windows ships the shell they need, so they run the same from PowerShell, cmd, and Git Bash.

The full handbook, including the Definition of Done, is [CLAUDE.md](CLAUDE.md).
```

- [ ] **Step 5: Create `TEMPLATES/CLAUDE.md`**

```markdown
# CLAUDE.md

The handbook for this repository. [AGENTS.md](AGENTS.md) is the short entry point; this file holds the rules and the reasons behind them.

## 1. Session start

1. Confirm where you are and who you are: the repository path, the branch, and `git config user.name` and `user.email`.
2. Run `sh init.sh` (PowerShell: `.\init.ps1`). It verifies Python, identity, hooks, the harness layout, and the toolchain, then runs `check` once.
3. Read your own handoff: `harness/handoff/<your-slug>.md`.
4. Read the last few progress notes in `harness/progress/` and the recent `git log`.
5. List candidate tickets: `py -3 harness/scripts/ticket.py show --status active --mine`, then the `next` queue.
6. Confirm the ticket with a human before writing code.

## 2. Working rules

- One `active` ticket per person. Claiming a second one fails.
- Run `check` on the merged tree before merging, not only on your own branch.
- A new C file goes into the CMake target as well as onto disk. A file that compiles only on your machine is not built.
- Leave compiler flags as they are. If a warning needs a flag change, raise it as a ticket.
- Fix the cause of a `cppcheck` finding. `harness/cppcheck-suppressions.txt` may only shrink.
- Run every command from the repository root, so relative paths in `harness/config.json` resolve.

## 3. Definition of Done

A ticket reaches `done` when all of these hold:

- `dod_pending` is empty.
- A `check` evidence entry passed on a commit that is HEAD or an ancestor of HEAD.
- When `requires_hil` is true, a `hil` evidence entry points at a captured log under `harness/evidence/`.
- The latest `review` evidence is by someone other than the assignee, with `open_critical` at zero.
- A human types the ticket ID in a terminal to confirm. `ticket.py move <id> done` needs a real terminal, which an agent shell usually does not have.

"Written" and "done" are different states. When the code is written and `check` passes but board verification or review is still owed, the ticket stays in `verifying` with the debt listed in `dod_pending`.

The limit of this design: `ticket_check` can prove that a `done` ticket carries HIL evidence and a review by another person, and it cannot prove a human produced that evidence. Pull request review is the final safeguard.

## 4. Why the gates look like this

| Gate | Why |
|---|---|
| `clang-format` on changed files only | Formatting the whole tree buries real changes in a reformatting diff. |
| `cppcheck` with a shrinking suppression list | A suppression is a debt. Recording it is fine; growing the list quietly is not. |
| `arch_check` | An include that crosses a layer is cheap to add and expensive to undo. The graph is checked on every run. |
| `ticket_check` | State files are edited by several people. The gate catches a ticket that says `done` without evidence. |
| Cross build with `-Wall -Wextra -Werror` | A warning on an embedded target is usually a real defect. |
| Host Unity tests | Logic that can run on the host should be tested without a board. |
| Size budget | Flash and RAM run out late and all at once. The budget turns that into a failing check. |
| Commit evidence derived from `git log` | Writing evidence into ticket files from a hook dirties the working tree and causes merge conflicts. |
| One file per ticket | Two people adding tickets in parallel get an add/add conflict git can show, instead of a silent overwrite. |

## 5. Incidents that became rules

Record what went wrong, so the rule keeps its reason.

| Date | What happened | The rule it produced |
|---|---|---|
| | | |
```

- [ ] **Step 6: Create the remaining templates**

`TEMPLATES/.github/copilot-instructions.md`:

```markdown
# Copilot instructions

Read [AGENTS.md](../AGENTS.md) first, then [CLAUDE.md](../CLAUDE.md). They hold the guardrails, the session loop, and the Definition of Done for this repository.

Review rules for C files live in [instructions/c-fw-review.instructions.md](instructions/c-fw-review.instructions.md), which is generated from `harness/review-checklist.json`.
```

`TEMPLATES/.clang-format`:

```yaml
# Formatting for C firmware sources. check runs clang-format --dry-run --Werror on changed files.
BasedOnStyle: LLVM
Language: Cpp
IndentWidth: 4
TabWidth: 4
UseTab: Never
ColumnLimit: 100
PointerAlignment: Right
AlignAfterOpenBracket: Align
AllowShortFunctionsOnASingleLine: None
AllowShortIfStatementsOnASingleLine: false
AllowShortLoopsOnASingleLine: false
BreakBeforeBraces: Attach
IndentCaseLabels: true
SortIncludes: false
SpaceAfterCStyleCast: true
```

`TEMPLATES/.gitignore`:

```gitignore
# Build output
build/
out/
Debug/
Release/

# Harness working files
.verify_logs/
feature_list.json
*.harness-proposed
__pycache__/
```

`TEMPLATES/docs/references/README.md`:

```markdown
# References

One file per external source an agent should read before touching the matching code: MCU reference manual notes, RTOS behaviour, SDK quirks, errata.

Name a file after its subject, for example `stm32f4-uart.llms.txt`. Keep each file to the facts that changed a decision in this repository, with a link to the original document.
```

`TEMPLATES/docs/deviations/README.md`:

```markdown
# MISRA deviations

One file per deviation, named `DEV-NNNN.md`, created by the `fw-misra-deviation` skill.

Each record holds the rule number, the reason the rule cannot be met here, the risk this creates, the scope the deviation covers, and the approver. The approver is someone other than the author.
```

- [ ] **Step 7: Write `SCRIPTS/manifest.py`**

```python
"""The files the harness owns, split into managed and team-owned (spec sections 3.1 and 4)."""
import hashlib
from pathlib import Path

from review_docs import INSTRUCTIONS_PATH

VERSION_PATH = "harness/.harness-version"
PROPOSED_SUFFIX = ".harness-proposed"

MANAGED = (
    ".githooks/_python.sh",
    ".githooks/commit-msg",
    ".githooks/post-commit",
    ".githooks/post-merge",
    ".github/copilot-instructions.md",
    "Makefile",
    "init.ps1",
    "init.sh",
)
TEAM_OWNED = (
    ".clang-format",
    ".gitignore",
    "AGENTS.md",
    "CLAUDE.md",
    "docs/deviations/README.md",
    "docs/references/README.md",
    "harness/architecture.json",
    "harness/config.json",
    "harness/cppcheck-suppressions.txt",
    "harness/review-checklist.json",
    "harness/review-policy.json",
)
GENERATED = (INSTRUCTIONS_PATH,)
DIRS = (
    "harness/tickets",
    "harness/progress",
    "harness/handoff",
    "harness/reviews",
    "harness/evidence",
)
EXECUTABLE = (
    ".githooks/commit-msg",
    ".githooks/post-commit",
    ".githooks/post-merge",
    "init.sh",
)


def managed_files(templates):
    scripts = sorted("harness/scripts/" + path.name
                     for path in (Path(templates) / "harness" / "scripts").glob("*.py"))
    return sorted(set(MANAGED) | set(scripts))


def read_version(templates):
    return (Path(templates) / "VERSION").read_text(encoding="utf-8").strip()


def digest(data):
    return hashlib.sha256(data).hexdigest()
```

- [ ] **Step 8: Run the tests and watch them pass**

Run: `py -3 -m pytest tests/scripts/test_manifest.py -q`
Expected: PASS. If `test_managed_files_include_every_script` fails on a `.pyc`, remove `__pycache__` from the templates folder: `py -3 -c "import shutil; shutil.rmtree(r'plugins/fw-c-harness/skills/fw-harness-init/templates/harness/scripts/__pycache__', ignore_errors=True)"`.

- [ ] **Step 9: Commit**

```bash
git add plugins/fw-c-harness/skills/fw-harness-init/templates tests/scripts/test_manifest.py
git commit -m "Add entry documents, default templates, and the harness file manifest"
```

---

### Task 8: `install.py`, the CLI behind `fw-harness-init`

**Files:**
- Create: `SCRIPTS/install.py`
- Test: `tests/scripts/test_install.py`

**Interfaces:**
- Consumes: `manifest.*`, `review_docs.load_checklist`, `review_docs.load_policy`, `review_docs.render_instructions`, `jsonio.read_json`, `jsonio.write_json_atomic`, `jsonio.write_text_atomic`, `gitutil.git`, `gitutil.repo_root`, `tickets.now_iso`
- Produces:
  - `install.DEFAULT_MARKETPLACE = "Yangchengyu0206/fw-harness"`, `install.MARKETPLACE_NAME = "fw-harness"`, `install.PLUGIN_NAME = "fw-c-harness"`
  - `install.InstallError(RuntimeError)`
  - `install.place(repo, source, path, report) -> None` (create, leave unchanged, or write a proposal)
  - `install.claude_settings(existing, marketplace) -> dict`, `install.copilot_settings(existing, marketplace) -> dict`
  - `install.version_record(repo, templates, version, marketplace, now) -> dict`
  - `install.install(repo, templates, marketplace=DEFAULT_MARKETPLACE, now=None) -> dict` with keys `created`, `merged` (settings files that already existed), `proposed`, `unchanged`, `version`
  - `install.main(argv=None, cwd=None, now=None) -> int`

- [ ] **Step 1: Write the failing tests**

Create `tests/scripts/test_install.py`:

```python
import json
import stat
import sys

import pytest

import install
import manifest
from helpers import TEMPLATES, commit_all, git, make_fixture_repo, make_repo


@pytest.fixture
def fresh(tmp_path):
    """A firmware repo with sources but no file the harness would install."""
    repo = make_fixture_repo(tmp_path / "fw")
    for path in (".gitignore", "harness/architecture.json", "harness/cppcheck-suppressions.txt"):
        (repo / path).unlink()
    commit_all(repo, "harness: clear installable files")
    return repo


def test_install_creates_every_manifest_file(fresh):
    report = install.install(fresh, TEMPLATES)
    for path in manifest.managed_files(TEMPLATES) + list(manifest.TEAM_OWNED) + list(manifest.GENERATED):
        assert (fresh / path).is_file(), path
    assert report["proposed"] == []
    assert report["version"] == manifest.read_version(TEMPLATES)


def test_install_creates_state_folders_with_gitkeep(fresh):
    install.install(fresh, TEMPLATES)
    for folder in manifest.DIRS:
        assert (fresh / folder / ".gitkeep").is_file()


def test_install_sets_the_hooks_path(fresh):
    install.install(fresh, TEMPLATES)
    assert git(fresh, "config", "core.hooksPath") == ".githooks"


def test_install_never_overwrites_and_proposes_instead(fresh):
    (fresh / "AGENTS.md").write_text("Our own entry point.\n", encoding="utf-8")
    report = install.install(fresh, TEMPLATES)
    assert (fresh / "AGENTS.md").read_text(encoding="utf-8") == "Our own entry point.\n"
    assert "AGENTS.md" in report["proposed"]
    assert (fresh / ("AGENTS.md" + manifest.PROPOSED_SUFFIX)).read_text(encoding="utf-8") == \
        (TEMPLATES / "AGENTS.md").read_text(encoding="utf-8")


def test_install_twice_changes_nothing(fresh):
    install.install(fresh, TEMPLATES)
    report = install.install(fresh, TEMPLATES)
    assert report["created"] == [] and report["proposed"] == []
    assert "AGENTS.md" in report["unchanged"]


def test_install_writes_the_version_record(fresh):
    install.install(fresh, TEMPLATES)
    record = json.loads((fresh / manifest.VERSION_PATH).read_text(encoding="utf-8"))
    assert record["version"] == manifest.read_version(TEMPLATES)
    assert record["marketplace"] == install.DEFAULT_MARKETPLACE
    assert record["managed"]["harness/scripts/check.py"] == manifest.digest(
        (fresh / "harness" / "scripts" / "check.py").read_bytes())
    assert record["team_owned"]["AGENTS.md"] == manifest.digest((TEMPLATES / "AGENTS.md").read_bytes())


def test_settings_merge_keeps_unrelated_keys():
    claude = install.claude_settings({"permissions": {"allow": ["Bash"]}}, "acme/fw-harness")
    assert claude["permissions"] == {"allow": ["Bash"]}
    assert claude["extraKnownMarketplaces"]["fw-harness"]["source"] == {"source": "github", "repo": "acme/fw-harness"}
    assert claude["enabledPlugins"]["fw-c-harness@fw-harness"] is True

    copilot = install.copilot_settings({"extraKnownMarketplaces": [{"name": "other", "source": "a/b"}]},
                                       "acme/fw-harness")
    names = [entry["name"] for entry in copilot["extraKnownMarketplaces"]]
    assert names == ["other", "fw-harness"]
    again = install.copilot_settings(copilot, "acme/fw-harness")
    assert len(again["extraKnownMarketplaces"]) == 2


def test_install_writes_both_settings_files(fresh):
    install.install(fresh, TEMPLATES)
    claude = json.loads((fresh / ".claude" / "settings.json").read_text(encoding="utf-8"))
    copilot = json.loads((fresh / ".github" / "copilot-settings.json").read_text(encoding="utf-8"))
    assert "fw-harness" in claude["extraKnownMarketplaces"]
    assert copilot["extraKnownMarketplaces"][0]["source"] == install.DEFAULT_MARKETPLACE


def test_install_renders_the_review_instructions_from_the_checklist(fresh):
    install.install(fresh, TEMPLATES)
    text = (fresh / manifest.GENERATED[0]).read_text(encoding="utf-8")
    assert 'applyTo: "**/*.{c,h}"' in text and "Critical (blocks merge)" in text


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX file modes")
def test_hooks_are_executable(fresh):
    install.install(fresh, TEMPLATES)
    for path in manifest.EXECUTABLE:
        assert (fresh / path).stat().st_mode & stat.S_IXUSR


def test_hooks_are_staged_with_the_executable_bit(fresh):
    install.install(fresh, TEMPLATES)
    listing = git(fresh, "ls-files", "--stage", ".githooks/commit-msg")
    assert listing.startswith("100755")


def test_main_reports_and_refuses_a_missing_templates_folder(tmp_path, capsys):
    repo = make_repo(tmp_path / "fw", "Alice Chen", "alice@example.com")
    assert install.main(["--templates", str(tmp_path / "nope")], cwd=repo) == 1
    assert "not found" in capsys.readouterr().err
    assert install.main(["--templates", str(TEMPLATES)], cwd=repo) == 0
    assert "created" in capsys.readouterr().out
```

- [ ] **Step 2: Run the tests and watch them fail**

Run: `py -3 -m pytest tests/scripts/test_install.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'install'`.

- [ ] **Step 3: Write `SCRIPTS/install.py`**

```python
"""fw-harness-init: write the harness into a firmware repository (spec sections 4 and 8)."""
import argparse
import json
import os
import sys
from pathlib import Path

import manifest
import review_docs
from console import use_utf8_stdio
from gitutil import git, repo_root
from jsonio import read_json, write_json_atomic, write_text_atomic
from tickets import now_iso

DEFAULT_MARKETPLACE = "Yangchengyu0206/fw-harness"
MARKETPLACE_NAME = "fw-harness"
PLUGIN_NAME = "fw-c-harness"
CLAUDE_SETTINGS = ".claude/settings.json"
COPILOT_SETTINGS = ".github/copilot-settings.json"


class InstallError(RuntimeError):
    pass


def place(repo, source, path, report):
    target = Path(repo) / path
    data = Path(source).read_bytes()
    if target.is_file():
        if target.read_bytes() == data:
            report["unchanged"].append(path)
        else:
            write_bytes(target.with_name(target.name + manifest.PROPOSED_SUFFIX), data)
            report["proposed"].append(path)
        return
    write_bytes(target, data)
    if path in manifest.EXECUTABLE:
        os.chmod(target, 0o755)
    report["created"].append(path)


def write_bytes(target, data):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)


def claude_settings(existing, marketplace):
    settings = dict(existing or {})
    known = dict(settings.get("extraKnownMarketplaces") or {})
    known[MARKETPLACE_NAME] = {"source": {"source": "github", "repo": marketplace}}
    settings["extraKnownMarketplaces"] = known
    enabled = dict(settings.get("enabledPlugins") or {})
    enabled[f"{PLUGIN_NAME}@{MARKETPLACE_NAME}"] = True
    settings["enabledPlugins"] = enabled
    return settings


def copilot_settings(existing, marketplace):
    settings = dict(existing or {})
    known = [entry for entry in (settings.get("extraKnownMarketplaces") or [])
             if not (isinstance(entry, dict) and entry.get("name") == MARKETPLACE_NAME)]
    known.append({"name": MARKETPLACE_NAME, "source": marketplace, "autoUpdate": True})
    settings["extraKnownMarketplaces"] = known
    return settings


def _merge_settings(repo, path, merge, marketplace, report):
    target = Path(repo) / path
    existed = target.is_file()
    existing = read_json(target) if existed else {}
    merged = merge(existing, marketplace)
    if existed and merged == existing:
        report["unchanged"].append(path)
        return
    write_json_atomic(target, merged)
    report["merged" if existed else "created"].append(path)


def version_record(repo, templates, version, marketplace, now):
    managed = {}
    for path in manifest.managed_files(templates) + list(manifest.GENERATED):
        target = Path(repo) / path
        if target.is_file():
            managed[path] = manifest.digest(target.read_bytes())
    team_owned = {path: manifest.digest((Path(templates) / path).read_bytes())
                  for path in manifest.TEAM_OWNED}
    return {"version": version, "installed_at": now, "marketplace": marketplace,
            "managed": managed, "team_owned": team_owned}


def install(repo, templates, marketplace=DEFAULT_MARKETPLACE, now=None):
    repo, templates = Path(repo), Path(templates)
    if not (templates / "VERSION").is_file():
        raise InstallError(f"templates folder {templates} not found or incomplete. "
                           "Fix: pass --templates <plugin>/skills/fw-harness-init/templates")
    report = {"created": [], "merged": [], "proposed": [], "unchanged": []}

    for path in manifest.managed_files(templates) + list(manifest.TEAM_OWNED):
        place(repo, templates / path, path, report)
    for folder in manifest.DIRS:
        keep = repo / folder / ".gitkeep"
        if not keep.is_file():
            write_bytes(keep, b"")
            report["created"].append(f"{folder}/.gitkeep")

    instructions = review_docs.render_instructions(review_docs.load_checklist(repo),
                                                   review_docs.load_policy(repo))
    generated = repo / manifest.GENERATED[0]
    if not generated.is_file() or generated.read_text(encoding="utf-8") != instructions:
        write_text_atomic(generated, instructions)
        report["created"].append(manifest.GENERATED[0])
    else:
        report["unchanged"].append(manifest.GENERATED[0])

    _merge_settings(repo, CLAUDE_SETTINGS, claude_settings, marketplace, report)
    _merge_settings(repo, COPILOT_SETTINGS, copilot_settings, marketplace, report)

    git(repo, "config", "core.hooksPath", ".githooks")
    for path in manifest.EXECUTABLE:
        if (repo / path).is_file():
            git(repo, "update-index", "--add", "--chmod=+x", path)

    version = manifest.read_version(templates)
    write_json_atomic(repo / manifest.VERSION_PATH,
                      version_record(repo, templates, version, marketplace, now or now_iso()))
    report["version"] = version
    return report


def default_templates():
    candidate = Path(__file__).resolve().parents[2]
    return candidate if (candidate / "VERSION").is_file() else None


def main(argv=None, cwd=None, now=None):
    use_utf8_stdio()
    parser = argparse.ArgumentParser(prog="install", description="Write the fw-c-harness into this repository")
    parser.add_argument("--templates", default=None, help="the plugin's templates folder")
    parser.add_argument("--marketplace", default=DEFAULT_MARKETPLACE, help="owner/repo of the plugin marketplace")
    args = parser.parse_args(argv)

    templates = Path(args.templates) if args.templates else default_templates()
    if templates is None:
        print("install failed: could not find the templates folder. "
              "Fix: pass --templates <plugin>/skills/fw-harness-init/templates", file=sys.stderr)
        return 1
    repo = repo_root(cwd or Path.cwd())
    try:
        report = install(repo, templates, marketplace=args.marketplace, now=now)
    except (InstallError, review_docs.ReviewDocsError, json.JSONDecodeError) as exc:
        print(f"install failed: {exc}", file=sys.stderr)
        return 1

    print(f"install: harness {report['version']} written to {repo}")
    for kind in ("created", "merged", "proposed", "unchanged"):
        names = report[kind]
        print(f"install: {kind} {len(names)} files" + (f": {', '.join(names[:5])}" if names[:5] else ""))
    for path in report["proposed"]:
        print(f"install: {path} already exists, so the new version is at {path}{manifest.PROPOSED_SUFFIX}. "
              "Fix: compare them and merge by hand")
    print("install: next run arch_sync scan, confirm the modules with a human, then arch_sync docs")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 4: Run the tests and watch them pass**

Run: `py -3 -m pytest tests/scripts/test_install.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/fw-c-harness/skills/fw-harness-init/templates/harness/scripts/install.py tests/scripts/test_install.py
git commit -m "Add install.py: place harness files, merge settings, record the version"
```

---

### Task 9: `upgrade.py`, the CLI behind `fw-harness-upgrade`

**Files:**
- Create: `SCRIPTS/upgrade.py`
- Test: `tests/scripts/test_upgrade.py`

**Interfaces:**
- Consumes: `manifest.*`, `install.write_bytes`, `install.version_record`, `install.DEFAULT_MARKETPLACE`, `review_docs.*`, `jsonio.*`
- Produces:
  - `upgrade.UpgradeError(RuntimeError)`
  - `upgrade.load_record(repo) -> dict`
  - `upgrade.plan(repo, templates, record) -> dict` with keys `created`, `updated`, `proposed`, `unchanged`, each a sorted list of repo-relative paths
  - `upgrade.upgrade(repo, templates, now=None, dry_run=False) -> dict` (the plan plus `from_version` and `to_version`)
  - `upgrade.main(argv=None, cwd=None, now=None) -> int` for `[--templates DIR] [--dry-run]`

- [ ] **Step 1: Write the failing tests**

Create `tests/scripts/test_upgrade.py`:

```python
import json
import shutil

import pytest

import install
import manifest
import upgrade
from helpers import TEMPLATES, commit_all, make_fixture_repo


@pytest.fixture
def installed(tmp_path):
    repo = make_fixture_repo(tmp_path / "fw")
    for path in (".gitignore", "harness/architecture.json", "harness/cppcheck-suppressions.txt"):
        (repo / path).unlink()
    commit_all(repo, "harness: clear installable files")
    install.install(repo, TEMPLATES)
    return repo


@pytest.fixture
def newer(tmp_path):
    """A copy of the shipped templates with a higher version and one changed file of each kind."""
    target = tmp_path / "templates-0.2.0"
    shutil.copytree(TEMPLATES, target, ignore=shutil.ignore_patterns("__pycache__"))
    (target / "VERSION").write_text("0.2.0\n", encoding="utf-8")
    makefile = target / "Makefile"
    makefile.write_text(makefile.read_text(encoding="utf-8") + "\n# new managed line\n", encoding="utf-8")
    agents = target / "AGENTS.md"
    agents.write_text(agents.read_text(encoding="utf-8") + "\nNew guardrail.\n", encoding="utf-8")
    return target


def test_upgrade_without_an_install_explains_the_fix(tmp_path):
    repo = make_fixture_repo(tmp_path / "bare")
    with pytest.raises(upgrade.UpgradeError, match="fw-harness-init"):
        upgrade.upgrade(repo, TEMPLATES)


def test_upgrade_updates_a_managed_file(installed, newer):
    report = upgrade.upgrade(installed, newer)
    assert report["from_version"] == "0.1.0" and report["to_version"] == "0.2.0"
    assert "Makefile" in report["updated"]
    assert "# new managed line" in (installed / "Makefile").read_text(encoding="utf-8")


def test_upgrade_proposes_a_team_owned_change(installed, newer):
    report = upgrade.upgrade(installed, newer)
    assert "AGENTS.md" in report["proposed"]
    assert "New guardrail." not in (installed / "AGENTS.md").read_text(encoding="utf-8")
    assert "New guardrail." in (installed / ("AGENTS.md" + manifest.PROPOSED_SUFFIX)).read_text(encoding="utf-8")


def test_upgrade_keeps_a_locally_edited_managed_file(installed, newer):
    makefile = installed / "Makefile"
    makefile.write_text(makefile.read_text(encoding="utf-8") + "\n# local tweak\n", encoding="utf-8")
    report = upgrade.upgrade(installed, newer)
    assert "Makefile" in report["proposed"] and "Makefile" not in report["updated"]
    assert "# local tweak" in makefile.read_text(encoding="utf-8")
    assert "# new managed line" in (installed / ("Makefile" + manifest.PROPOSED_SUFFIX)).read_text(encoding="utf-8")


def test_upgrade_recreates_a_deleted_managed_file(installed, newer):
    (installed / "harness" / "scripts" / "ratchet.py").unlink()
    report = upgrade.upgrade(installed, newer)
    assert "harness/scripts/ratchet.py" in report["created"]
    assert (installed / "harness" / "scripts" / "ratchet.py").is_file()


def test_upgrade_rewrites_the_version_record(installed, newer):
    upgrade.upgrade(installed, newer)
    record = json.loads((installed / manifest.VERSION_PATH).read_text(encoding="utf-8"))
    assert record["version"] == "0.2.0"
    assert record["managed"]["Makefile"] == manifest.digest((installed / "Makefile").read_bytes())
    assert record["team_owned"]["AGENTS.md"] == manifest.digest((newer / "AGENTS.md").read_bytes())


def test_upgrade_is_idempotent(installed, newer):
    upgrade.upgrade(installed, newer)
    report = upgrade.upgrade(installed, newer)
    assert report["updated"] == [] and report["created"] == []


def test_dry_run_writes_nothing(installed, newer):
    before = (installed / "Makefile").read_bytes()
    report = upgrade.upgrade(installed, newer, dry_run=True)
    assert "Makefile" in report["updated"]
    assert (installed / "Makefile").read_bytes() == before
    assert json.loads((installed / manifest.VERSION_PATH).read_text(encoding="utf-8"))["version"] == "0.1.0"


def test_main_reports_each_group(installed, newer, capsys):
    assert upgrade.main(["--templates", str(newer)], cwd=installed) == 0
    output = capsys.readouterr().out
    assert "0.1.0 to 0.2.0" in output and "AGENTS.md" in output
```

- [ ] **Step 2: Run the tests and watch them fail**

Run: `py -3 -m pytest tests/scripts/test_upgrade.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'upgrade'`.

- [ ] **Step 3: Write `SCRIPTS/upgrade.py`**

```python
"""fw-harness-upgrade: refresh managed harness files and propose team-owned changes (spec section 3.1)."""
import argparse
import json
import sys
from pathlib import Path

import install
import manifest
import review_docs
from console import use_utf8_stdio
from gitutil import repo_root
from jsonio import read_json, write_json_atomic, write_text_atomic
from tickets import now_iso


class UpgradeError(RuntimeError):
    pass


def load_record(repo):
    path = Path(repo) / manifest.VERSION_PATH
    if not path.is_file():
        raise UpgradeError(f"{manifest.VERSION_PATH} not found, so this repository has no harness yet. "
                           "Fix: run fw-harness-init first")
    try:
        record = read_json(path)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise UpgradeError(f"{manifest.VERSION_PATH} is not valid JSON ({exc}). "
                           "Fix: restore it from git") from exc
    if not isinstance(record.get("managed"), dict) or not isinstance(record.get("team_owned"), dict):
        raise UpgradeError(f"{manifest.VERSION_PATH} is missing the managed and team_owned tables. "
                           "Fix: restore it from git, or run fw-harness-init again")
    return record


def plan(repo, templates, record):
    repo, templates = Path(repo), Path(templates)
    report = {"created": [], "updated": [], "proposed": [], "unchanged": []}

    for path in manifest.managed_files(templates):
        source = (templates / path).read_bytes()
        target = repo / path
        if not target.is_file():
            report["created"].append((path, source))
        elif target.read_bytes() == source:
            report["unchanged"].append(path)
        elif record["managed"].get(path) == manifest.digest(target.read_bytes()):
            report["updated"].append((path, source))
        else:
            report["proposed"].append((path, source))

    for path in manifest.TEAM_OWNED:
        source = (templates / path).read_bytes()
        target = repo / path
        if not target.is_file():
            report["created"].append((path, source))
        elif record["team_owned"].get(path) == manifest.digest(source):
            report["unchanged"].append(path)
        elif target.read_bytes() == source:
            report["unchanged"].append(path)
        else:
            report["proposed"].append((path, source))
    return report


def upgrade(repo, templates, now=None, dry_run=False):
    repo, templates = Path(repo), Path(templates)
    if not (templates / "VERSION").is_file():
        raise UpgradeError(f"templates folder {templates} not found or incomplete. "
                           "Fix: pass --templates <plugin>/skills/fw-harness-init/templates")
    record = load_record(repo)
    work = plan(repo, templates, record)

    if not dry_run:
        for path, data in work["created"] + work["updated"]:
            install.write_bytes(repo / path, data)
            if path in manifest.EXECUTABLE:
                (repo / path).chmod(0o755)
        for path, data in work["proposed"]:
            install.write_bytes(repo / (path + manifest.PROPOSED_SUFFIX), data)

        instructions = review_docs.render_instructions(review_docs.load_checklist(repo),
                                                       review_docs.load_policy(repo))
        generated = repo / manifest.GENERATED[0]
        if not generated.is_file() or generated.read_text(encoding="utf-8") != instructions:
            write_text_atomic(generated, instructions)

    version = manifest.read_version(templates)
    result = {kind: sorted(path for path, _ in entries) if kind != "unchanged" else sorted(entries)
              for kind, entries in work.items()}
    result["from_version"] = record.get("version", "unknown")
    result["to_version"] = version
    if not dry_run:
        write_json_atomic(repo / manifest.VERSION_PATH,
                          install.version_record(repo, templates, version,
                                                 record.get("marketplace", install.DEFAULT_MARKETPLACE),
                                                 now or now_iso()))
    return result


def main(argv=None, cwd=None, now=None):
    use_utf8_stdio()
    parser = argparse.ArgumentParser(prog="upgrade", description="Update the harness in this repository")
    parser.add_argument("--templates", default=None, help="the plugin's templates folder")
    parser.add_argument("--dry-run", action="store_true", help="report the work without writing anything")
    args = parser.parse_args(argv)

    templates = Path(args.templates) if args.templates else install.default_templates()
    if templates is None:
        print("upgrade failed: could not find the templates folder. "
              "Fix: pass --templates <plugin>/skills/fw-harness-init/templates", file=sys.stderr)
        return 1
    repo = repo_root(cwd or Path.cwd())
    try:
        report = upgrade(repo, templates, now=now, dry_run=args.dry_run)
    except (UpgradeError, review_docs.ReviewDocsError) as exc:
        print(f"upgrade failed: {exc}", file=sys.stderr)
        return 1

    print(f"upgrade: {report['from_version']} to {report['to_version']}"
          + (" (dry run, nothing written)" if args.dry_run else ""))
    for kind in ("created", "updated", "proposed", "unchanged"):
        names = report[kind]
        print(f"upgrade: {kind} {len(names)} files" + (f": {', '.join(names[:5])}" if names[:5] else ""))
    for path in report["proposed"]:
        print(f"upgrade: {path} differs from the new template, so the new version is at "
              f"{path}{manifest.PROPOSED_SUFFIX}. Fix: review the difference item by item and merge what you want")
    if report["updated"] or report["created"]:
        print("upgrade: run check before committing, so a script change is verified here")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 4: Run the tests and watch them pass**

Run: `py -3 -m pytest tests/scripts/test_upgrade.py -q`
Expected: PASS.

- [ ] **Step 5: Run the whole suite**

Run: `py -3 -m pytest tests -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add plugins/fw-c-harness/skills/fw-harness-init/templates/harness/scripts/upgrade.py tests/scripts/test_upgrade.py
git commit -m "Add upgrade.py: update managed files and propose team-owned changes"
```

---

### Task 10: End-to-end generation on the sample firmware

**Files:**
- Create: `tests/scripts/test_end_to_end.py`

**Interfaces:**
- Consumes: `install.install`, `arch_sync.scan`, `arch_sync.docs`, `check.main`, `init_check.main`, `helpers.fake_config`, `helpers.write_config`
- Produces: nothing new; this task proves the pieces work together.

- [ ] **Step 1: Write the failing test**

Create `tests/scripts/test_end_to_end.py`:

```python
import json
import shutil

import pytest

import arch_sync
import check
import init_check
import install
from helpers import FIXTURES, TEMPLATES, commit_all, fake_config, git, make_repo, write_config


@pytest.fixture
def firmware(tmp_path):
    """A firmware repo holding sources only: no harness, no architecture, no documents."""
    repo = make_repo(tmp_path / "fw", "Alice Chen", "alice@example.com")
    for folder in ("src", "test", "third_party"):
        shutil.copytree(FIXTURES / "sample-fw" / folder, repo / folder)
    for doc in repo.rglob("ARCHITECTURE.md"):
        doc.unlink()
    commit_all(repo, "harness: add firmware sources")
    return repo


def test_generate_a_harness_and_pass_check(firmware, capsys):
    report = install.install(firmware, TEMPLATES)
    assert report["proposed"] == []

    write_config(firmware, fake_config())

    written, arch, scan_report = arch_sync.scan(firmware)
    assert written == "harness/architecture.json"
    assert sorted(arch["modules"]) == ["src/app", "src/drivers", "src/hal", "test", "third_party/cmsis"]
    assert scan_report["reverse"] == [("src/hal", "src/app")]

    documents = arch_sync.docs(firmware)
    assert "ARCHITECTURE.md" in documents
    assert (firmware / "src" / "hal" / "ARCHITECTURE.md").is_file()

    assert check.main([], cwd=firmware) == 0
    assert "check 7/7 passed" in capsys.readouterr().out


def test_generated_harness_passes_init_and_commits_cleanly(firmware, capsys):
    install.install(firmware, TEMPLATES)
    write_config(firmware, fake_config())
    arch_sync.scan(firmware)
    arch_sync.docs(firmware)

    assert init_check.main([], cwd=firmware) == 0
    assert git(firmware, "config", "core.hooksPath") == ".githooks"

    commit_all(firmware, "harness: add the generated harness")
    assert git(firmware, "status", "--porcelain") == ""

    record = json.loads((firmware / "harness" / ".harness-version").read_text(encoding="utf-8"))
    assert record["version"] == (TEMPLATES / "VERSION").read_text(encoding="utf-8").strip()


def test_a_new_folder_fails_arch_check_until_it_is_synced(firmware):
    install.install(firmware, TEMPLATES)
    write_config(firmware, fake_config())
    arch_sync.scan(firmware)
    arch_sync.docs(firmware)
    commit_all(firmware, "harness: add the generated harness")

    new = firmware / "src" / "sensors"
    new.mkdir()
    (new / "sensor.c").write_text('#include "uart.h"\n\nint sensor_init(void) { return 0; }\n', encoding="utf-8")
    assert check.main([], cwd=firmware) == 1

    arch_sync.scan(firmware, force=True)
    arch_sync.docs(firmware)
    assert check.main([], cwd=firmware) == 0
```

- [ ] **Step 2: Run the test and watch it fail**

Run: `py -3 -m pytest tests/scripts/test_end_to_end.py -q`
Expected: FAIL. The first failure is the point of the task: note which step breaks (most likely the `check` run, because `harness/config.json` from the template names real tools).

- [ ] **Step 3: Make the end-to-end path work**

Work through the failures in order. Expected fixes, each small:

- `write_config` commits, so call it before `arch_sync.scan`, which reads the config. The test already does this.
- `check.main` runs `ticket_check` over `harness/tickets/`, which holds only `.gitkeep`. That passes with zero tickets.
- `arch_check` compares the grandfather list against the baseline. `harness/architecture.json` is uncommitted at this point, so `ratchet.baseline_text` returns `None` and nothing counts as new. In `test_a_new_folder_fails_arch_check_until_it_is_synced`, the list is committed and unchanged by the rescan, so it still passes.
- The size step reads `fake_config`, which prints a fixed Berkeley table, so no toolchain is needed.

Change only the scripts, never the test's expectations. If a script needs a fix, add the matching unit test to that script's own test module in the same commit.

- [ ] **Step 4: Run the test and watch it pass**

Run: `py -3 -m pytest tests/scripts/test_end_to_end.py -q`
Expected: PASS.

- [ ] **Step 5: Run the whole suite**

Run: `py -3 -m pytest tests -q`
Expected: PASS, with the same two skips as before (`make` and `sh` when they are not on PATH).

- [ ] **Step 6: Commit**

```bash
git add tests/scripts/test_end_to_end.py plugins/fw-c-harness/skills/fw-harness-init/templates/harness/scripts
git commit -m "Add the end-to-end test: install, scan, document, and pass check"
```

---

## Manual verification after Task 10

Run once by hand from `C:\Users\YANG\Desktop\fw-harness`, because no automated test covers the CLI wrappers on a real tree:

```bash
py -3 -c "import shutil, pathlib; d=pathlib.Path(r'C:\Users\YANG\AppData\Local\Temp\fw-demo'); shutil.rmtree(d, ignore_errors=True); shutil.copytree('tests/fixtures/sample-fw', d)"
cd C:\Users\YANG\AppData\Local\Temp\fw-demo
git init -b main && git add -A && git commit -m "harness: sources"
py -3 C:\Users\YANG\Desktop\fw-harness\plugins\fw-c-harness\skills\fw-harness-init\templates\harness\scripts\install.py --templates C:\Users\YANG\Desktop\fw-harness\plugins\fw-c-harness\skills\fw-harness-init\templates
py -3 harness/scripts/arch_sync.py scan --force
py -3 harness/scripts/arch_sync.py docs
```

Expected: `install` reports created files and no proposals for a fresh repo, `arch_sync scan` reports five modules and one grandfathered reverse dependency, `arch_sync docs` writes six documents, and every written file is UTF-8 with LF endings. `check` needs the real toolchain, so it is not part of this manual pass.

## Out of scope for this plan

- SKILL.md files, both marketplace manifests, and the README (plan 4).
- A slug clash between two people whose email local parts match.
- Running `check` against a real GCC and CMake toolchain, which the development machine does not have.
