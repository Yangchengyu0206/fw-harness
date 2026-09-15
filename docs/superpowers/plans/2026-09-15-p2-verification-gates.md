# Plan 2: Verification Gates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the verification layer of the harness: `harness/config.json`, the seven `check` steps (format, cppcheck, arch, tickets, build, test, size) with ratchets, `check.py` with `--record`, the `init` environment check, git hooks, and the `Makefile` / `init.sh` / `init.ps1` wrappers.

**Architecture:** Plain Python standard-library modules next to plan 1's scripts. `steps.py` holds one function per gate, each returning a `StepResult`; `check.py` runs them in order and stops at the first failure. Every external tool is an argv array in `harness/config.json`, which lets tests substitute tiny `python -c` commands for `clang-format`, `cppcheck`, `cmake`, and `arm-none-eabi-size`. A small sample firmware tree in `tests/fixtures/sample-fw/` gives `arch_check` real includes to analyse. Git hooks are POSIX sh wrappers around Python scripts, so they behave the same for people, Copilot, and Claude.

**Tech Stack:** Python 3.9+ standard library, git CLI, POSIX sh (Git for Windows ships one), Windows PowerShell 5.1+, GNU make (optional), pytest (plugin development only).

**Spec:** `docs/superpowers/specs/2026-09-15-fw-c-harness-plugin-design.md`, sections 4.2, 4.3, 6.2, 6.3, 8, 9.

**Split (this plan is 2 of 4):**
1. Identity, tickets, and state scripts (done)
2. Verification gates (this plan)
3. `fw-harness-init` / `fw-harness-upgrade` / `fw-architecture-sync`: templates, ARCHITECTURE.md generation and its marked blocks, existing-file handling, end-to-end test with a real toolchain
4. Remaining skills, both marketplace manifests, README, manual checklist

## Global Constraints

- English only in code, comments, messages, and test data. No Chinese characters anywhere outside `docs/`.
- Python standard library only; Python 3.9 or newer. On Windows, run with `py -3`.
- All reads and writes use UTF-8; CLIs call `console.use_utf8_stdio()` first.
- Every failure message names the check, the file, and the fix (`... Fix: ...`).
- Scripts are flat modules in `SCRIPTS` and import each other by module name, like plan 1.
- The ratchet baseline is `origin/main`; without it, compare against HEAD and warn. A list absent at the baseline counts as newly introduced, so nothing in it is new.
- `check.py` is the only implementation of the gates. Wrappers pass no flags of their own.
- Commit messages in English.

## File Structure

`SCRIPTS` = `plugins/fw-c-harness/skills/fw-harness-init/templates/harness/scripts`
`TEMPLATES` = `plugins/fw-c-harness/skills/fw-harness-init/templates`

| File | Responsibility |
|---|---|
| `SCRIPTS/harness_config.py` | Load and validate `harness/config.json` |
| `SCRIPTS/ratchet.py` | Baseline ref, baseline file text, "may only shrink" comparison |
| `SCRIPTS/arch_check.py` | `architecture.json` schema, include dependency graph, `arch_check` gate and CLI |
| `SCRIPTS/size_check.py` | Parse Berkeley `size` output, evaluate budgets |
| `SCRIPTS/steps.py` | `StepResult`, command runner, changed files, the seven step functions, `STEPS` |
| `SCRIPTS/check.py` | Run `STEPS` in order, log to `.verify_logs/`, `--record` |
| `SCRIPTS/commit_msg_check.py` | Commit message rule used by the `commit-msg` hook |
| `SCRIPTS/init_check.py` | Session-start environment verification, then `check` |
| `TEMPLATES/harness/config.json` | Default gate configuration |
| `TEMPLATES/harness/architecture.json` | Empty architecture (filled in by plan 3) |
| `TEMPLATES/harness/cppcheck-suppressions.txt` | Empty suppression list with header |
| `TEMPLATES/.githooks/_python.sh`, `commit-msg`, `post-commit`, `post-merge` | Git hooks |
| `TEMPLATES/Makefile`, `TEMPLATES/init.sh`, `TEMPLATES/init.ps1` | Thin wrappers |
| `tests/fixtures/sample-fw/**` | Sample firmware tree with a deliberate reverse dependency |
| `tests/helpers.py` | Add `TEMPLATES`, `SCRIPTS`, `FIXTURES`, `PY`, `add_origin`, `make_fixture_repo`, `fake_config`, `write_config` |
| `tests/scripts/test_*.py` | One test module per script, plus hooks and wrappers |

All commands run from `C:\Users\YANG\Desktop\fw-harness`.

---

### Task 1: `harness_config` and the default config template

**Files:**
- Modify: `tests/helpers.py`
- Create: `TEMPLATES/harness/config.json`
- Create: `SCRIPTS/harness_config.py`
- Test: `tests/scripts/test_harness_config.py`

**Interfaces:**
- Consumes: `jsonio.read_json`
- Produces:
  - `harness_config.CONFIG_PATH = "harness/config.json"`, `LANGUAGES = ("en", "zh-TW")`
  - `harness_config.ConfigError(ValueError)`
  - `harness_config.validate_config(config) -> list[str]` (each error names the key, for example `check.size.flash_budget`)
  - `harness_config.load_config(repo) -> dict` (raises `ConfigError` when missing, not JSON, or invalid)
  - Config shape: `language`; `required_tools` (array of command names); `check.format` `{command, extensions}`; `check.cppcheck` `{command, paths}`; `check.build` / `check.test` `{commands}`; `check.size` `{command, flash_budget, ram_budget}`. Every command is an argv array; `{python}` expands to the running interpreter.
  - `helpers.TEMPLATES`, `helpers.SCRIPTS`, `helpers.FIXTURES`, `helpers.PY = "{python}"`, `helpers.fake_config(**check_overrides) -> dict`, `helpers.write_config(repo, config)` (writes and commits), `helpers.add_origin(repo, tmp_path) -> Path`, `helpers.make_fixture_repo(path, name="Alice Chen", email="alice@example.com") -> Path` (the fixture is created in Task 3; the helper is added now)

- [ ] **Step 1: Extend `tests/helpers.py`**

Replace the import block at the top with:

```python
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "plugins" / "fw-c-harness" / "skills" / "fw-harness-init" / "templates"
SCRIPTS = TEMPLATES / "harness" / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
PY = "{python}"
```

Append to the end of the file:

```python
def add_origin(repo, tmp_path):
    origin = Path(tmp_path) / "origin.git"
    git(tmp_path, "clone", "--bare", str(repo), str(origin))
    git(repo, "remote", "add", "origin", str(origin))
    git(repo, "fetch", "origin")
    return origin


def make_fixture_repo(path, name="Alice Chen", email="alice@example.com"):
    repo = make_repo(path, name, email)
    shutil.copytree(FIXTURES / "sample-fw", repo, dirs_exist_ok=True)
    commit_all(repo, "harness: add sample firmware")
    return repo


def fake_config(**check_overrides):
    ok = [PY, "-c", "pass"]
    size = [PY, "-c", "print('   text    data     bss     dec     hex filename'); "
                      "print('   1000     100     200    1300     514 fw.elf')"]
    check = {
        "format": {"command": ok, "extensions": [".c", ".h"]},
        "cppcheck": {"command": ok, "paths": ["src"]},
        "build": {"commands": [ok]},
        "test": {"commands": [ok]},
        "size": {"command": size, "flash_budget": 4096, "ram_budget": 1024},
    }
    check.update(check_overrides)
    return {"language": "en", "required_tools": [], "check": check}


def write_config(repo, config):
    path = Path(repo) / "harness" / "config.json"
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    commit_all(repo, "harness: config")
```

- [ ] **Step 2: Create the default config template**

`TEMPLATES/harness/config.json`:

```json
{
  "language": "en",
  "required_tools": ["arm-none-eabi-gcc", "arm-none-eabi-size", "gcc", "cmake", "ctest", "cppcheck", "clang-format"],
  "check": {
    "format": {
      "command": ["clang-format", "--dry-run", "--Werror"],
      "extensions": [".c", ".h"]
    },
    "cppcheck": {
      "command": ["cppcheck", "--enable=warning,style,performance,portability", "--error-exitcode=1", "--inline-suppr", "--quiet"],
      "paths": ["src"]
    },
    "build": {
      "commands": [["cmake", "--preset", "target"], ["cmake", "--build", "--preset", "target"]]
    },
    "test": {
      "commands": [["cmake", "--preset", "host-test"], ["cmake", "--build", "--preset", "host-test"], ["ctest", "--preset", "host-test"]]
    },
    "size": {
      "command": ["arm-none-eabi-size", "build/target/firmware.elf"],
      "flash_budget": 262144,
      "ram_budget": 32768
    }
  }
}
```

- [ ] **Step 3: Write the failing test**

`tests/scripts/test_harness_config.py`:

```python
import json

import pytest

from harness_config import ConfigError, load_config, validate_config
from helpers import TEMPLATES, fake_config


def test_template_config_is_valid():
    config = json.loads((TEMPLATES / "harness" / "config.json").read_text(encoding="utf-8"))
    assert validate_config(config) == []


def test_fake_config_is_valid():
    assert validate_config(fake_config()) == []


@pytest.mark.parametrize("mutate, fragment", [
    (lambda c: c.update(language="fr"), "language"),
    (lambda c: c.update(required_tools="cmake"), "required_tools"),
    (lambda c: c["check"].pop("build"), "check.build"),
    (lambda c: c["check"]["format"].update(command=[]), "check.format.command"),
    (lambda c: c["check"]["format"].update(extensions=["c"]), "check.format.extensions"),
    (lambda c: c["check"]["cppcheck"].update(paths=[]), "check.cppcheck.paths"),
    (lambda c: c["check"]["test"].update(commands=[["ctest"], []]), "check.test.commands"),
    (lambda c: c["check"]["size"].update(flash_budget=0), "check.size.flash_budget"),
])
def test_invalid_configs(mutate, fragment):
    config = fake_config()
    mutate(config)
    errors = validate_config(config)
    assert any(fragment in e for e in errors), errors


def test_load_config_missing(repo):
    with pytest.raises(ConfigError, match="fw-harness-init"):
        load_config(repo)


def test_load_config_lists_every_problem(repo):
    config = fake_config()
    config["language"] = "fr"
    config["check"]["size"]["ram_budget"] = -1
    (repo / "harness" / "config.json").write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(ConfigError) as exc:
        load_config(repo)
    assert "language" in str(exc.value) and "ram_budget" in str(exc.value)


def test_load_config_broken_json(repo):
    (repo / "harness" / "config.json").write_text("{", encoding="utf-8")
    with pytest.raises(ConfigError, match="not valid JSON"):
        load_config(repo)
```

- [ ] **Step 4: Run it and watch it fail**

Run: `py -3 -m pytest tests/scripts/test_harness_config.py`
Expected: FAIL, `ModuleNotFoundError: No module named 'harness_config'`

- [ ] **Step 5: Implement `harness_config.py`**

`SCRIPTS/harness_config.py`:

```python
"""Load and validate harness/config.json (spec section 4.2)."""
import json
from pathlib import Path

from jsonio import read_json

CONFIG_PATH = "harness/config.json"
LANGUAGES = ("en", "zh-TW")


class ConfigError(ValueError):
    pass


def _is_argv(value):
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item for item in value)


def _is_str_list(value, allow_empty=False):
    return (isinstance(value, list) and (allow_empty or bool(value))
            and all(isinstance(item, str) and item for item in value))


def _is_positive(value):
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def validate_config(config):
    if not isinstance(config, dict):
        return ["config must be a JSON object"]
    errors = []
    if config.get("language") not in LANGUAGES:
        errors.append(f"language must be one of {', '.join(LANGUAGES)}")
    if not _is_str_list(config.get("required_tools"), allow_empty=True):
        errors.append("required_tools must be an array of command names")
    check = config.get("check")
    if not isinstance(check, dict):
        return errors + ["check must be an object with format, cppcheck, build, test, and size"]
    for name in ("format", "cppcheck", "build", "test", "size"):
        if not isinstance(check.get(name), dict):
            errors.append(f"check.{name} must be an object")

    fmt = check.get("format")
    if isinstance(fmt, dict):
        if not _is_argv(fmt.get("command")):
            errors.append("check.format.command must be a non-empty argv array")
        extensions = fmt.get("extensions")
        if not (_is_str_list(extensions) and all(ext.startswith(".") for ext in extensions)):
            errors.append('check.format.extensions must be an array like [".c", ".h"]')

    cppcheck = check.get("cppcheck")
    if isinstance(cppcheck, dict):
        if not _is_argv(cppcheck.get("command")):
            errors.append("check.cppcheck.command must be a non-empty argv array")
        if not _is_str_list(cppcheck.get("paths")):
            errors.append("check.cppcheck.paths must be a non-empty array of paths")

    for name in ("build", "test"):
        step = check.get(name)
        if isinstance(step, dict):
            commands = step.get("commands")
            if not (isinstance(commands, list) and commands and all(_is_argv(c) for c in commands)):
                errors.append(f"check.{name}.commands must be a non-empty array of argv arrays")

    size = check.get("size")
    if isinstance(size, dict):
        if not _is_argv(size.get("command")):
            errors.append("check.size.command must be a non-empty argv array")
        for key in ("flash_budget", "ram_budget"):
            if not _is_positive(size.get(key)):
                errors.append(f"check.size.{key} must be a positive integer (bytes)")
    return errors


def load_config(repo):
    path = Path(repo) / CONFIG_PATH
    if not path.is_file():
        raise ConfigError(f"{CONFIG_PATH} not found. Fix: run fw-harness-init to create it")
    try:
        config = read_json(path)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ConfigError(f"{CONFIG_PATH} is not valid JSON ({exc}). Fix: repair it or restore it from git") from exc
    errors = validate_config(config)
    if errors:
        raise ConfigError(f"{CONFIG_PATH} is invalid:\n- " + "\n- ".join(errors))
    return config
```

- [ ] **Step 6: Run it and watch it pass**

Run: `py -3 -m pytest tests/scripts/test_harness_config.py`
Expected: `13 passed`

- [ ] **Step 7: Commit**

```bash
git add tests plugins
git commit -m "Add harness config loading, validation, and default template"
```

---

### Task 2: `ratchet`

**Files:**
- Create: `SCRIPTS/ratchet.py`
- Test: `tests/scripts/test_ratchet.py`

**Interfaces:**
- Consumes: `gitutil.git`, `gitutil.git_ok`; `helpers.add_origin`, `helpers.commit_all`
- Produces:
  - `ratchet.BASE_REF = "origin/main"`
  - `ratchet.parse_entries(text) -> set[str]` (non-blank lines that do not start with `#`, stripped)
  - `ratchet.baseline_ref(repo) -> tuple[str, str | None]` (`("origin/main", None)`, or `("HEAD", warning)`)
  - `ratchet.baseline_text(repo, ref, path) -> str | None` (`None` when the file does not exist at `ref`)
  - `ratchet.new_entries(current, baseline) -> list[str]` (sorted; `[]` when `baseline is None`)

- [ ] **Step 1: Write the failing test**

`tests/scripts/test_ratchet.py`:

```python
from helpers import add_origin, commit_all
from ratchet import BASE_REF, baseline_ref, baseline_text, new_entries, parse_entries


def test_parse_entries_skips_blank_lines_and_comments():
    text = "# header\n\nuninitvar:src/a.c\n  nullPointer:src/b.c  \n"
    assert parse_entries(text) == {"uninitvar:src/a.c", "nullPointer:src/b.c"}


def test_new_entries():
    assert new_entries({"a", "b"}, {"a"}) == ["b"]
    assert new_entries({"a"}, {"a", "b"}) == []
    assert new_entries({"a"}, None) == []


def test_baseline_falls_back_to_head_with_warning(repo):
    ref, warning = baseline_ref(repo)
    assert ref == "HEAD" and f"{BASE_REF} not found" in warning


def test_baseline_uses_origin_main(repo, tmp_path):
    add_origin(repo, tmp_path)
    assert baseline_ref(repo) == (BASE_REF, None)


def test_baseline_text(repo):
    (repo / "harness" / "list.txt").write_text("a\n", encoding="utf-8")
    commit_all(repo, "harness: list")
    assert baseline_text(repo, "HEAD", "harness/list.txt") == "a"
    assert baseline_text(repo, "HEAD", "harness/missing.txt") is None
```

- [ ] **Step 2: Run it and watch it fail**

Run: `py -3 -m pytest tests/scripts/test_ratchet.py`
Expected: FAIL, `ModuleNotFoundError: No module named 'ratchet'`

- [ ] **Step 3: Implement `ratchet.py`**

`SCRIPTS/ratchet.py`:

```python
"""Ratchet lists may only shrink. Entries are compared with the same file at a baseline ref (spec section 4.2)."""
from gitutil import git, git_ok

BASE_REF = "origin/main"


def parse_entries(text):
    entries = set()
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            entries.add(line)
    return entries


def baseline_ref(repo):
    if git_ok(repo, "rev-parse", "--verify", "--quiet", f"{BASE_REF}^{{commit}}"):
        return BASE_REF, None
    return "HEAD", (
        f"Warning: {BASE_REF} not found, so ratchets compare against HEAD and only catch uncommitted additions. "
        "Fix: add the origin remote and fetch main"
    )


def baseline_text(repo, ref, path):
    if not git_ok(repo, "cat-file", "-e", f"{ref}:{path}"):
        return None
    return git(repo, "show", f"{ref}:{path}")


def new_entries(current, baseline):
    """Entries in current that the baseline lacks. A list absent at the baseline is being introduced, so nothing is new."""
    if baseline is None:
        return []
    return sorted(set(current) - set(baseline))
```

- [ ] **Step 4: Run it and watch it pass**

Run: `py -3 -m pytest tests/scripts/test_ratchet.py`
Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add tests plugins
git commit -m "Add ratchet baseline helpers"
```

---

### Task 3: Sample firmware fixture and `arch_check`

**Files:**
- Create: `tests/fixtures/sample-fw/.gitignore`
- Create: `tests/fixtures/sample-fw/harness/architecture.json`
- Create: `tests/fixtures/sample-fw/harness/cppcheck-suppressions.txt`
- Create: `tests/fixtures/sample-fw/src/app/main.c`, `src/app/app_config.h`, `src/app/ARCHITECTURE.md`
- Create: `tests/fixtures/sample-fw/src/drivers/uart.c`, `src/drivers/uart.h`, `src/drivers/ARCHITECTURE.md`
- Create: `tests/fixtures/sample-fw/src/hal/hal_gpio.c`, `src/hal/hal_gpio.h`, `src/hal/ARCHITECTURE.md`
- Create: `tests/fixtures/sample-fw/third_party/cmsis/Include/core_cm4.h`, `third_party/cmsis/ARCHITECTURE.md`
- Create: `tests/fixtures/sample-fw/test/test_uart.c`, `test/ARCHITECTURE.md`
- Create: `TEMPLATES/harness/architecture.json`
- Create: `TEMPLATES/harness/cppcheck-suppressions.txt`
- Create: `SCRIPTS/arch_check.py`
- Test: `tests/scripts/test_arch_check.py`

**Interfaces:**
- Consumes: `gitutil.git`, `gitutil.repo_root`; `jsonio.read_json`; `console.use_utf8_stdio`; `ratchet.baseline_ref`, `baseline_text`, `new_entries`
- Produces:
  - `arch_check.ARCH_PATH = "harness/architecture.json"`, `KINDS = ("owned", "vendor", "generated", "test")`, `READ_ONLY_KINDS = ("vendor", "generated")`
  - `arch_check.ArchitectureError(ValueError)`
  - `arch_check.validate_architecture(arch) -> list[str]`
  - `arch_check.load_architecture(repo) -> dict`
  - `arch_check.module_of(path, modules) -> str | None` (longest matching module folder)
  - `arch_check.read_only_prefixes(arch) -> list[str]`
  - `arch_check.source_files(repo) -> list[str]` (tracked and untracked, not ignored, `.c`/`.h`, posix paths)
  - `arch_check.dependencies(repo, arch, files) -> dict[tuple[str, str], list[str]]` (`(from_module, to_module)` to `["path:line", ...]`, owned sources only)
  - `arch_check.check_architecture(repo) -> tuple[list[str], list[str]]` (errors, warnings; raises `ArchitectureError` for a missing or invalid file)
  - `arch_check.main(argv=None) -> int`
  - The fixture's only unapproved dependency is `src/hal -> src/app` at `src/hal/hal_gpio.c:2`, and it is grandfathered.

- [ ] **Step 1: Create the fixture**

`tests/fixtures/sample-fw/.gitignore`:

```gitignore
build/
.verify_logs/
feature_list.json
__pycache__/
```

`tests/fixtures/sample-fw/harness/architecture.json`:

```json
{
  "version": 1,
  "include_dirs": ["src/app", "src/drivers", "src/hal", "third_party/cmsis/Include"],
  "modules": {
    "src/app": {"kind": "owned", "allowed_deps": ["src/drivers"]},
    "src/drivers": {"kind": "owned", "allowed_deps": ["src/hal"]},
    "src/hal": {"kind": "owned", "allowed_deps": ["third_party/cmsis"]},
    "third_party/cmsis": {"kind": "vendor", "allowed_deps": []},
    "test": {"kind": "test", "allowed_deps": []}
  },
  "grandfathered": ["src/hal -> src/app"]
}
```

`tests/fixtures/sample-fw/harness/cppcheck-suppressions.txt`:

```text
# cppcheck suppressions, one per line (id:path). This list may only shrink.
```

`tests/fixtures/sample-fw/src/app/main.c`:

```c
#include <stdint.h>
#include "uart.h"
#include "app_config.h"

int main(void)
{
    (void)uart_init();
    for (;;) {
    }
}
```

`tests/fixtures/sample-fw/src/app/app_config.h`:

```c
#ifndef APP_CONFIG_H
#define APP_CONFIG_H

#define APP_GPIO_COUNT 4

#endif
```

`tests/fixtures/sample-fw/src/drivers/uart.h`:

```c
#ifndef UART_H
#define UART_H

int uart_init(void);

#endif
```

`tests/fixtures/sample-fw/src/drivers/uart.c`:

```c
#include "uart.h"
#include "hal_gpio.h"

int uart_init(void)
{
    return hal_gpio_init();
}
```

`tests/fixtures/sample-fw/src/hal/hal_gpio.h`:

```c
#ifndef HAL_GPIO_H
#define HAL_GPIO_H

#include <core_cm4.h>

int hal_gpio_init(void);

#endif
```

`tests/fixtures/sample-fw/src/hal/hal_gpio.c` (line 2 is the deliberate reverse dependency):

```c
#include "hal_gpio.h"
#include "../app/app_config.h"

int hal_gpio_init(void)
{
    return APP_GPIO_COUNT;
}
```

`tests/fixtures/sample-fw/third_party/cmsis/Include/core_cm4.h`:

```c
/* Stand-in for a vendor CMSIS header. Vendor code is read-only. */
#ifndef CORE_CM4_H
#define CORE_CM4_H

#include "cmsis_compiler.h"

#endif
```

`tests/fixtures/sample-fw/test/test_uart.c`:

```c
#include "unity.h"
#include "uart.h"
#include "../src/app/app_config.h"

void test_uart_init_returns_gpio_count(void)
{
    TEST_ASSERT_EQUAL_INT(APP_GPIO_COUNT, uart_init());
}
```

Each `ARCHITECTURE.md` is a one-paragraph placeholder:

`src/app/ARCHITECTURE.md`:

```markdown
# src/app

Application entry point for the sample firmware used by the fw-harness tests.
```

`src/drivers/ARCHITECTURE.md`:

```markdown
# src/drivers

Peripheral drivers for the sample firmware used by the fw-harness tests.
```

`src/hal/ARCHITECTURE.md`:

```markdown
# src/hal

Hardware abstraction for the sample firmware. `hal_gpio.c` includes an app header on purpose: it is the grandfathered reverse dependency the tests rely on.
```

`third_party/cmsis/ARCHITECTURE.md`:

```markdown
# third_party/cmsis

Vendor code, read-only. Stand-in for CMSIS in the fw-harness tests.
```

`test/ARCHITECTURE.md`:

```markdown
# test

Host unit tests (Unity) for the sample firmware used by the fw-harness tests.
```

- [ ] **Step 2: Create the templates**

`TEMPLATES/harness/architecture.json`:

```json
{
  "version": 1,
  "include_dirs": [],
  "modules": {},
  "grandfathered": []
}
```

`TEMPLATES/harness/cppcheck-suppressions.txt`:

```text
# cppcheck suppressions, one per line (id:path). This list may only shrink.
```

- [ ] **Step 3: Write the failing test**

`tests/scripts/test_arch_check.py`:

```python
import json

import pytest

from arch_check import (
    ArchitectureError, check_architecture, dependencies, load_architecture, main, module_of,
    source_files, validate_architecture,
)
from helpers import TEMPLATES, add_origin, commit_all, make_fixture_repo


def edit_arch(repo, mutate):
    path = repo / "harness" / "architecture.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    mutate(data)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


@pytest.fixture
def fw(tmp_path):
    return make_fixture_repo(tmp_path / "fw")


def test_template_architecture_is_valid():
    data = json.loads((TEMPLATES / "harness" / "architecture.json").read_text(encoding="utf-8"))
    assert validate_architecture(data) == []


@pytest.mark.parametrize("mutate, fragment", [
    (lambda a: a.update(version=2), "version"),
    (lambda a: a["modules"]["src/app"].update(kind="library"), "kind"),
    (lambda a: a["modules"]["src/app"].update(allowed_deps=["src/nowhere"]), "src/nowhere"),
    (lambda a: a["modules"].update({"src/app/": {"kind": "owned", "allowed_deps": []}}), "src/app/"),
    (lambda a: a.update(grandfathered=["src/hal to src/app"]), "grandfathered"),
    (lambda a: a.update(include_dirs="src"), "include_dirs"),
])
def test_invalid_architecture(fw, mutate, fragment):
    data = load_architecture(fw)
    mutate(data)
    assert any(fragment in e for e in validate_architecture(data))


def test_module_of_uses_longest_prefix():
    modules = {"src": {}, "src/drivers": {}}
    assert module_of("src/drivers/uart.c", modules) == "src/drivers"
    assert module_of("src/main.c", modules) == "src"
    assert module_of("srcx/main.c", modules) is None


def test_dependencies_resolve_relative_and_include_dir_paths(fw):
    deps = dependencies(fw, load_architecture(fw), source_files(fw))
    assert deps[("src/hal", "src/app")] == ["src/hal/hal_gpio.c:2"]
    assert ("src/app", "src/drivers") in deps
    assert ("src/hal", "third_party/cmsis") in deps
    assert not any(source == "test" for source, _ in deps)


def test_sample_firmware_passes_with_grandfathered_reverse_dependency(fw):
    errors, warnings = check_architecture(fw)
    assert errors == []
    assert any("origin/main not found" in w for w in warnings)


def test_unapproved_dependency_fails_with_location(fw):
    edit_arch(fw, lambda a: a.update(grandfathered=[]))
    errors, _ = check_architecture(fw)
    assert len(errors) == 1
    assert errors[0].startswith("src/hal -> src/app: dependency not approved (src/hal/hal_gpio.c:2)")


def test_new_grandfather_entry_fails_ratchet_and_stale_entry_warns(fw):
    edit_arch(fw, lambda a: a["grandfathered"].append("src/app -> src/hal"))
    errors, warnings = check_architecture(fw)
    assert any("may only shrink" in e and "src/app -> src/hal" in e for e in errors)
    assert any(w.startswith("src/app -> src/hal: grandfathered but no longer violated") for w in warnings)


def test_ratchet_compares_with_origin_main(fw, tmp_path):
    add_origin(fw, tmp_path)
    edit_arch(fw, lambda a: a["grandfathered"].append("src/app -> src/hal"))
    commit_all(fw, "harness: sneak in a grandfather entry")
    errors, _ = check_architecture(fw)
    assert any("not on origin/main" in e and "may only shrink" in e for e in errors)


def test_uncovered_folder_fails(fw):
    (fw / "src" / "net").mkdir()
    (fw / "src" / "net" / "net.c").write_text("int net_init(void) { return 0; }\n", encoding="utf-8")
    errors, _ = check_architecture(fw)
    assert any(e.startswith("src/net:") and "fw-architecture-sync" in e for e in errors)


def test_ignored_build_output_is_not_scanned(fw):
    (fw / "build").mkdir()
    (fw / "build" / "generated.c").write_text("int x;\n", encoding="utf-8")
    assert check_architecture(fw)[0] == []


def test_missing_architecture_md_fails_and_deleted_folder_warns(fw):
    (fw / "src" / "drivers" / "ARCHITECTURE.md").unlink()
    edit_arch(fw, lambda a: a["modules"].update({"src/legacy": {"kind": "owned", "allowed_deps": []}}))
    errors, warnings = check_architecture(fw)
    assert any(e.startswith("src/drivers:") and "ARCHITECTURE.md" in e for e in errors)
    assert any(w.startswith("src/legacy:") and "no longer exists" in w for w in warnings)


def test_load_architecture_errors(repo):
    with pytest.raises(ArchitectureError, match="fw-harness-init"):
        load_architecture(repo)
    (repo / "harness" / "architecture.json").write_text("{", encoding="utf-8")
    with pytest.raises(ArchitectureError, match="not valid JSON"):
        load_architecture(repo)


def test_main_exit_codes(fw, monkeypatch, capsys):
    monkeypatch.chdir(fw)
    assert main([]) == 0
    assert "arch_check: passed" in capsys.readouterr().out
    edit_arch(fw, lambda a: a.update(grandfathered=[]))
    assert main([]) == 1
    assert "src/hal -> src/app" in capsys.readouterr().err
```

- [ ] **Step 4: Run it and watch it fail**

Run: `py -3 -m pytest tests/scripts/test_arch_check.py`
Expected: FAIL, `ModuleNotFoundError: No module named 'arch_check'`

- [ ] **Step 5: Implement `arch_check.py`**

`SCRIPTS/arch_check.py`:

```python
"""Architecture gate (spec section 6.3): module coverage, approved include dependencies, and the grandfather ratchet."""
import json
import posixpath
import re
import sys
from collections import defaultdict
from pathlib import Path

from console import use_utf8_stdio
from gitutil import git, repo_root
from jsonio import read_json
from ratchet import baseline_ref, baseline_text, new_entries

ARCH_PATH = "harness/architecture.json"
KINDS = ("owned", "vendor", "generated", "test")
READ_ONLY_KINDS = ("vendor", "generated")
SOURCE_SUFFIXES = (".c", ".h")
INCLUDE_RE = re.compile(r'^[ \t]*#[ \t]*include[ \t]*[<"]([^">\n]+)[">]', re.MULTILINE)
EDGE_RE = re.compile(r"^(\S+) -> (\S+)$")


class ArchitectureError(ValueError):
    pass


def validate_architecture(arch):
    if not isinstance(arch, dict):
        return ["architecture must be a JSON object"]
    errors = []
    if arch.get("version") != 1:
        errors.append("version must be 1")
    include_dirs = arch.get("include_dirs")
    if not (isinstance(include_dirs, list) and all(isinstance(d, str) and d for d in include_dirs)):
        errors.append("include_dirs must be an array of repo-relative folders")
    modules = arch.get("modules")
    if not isinstance(modules, dict):
        return errors + ["modules must be an object keyed by repo-relative folder"]
    for path, module in modules.items():
        if (not path or path.startswith("/") or "\\" in path
                or path.endswith("/") or path != posixpath.normpath(path)):
            errors.append(f"modules key {path!r} must be a normalized repo-relative folder "
                          "with forward slashes and no trailing slash")
        if not isinstance(module, dict) or module.get("kind") not in KINDS:
            errors.append(f"modules[{path!r}].kind must be one of {', '.join(KINDS)}")
            continue
        deps = module.get("allowed_deps")
        if not (isinstance(deps, list) and all(isinstance(dep, str) for dep in deps)):
            errors.append(f"modules[{path!r}].allowed_deps must be an array of module folders")
            continue
        for dep in deps:
            if dep not in modules:
                errors.append(f"modules[{path!r}].allowed_deps names {dep!r}, which is not a module")
    grandfathered = arch.get("grandfathered")
    if not isinstance(grandfathered, list):
        errors.append('grandfathered must be an array of "<module> -> <module>" strings')
    else:
        for entry in grandfathered:
            match = EDGE_RE.match(entry) if isinstance(entry, str) else None
            if not match or match.group(1) not in modules or match.group(2) not in modules:
                errors.append(f'grandfathered entry {entry!r} must look like "<module> -> <module>"')
    return errors


def load_architecture(repo):
    path = Path(repo) / ARCH_PATH
    if not path.is_file():
        raise ArchitectureError(f"{ARCH_PATH} not found. Fix: run fw-harness-init to create it")
    try:
        arch = read_json(path)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ArchitectureError(f"{ARCH_PATH} is not valid JSON ({exc}). Fix: repair it or restore it from git") from exc
    errors = validate_architecture(arch)
    if errors:
        raise ArchitectureError(f"{ARCH_PATH} is invalid:\n- " + "\n- ".join(errors))
    return arch


def module_of(path, modules):
    matches = [module for module in modules if path == module or path.startswith(module + "/")]
    return max(matches, key=len) if matches else None


def read_only_prefixes(arch):
    return [path for path, module in arch["modules"].items() if module["kind"] in READ_ONLY_KINDS]


def source_files(repo):
    listing = git(repo, "-c", "core.quotepath=off", "ls-files", "--cached", "--others", "--exclude-standard")
    return sorted(name for name in listing.splitlines()
                  if name.endswith(SOURCE_SUFFIXES) and (Path(repo) / name).is_file())


def _resolve(repo, including_file, target, include_dirs):
    for base in [posixpath.dirname(including_file), *include_dirs]:
        candidate = posixpath.normpath(posixpath.join(base, target))
        if not candidate.startswith("..") and (Path(repo) / candidate).is_file():
            return candidate
    return None


def dependencies(repo, arch, files):
    modules = arch["modules"]
    found = defaultdict(list)
    for name in files:
        source = module_of(name, modules)
        if source is None or modules[source]["kind"] != "owned":
            continue
        text = (Path(repo) / name).read_text(encoding="utf-8", errors="replace")
        for match in INCLUDE_RE.finditer(text):
            resolved = _resolve(repo, name, match.group(1), arch["include_dirs"])
            target = module_of(resolved, modules) if resolved else None
            if target is None or target == source:
                continue
            line = text.count("\n", 0, match.start()) + 1
            found[(source, target)].append(f"{name}:{line}")
    return found


def check_architecture(repo):
    arch = load_architecture(repo)
    modules = arch["modules"]
    errors, warnings = [], []

    files = source_files(repo)
    uncovered = sorted({posixpath.dirname(name) or "." for name in files if module_of(name, modules) is None})
    for folder in uncovered:
        errors.append(f"{folder}: C sources are not covered by any module in {ARCH_PATH}. "
                      "Fix: run fw-architecture-sync")
    for path in sorted(modules):
        if not (Path(repo) / path).is_dir():
            warnings.append(f"{path}: listed in {ARCH_PATH} but the folder no longer exists. Fix: remove it from modules")
        elif not (Path(repo) / path / "ARCHITECTURE.md").is_file():
            errors.append(f"{path}: missing ARCHITECTURE.md. Fix: run fw-architecture-sync")

    grandfathered = set(arch["grandfathered"])
    violations = set()
    for (source, target), where in sorted(dependencies(repo, arch, files).items()):
        if target in modules[source]["allowed_deps"]:
            continue
        edge = f"{source} -> {target}"
        violations.add(edge)
        if edge not in grandfathered:
            shown = ", ".join(where[:3]) + (", ..." if len(where) > 3 else "")
            errors.append(f"{edge}: dependency not approved ({shown}). "
                          f"Fix: remove the include, or have a human approve it in {ARCH_PATH}")
    for edge in sorted(grandfathered - violations):
        warnings.append(f"{edge}: grandfathered but no longer violated. Fix: remove it from the grandfather list")

    ref, warning = baseline_ref(repo)
    if warning:
        warnings.append(warning)
    base = baseline_text(repo, ref, ARCH_PATH)
    base_entries = None
    if base is not None:
        try:
            base_entries = json.loads(base).get("grandfathered", [])
        except (json.JSONDecodeError, AttributeError):
            base_entries = None
    added = new_entries(grandfathered, base_entries)
    if added:
        errors.append(f"{ARCH_PATH} grandfather list gained entries not on {ref}: {', '.join(added)}. "
                      "The list may only shrink. Fix: remove the new dependency instead of grandfathering it")
    return errors, warnings


def main(argv=None):
    use_utf8_stdio()
    repo = repo_root(Path.cwd())
    try:
        errors, warnings = check_architecture(repo)
    except ArchitectureError as exc:
        print(f"arch_check failed: {exc}", file=sys.stderr)
        return 1
    for warning in warnings:
        print(f"arch_check: {warning}")
    for error in errors:
        print(f"arch_check failed: {error}", file=sys.stderr)
    if errors:
        return 1
    print("arch_check: passed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 6: Run it and watch it pass**

Run: `py -3 -m pytest tests/scripts/test_arch_check.py`
Expected: `18 passed`

- [ ] **Step 7: Commit**

```bash
git add tests plugins
git commit -m "Add arch_check gate and sample firmware fixture"
```

---

### Task 4: Command runner, changed files, format and cppcheck steps

**Files:**
- Create: `SCRIPTS/steps.py`
- Test: `tests/scripts/test_steps_lint.py`

**Interfaces:**
- Consumes: `arch_check.ArchitectureError`, `load_architecture`, `read_only_prefixes`; `gitutil.git`; `ratchet.baseline_ref`, `baseline_text`, `new_entries`, `parse_entries`
- Produces:
  - `steps.StepResult(name: str, passed: bool, summary: str, output: str = "")` (dataclass, compares by value)
  - `steps.SUPPRESSIONS_PATH = "harness/cppcheck-suppressions.txt"`
  - `steps.expand_argv(argv) -> list[str]`
  - `steps.run_command(repo, argv) -> tuple[CompletedProcess | None, str | None]` (second item is the missing-tool message)
  - `steps.changed_files(repo, extensions) -> list[str]`
  - `steps.step_format(repo, config) -> StepResult`, `steps.step_cppcheck(repo, config) -> StepResult`

- [ ] **Step 1: Write the failing test**

`tests/scripts/test_steps_lint.py`:

```python
import sys

import pytest

from helpers import PY, add_origin, commit_all, fake_config, make_fixture_repo
from steps import StepResult, changed_files, expand_argv, run_command, step_cppcheck, step_format

FAIL_IF_ARGS = [PY, "-c", "import sys; print(' '.join(sys.argv[1:])); sys.exit(1 if len(sys.argv) > 1 else 0)"]


@pytest.fixture
def fw(tmp_path):
    return make_fixture_repo(tmp_path / "fw")


def test_expand_argv_replaces_python_placeholder():
    assert expand_argv(["{python}", "-c", "pass"]) == [sys.executable, "-c", "pass"]


def test_run_command_reports_missing_tool(fw):
    proc, problem = run_command(fw, ["definitely-not-a-real-tool-xyz", "--version"])
    assert proc is None and "definitely-not-a-real-tool-xyz not found on PATH" in problem


def test_changed_files_include_modified_and_untracked_only(fw):
    assert changed_files(fw, [".c", ".h"]) == []
    (fw / "src" / "app" / "main.c").write_text("int main(void) { return 0; }\n", encoding="utf-8")
    (fw / "src" / "app" / "extra.h").write_text("#define EXTRA 1\n", encoding="utf-8")
    (fw / "src" / "app" / "notes.txt").write_text("x\n", encoding="utf-8")
    assert changed_files(fw, [".c", ".h"]) == ["src/app/extra.h", "src/app/main.c"]


def test_changed_files_since_merge_base_with_origin(fw, tmp_path):
    add_origin(fw, tmp_path)
    (fw / "src" / "drivers" / "uart.c").write_text("int uart_init(void) { return 1; }\n", encoding="utf-8")
    commit_all(fw, "FW-0001 change uart")
    assert changed_files(fw, [".c"]) == ["src/drivers/uart.c"]


def test_format_passes_when_nothing_changed(fw):
    result = step_format(fw, fake_config(format={"command": FAIL_IF_ARGS, "extensions": [".c", ".h"]}))
    assert result == StepResult("format", True, "no changed C sources to check")


def test_format_checks_changed_files_but_skips_vendor(fw):
    config = fake_config(format={"command": FAIL_IF_ARGS, "extensions": [".c", ".h"]})
    (fw / "third_party" / "cmsis" / "Include" / "core_cm4.h").write_text("/* vendor update */\n", encoding="utf-8")
    assert step_format(fw, config).passed
    (fw / "src" / "app" / "main.c").write_text("int main(void){return 0;}\n", encoding="utf-8")
    result = step_format(fw, config)
    assert not result.passed
    assert "src/app/main.c" in result.output and "core_cm4.h" not in result.output


def test_cppcheck_runs_with_suppressions_list_and_paths(fw):
    echo = [PY, "-c", "import sys; print(' '.join(sys.argv[1:]))"]
    result = step_cppcheck(fw, fake_config(cppcheck={"command": echo, "paths": ["src"]}))
    assert result.passed
    assert "--suppressions-list=harness/cppcheck-suppressions.txt src" in result.output


def test_cppcheck_failure(fw):
    fail = [PY, "-c", "import sys; print('src/app/main.c:3: error: nullPointer'); sys.exit(1)"]
    result = step_cppcheck(fw, fake_config(cppcheck={"command": fail, "paths": ["src"]}))
    assert not result.passed and "nullPointer" in result.output


def test_cppcheck_suppression_ratchet(fw):
    path = fw / "harness" / "cppcheck-suppressions.txt"
    path.write_text(path.read_text(encoding="utf-8") + "nullPointer:src/app/main.c\n", encoding="utf-8")
    result = step_cppcheck(fw, fake_config())
    assert not result.passed
    assert "may only shrink" in result.summary and "nullPointer:src/app/main.c" in result.summary
```

- [ ] **Step 2: Run it and watch it fail**

Run: `py -3 -m pytest tests/scripts/test_steps_lint.py`
Expected: FAIL, `ModuleNotFoundError: No module named 'steps'`

- [ ] **Step 3: Implement the first part of `steps.py`**

`SCRIPTS/steps.py`:

```python
"""The check steps (spec section 4.2). Each step takes (repo, config) and returns a StepResult."""
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from arch_check import ArchitectureError, load_architecture, read_only_prefixes
from gitutil import git
from ratchet import baseline_ref, baseline_text, new_entries, parse_entries

SUPPRESSIONS_PATH = "harness/cppcheck-suppressions.txt"
OUTPUT_TAIL_LINES = 40


@dataclass
class StepResult:
    name: str
    passed: bool
    summary: str
    output: str = ""


def expand_argv(argv):
    return [sys.executable if item == "{python}" else item for item in argv]


def run_command(repo, argv):
    argv = expand_argv(argv)
    if shutil.which(argv[0]) is None:
        return None, f"{argv[0]} not found on PATH. Fix: install it, then run init to confirm the version"
    proc = subprocess.run(argv, cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return proc, None


def _output(proc):
    lines = (proc.stdout + proc.stderr).rstrip().splitlines()
    return "\n".join(lines[-OUTPUT_TAIL_LINES:])


def changed_files(repo, extensions):
    ref, _ = baseline_ref(repo)
    base = git(repo, "merge-base", "HEAD", ref) if ref != "HEAD" else "HEAD"
    changed = git(repo, "-c", "core.quotepath=off", "diff", "--name-only", "--diff-filter=ACMR", base).splitlines()
    untracked = git(repo, "-c", "core.quotepath=off", "ls-files", "--others", "--exclude-standard").splitlines()
    return sorted({name for name in changed + untracked
                   if Path(name).suffix in extensions and (Path(repo) / name).is_file()})


def _read_only_prefixes(repo):
    try:
        return read_only_prefixes(load_architecture(repo))
    except ArchitectureError:
        return []  # the arch step reports the broken file


def step_format(repo, config):
    spec = config["check"]["format"]
    prefixes = _read_only_prefixes(repo)
    files = [name for name in changed_files(repo, spec["extensions"])
             if not any(name == prefix or name.startswith(prefix + "/") for prefix in prefixes)]
    if not files:
        return StepResult("format", True, "no changed C sources to check")
    proc, problem = run_command(repo, spec["command"] + files)
    if problem:
        return StepResult("format", False, problem)
    if proc.returncode != 0:
        return StepResult("format", False,
                          f"{len(files)} changed file(s) are not formatted. "
                          "Fix: run the formatter in place on them (for example clang-format -i)",
                          _output(proc))
    return StepResult("format", True, f"{len(files)} changed file(s) formatted", _output(proc))


def _suppression_additions(repo):
    ref, warning = baseline_ref(repo)
    path = Path(repo) / SUPPRESSIONS_PATH
    current = parse_entries(path.read_text(encoding="utf-8")) if path.is_file() else set()
    base = baseline_text(repo, ref, SUPPRESSIONS_PATH)
    return new_entries(current, parse_entries(base) if base is not None else None), ref, warning


def step_cppcheck(repo, config):
    spec = config["check"]["cppcheck"]
    added, ref, warning = _suppression_additions(repo)
    if added:
        return StepResult("cppcheck", False,
                          f"{SUPPRESSIONS_PATH} gained entries not on {ref}: {', '.join(added)}. "
                          "The list may only shrink. Fix: fix the findings instead of suppressing them")
    argv = list(spec["command"])
    if (Path(repo) / SUPPRESSIONS_PATH).is_file():
        argv.append(f"--suppressions-list={SUPPRESSIONS_PATH}")
    proc, problem = run_command(repo, argv + spec["paths"])
    if problem:
        return StepResult("cppcheck", False, problem)
    output = "\n".join(part for part in (warning, _output(proc)) if part)
    if proc.returncode != 0:
        return StepResult("cppcheck", False,
                          "cppcheck reported findings. Fix: address them; suppressions may only shrink", output)
    return StepResult("cppcheck", True, f"no findings in {', '.join(spec['paths'])}", output)
```

- [ ] **Step 4: Run it and watch it pass**

Run: `py -3 -m pytest tests/scripts/test_steps_lint.py`
Expected: `9 passed`

- [ ] **Step 5: Commit**

```bash
git add tests plugins
git commit -m "Add command runner, format step, and cppcheck step with suppression ratchet"
```

---

### Task 5: Size budget and the remaining steps

**Files:**
- Create: `SCRIPTS/size_check.py`
- Modify: `SCRIPTS/steps.py` (add imports and append the remaining steps)
- Test: `tests/scripts/test_steps_build.py`

**Interfaces:**
- Consumes: Task 4's `StepResult`, `run_command`, `_output`; `arch_check.check_architecture`; `ticket_check.check_tickets`
- Produces:
  - `size_check.parse_berkeley(output) -> tuple[int, int, int]` (text, data, bss; raises `ValueError` mentioning `text/data/bss`)
  - `size_check.evaluate(text, data, bss, flash_budget, ram_budget) -> tuple[list[str], str]` (problems, summary like `flash 12400/16384 B (75%), RAM 2400/4096 B (58%)`)
  - `steps.step_arch`, `steps.step_tickets`, `steps.step_build`, `steps.step_test`, `steps.step_size`
  - `steps.STEPS` (tuple of `(name, function)` in spec order: format, cppcheck, arch, tickets, build, test, size)

- [ ] **Step 1: Write the failing test**

`tests/scripts/test_steps_build.py`:

```python
import pytest

from helpers import PY, fake_config, make_fixture_repo
from size_check import evaluate, parse_berkeley
from steps import STEPS, step_arch, step_build, step_size, step_test, step_tickets

BERKELEY = ("   text\t   data\t    bss\t    dec\t    hex\tfilename\n"
            "  12000\t    400\t   2000\t  14400\t   3840\tbuild/target/firmware.elf\n")


@pytest.fixture
def fw(tmp_path):
    return make_fixture_repo(tmp_path / "fw")


def test_parse_berkeley():
    assert parse_berkeley(BERKELEY) == (12000, 400, 2000)
    with pytest.raises(ValueError, match="text/data/bss"):
        parse_berkeley("size: build/target/firmware.elf: No such file")


def test_evaluate_budget():
    problems, summary = evaluate(12000, 400, 2000, flash_budget=16384, ram_budget=4096)
    assert problems == [] and summary == "flash 12400/16384 B (75%), RAM 2400/4096 B (58%)"
    problems, _ = evaluate(12000, 400, 2000, flash_budget=12000, ram_budget=2000)
    assert problems == ["flash 12400 B exceeds the 12000 B budget", "RAM 2400 B exceeds the 2000 B budget"]


def test_steps_run_in_spec_order():
    assert [name for name, _ in STEPS] == ["format", "cppcheck", "arch", "tickets", "build", "test", "size"]


def test_commands_run_in_order_and_stop_at_failure(fw):
    marker = fw / "ran.txt"
    append = [PY, "-c", f"open(r'{marker}', 'a').write('x')"]
    fail = [PY, "-c", "import sys; print('undefined reference to main'); sys.exit(2)"]
    ok = step_build(fw, fake_config(build={"commands": [append, append]}))
    assert ok.passed and marker.read_text() == "xx"
    bad = step_test(fw, fake_config(test={"commands": [fail, append]}))
    assert not bad.passed and "exit 2" in bad.summary
    assert "undefined reference" in bad.output and marker.read_text() == "xx"


def test_size_step(fw):
    printer = [PY, "-c", f"print({BERKELEY!r})"]
    ok = step_size(fw, fake_config(size={"command": printer, "flash_budget": 16384, "ram_budget": 4096}))
    assert ok.passed and ok.summary.startswith("flash 12400/16384 B")
    over = step_size(fw, fake_config(size={"command": printer, "flash_budget": 1000, "ram_budget": 4096}))
    assert not over.passed and "exceeds" in over.summary
    garbage = step_size(fw, fake_config(size={"command": [PY, "-c", "print('nothing')"], "flash_budget": 1, "ram_budget": 1}))
    assert not garbage.passed and "text/data/bss" in garbage.summary


def test_arch_and_tickets_steps(fw):
    assert step_arch(fw, fake_config()).passed
    assert step_tickets(fw, fake_config()).passed
    (fw / "harness" / "tickets" / "FW-0001.json").write_text("{", encoding="utf-8")
    result = step_tickets(fw, fake_config())
    assert not result.passed and "FW-0001.json" in result.output
    (fw / "harness" / "architecture.json").write_text("{", encoding="utf-8")
    assert not step_arch(fw, fake_config()).passed
```

- [ ] **Step 2: Run it and watch it fail**

Run: `py -3 -m pytest tests/scripts/test_steps_build.py`
Expected: FAIL, `ModuleNotFoundError: No module named 'size_check'`

- [ ] **Step 3: Implement `size_check.py`**

`SCRIPTS/size_check.py`:

```python
"""Size budget from Berkeley-format size output (for example arm-none-eabi-size): flash = text + data, RAM = data + bss."""


def parse_berkeley(output):
    for line in output.splitlines():
        fields = line.split()
        if len(fields) >= 3 and all(field.isdigit() for field in fields[:3]):
            return int(fields[0]), int(fields[1]), int(fields[2])
    raise ValueError("could not find text/data/bss numbers in the size output")


def evaluate(text, data, bss, flash_budget, ram_budget):
    flash, ram = text + data, data + bss
    problems = []
    if flash > flash_budget:
        problems.append(f"flash {flash} B exceeds the {flash_budget} B budget")
    if ram > ram_budget:
        problems.append(f"RAM {ram} B exceeds the {ram_budget} B budget")
    summary = (f"flash {flash}/{flash_budget} B ({flash * 100 // flash_budget}%), "
               f"RAM {ram}/{ram_budget} B ({ram * 100 // ram_budget}%)")
    return problems, summary
```

- [ ] **Step 4: Extend `steps.py`**

Change the import block of `SCRIPTS/steps.py` to:

```python
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from arch_check import ArchitectureError, check_architecture, load_architecture, read_only_prefixes
from gitutil import git
from ratchet import baseline_ref, baseline_text, new_entries, parse_entries
from size_check import evaluate, parse_berkeley
from ticket_check import check_tickets
```

Append to the end of `SCRIPTS/steps.py`:

```python
def step_arch(repo, config):
    try:
        errors, warnings = check_architecture(repo)
    except ArchitectureError as exc:
        return StepResult("arch", False, str(exc))
    output = "\n".join(errors + warnings)
    if errors:
        return StepResult("arch", False, f"{len(errors)} architecture problem(s)", output)
    return StepResult("arch", True, "module coverage and dependencies approved", output)


def step_tickets(repo, config):
    errors = check_tickets(repo)
    if errors:
        return StepResult("tickets", False, f"{len(errors)} ticket problem(s)", "\n".join(errors))
    return StepResult("tickets", True, "ticket files consistent")


def _run_commands(name, repo, commands):
    outputs = []
    for argv in commands:
        proc, problem = run_command(repo, argv)
        if problem:
            return StepResult(name, False, problem, "\n".join(outputs))
        if _output(proc):
            outputs.append(_output(proc))
        if proc.returncode != 0:
            return StepResult(name, False, f"{' '.join(argv)} failed (exit {proc.returncode})", "\n".join(outputs))
    return StepResult(name, True, f"{len(commands)} command(s) succeeded", "\n".join(outputs))


def step_build(repo, config):
    return _run_commands("build", repo, config["check"]["build"]["commands"])


def step_test(repo, config):
    return _run_commands("test", repo, config["check"]["test"]["commands"])


def step_size(repo, config):
    spec = config["check"]["size"]
    proc, problem = run_command(repo, spec["command"])
    if problem:
        return StepResult("size", False, problem)
    if proc.returncode != 0:
        return StepResult("size", False, f"size tool failed (exit {proc.returncode})", _output(proc))
    try:
        text, data, bss = parse_berkeley(proc.stdout)
    except ValueError as exc:
        return StepResult("size", False, f"{exc}. Fix: point check.size.command at the built ELF", _output(proc))
    problems, summary = evaluate(text, data, bss, spec["flash_budget"], spec["ram_budget"])
    if problems:
        return StepResult("size", False, "; ".join(problems) + f" ({summary}). Fix: shrink the image or revisit the budget in harness/config.json")
    return StepResult("size", True, summary)


STEPS = (
    ("format", step_format),
    ("cppcheck", step_cppcheck),
    ("arch", step_arch),
    ("tickets", step_tickets),
    ("build", step_build),
    ("test", step_test),
    ("size", step_size),
)
```

- [ ] **Step 5: Run it and watch it pass**

Run: `py -3 -m pytest tests/scripts/test_steps_build.py tests/scripts/test_steps_lint.py`
Expected: `15 passed`

- [ ] **Step 6: Commit**

```bash
git add tests plugins
git commit -m "Add build, test, size, arch, and tickets check steps"
```

---

### Task 6: `check.py`

**Files:**
- Create: `SCRIPTS/check.py`
- Test: `tests/scripts/test_check.py`

**Interfaces:**
- Consumes: `steps.STEPS`, `steps.StepResult`; `harness_config.load_config`, `ConfigError`; `identity.current_identity`, `IdentityError`; `tickets.load_ticket`, `make_evidence`, `save_ticket`, `validate_ticket`, `now_iso`; `gitutil.git`, `repo_root`, `GitError`; `arch_check.ArchitectureError`; `console.use_utf8_stdio`
- Produces:
  - `check.LOG_DIR = ".verify_logs"`
  - `check.run_check(repo, config, log) -> list[StepResult]` (`log` is a one-argument callable; stops after the first failed step; an exception inside a step becomes a failed `StepResult`)
  - `check.summarize(results) -> tuple[str, bool]` (`"check 7/7 passed"` or `"check failed at <step> (<n>/7 passed)"`)
  - `check.main(argv=None, cwd=None, now=None) -> int` (prints `== <step>: passed|FAILED: <summary>` lines and step output, writes `.verify_logs/check-<YYYYmmdd-HHMMSS>.log`, `--record FW-NNNN` adds check evidence)

- [ ] **Step 1: Write the failing test**

`tests/scripts/test_check.py`:

```python
import pytest

from check import main, summarize
from helpers import PY, commit_all, fake_config, git, make_fixture_repo, write_config
from steps import StepResult
from tickets import load_ticket, new_ticket, save_ticket
from transitions import transition

NOW = "2026-09-15T10:00:00+08:00"
ALICE = {"name": "Alice Chen", "email": "alice@example.com"}
FAIL = [PY, "-c", "import sys; print('boom'); sys.exit(1)"]


@pytest.fixture
def fw(tmp_path):
    repo = make_fixture_repo(tmp_path / "fw")
    write_config(repo, fake_config())
    return repo


def run(repo, *argv):
    return main(list(argv), cwd=repo, now=NOW)


def test_all_steps_pass_and_log_is_written(fw, capsys):
    assert run(fw) == 0
    assert "check 7/7 passed" in capsys.readouterr().out
    logs = list((fw / ".verify_logs").glob("check-*.log"))
    assert len(logs) == 1 and "check 7/7 passed" in logs[0].read_text(encoding="utf-8")
    assert git(fw, "status", "--porcelain") == ""


def test_stops_at_first_failure(fw, capsys):
    write_config(fw, fake_config(build={"commands": [FAIL]}))
    assert run(fw) == 1
    out = capsys.readouterr().out
    assert "check failed at build (4/7 passed)" in out
    assert "boom" in out and "== test" not in out


def test_missing_tool_fails_its_step(fw, capsys):
    write_config(fw, fake_config(cppcheck={"command": ["definitely-not-a-real-tool-xyz"], "paths": ["src"]}))
    assert run(fw) == 1
    out = capsys.readouterr().out
    assert "check failed at cppcheck" in out and "not found on PATH" in out


def test_size_over_budget_fails_the_last_step(fw, capsys):
    size = fake_config()["check"]["size"]
    write_config(fw, fake_config(size=dict(size, flash_budget=10)))
    assert run(fw) == 1
    assert "check failed at size (6/7 passed)" in capsys.readouterr().out


def test_missing_config(tmp_path, capsys):
    repo = make_fixture_repo(tmp_path / "noconfig")
    assert run(repo) == 1
    assert "harness/config.json not found" in capsys.readouterr().err


def test_summarize():
    names = ("format", "cppcheck", "arch", "tickets", "build", "test", "size")
    passing = [StepResult(name, True, "") for name in names]
    assert summarize(passing) == ("check 7/7 passed", True)
    assert summarize(passing[:3] + [StepResult("tickets", False, "")]) == ("check failed at tickets (3/7 passed)", False)


def open_active_ticket(repo):
    ticket = new_ticket("FW-0001", "UART DMA", "drivers/uart", ALICE, NOW)
    ticket = transition(repo, transition(repo, ticket, "next", ALICE, NOW), "active", ALICE, NOW)
    save_ticket(repo, ticket)
    commit_all(repo, "FW-0001 claim")


def test_record_needs_clean_tree(fw, capsys):
    open_active_ticket(fw)
    (fw / "src" / "app" / "main.c").write_text("int main(void) { return 0; }\n", encoding="utf-8")
    assert run(fw, "--record", "FW-0001") == 1
    assert "clean working tree" in capsys.readouterr().err
    assert load_ticket(fw, "FW-0001")["evidence"] == []


def test_record_passing_check_enables_verifying(fw):
    open_active_ticket(fw)
    assert run(fw, "--record", "FW-0001") == 0
    evidence = load_ticket(fw, "FW-0001")["evidence"][-1]
    assert evidence["passed"] is True and evidence["summary"] == "check 7/7 passed"
    assert evidence["by"] == ALICE and evidence["commit"] == git(fw, "rev-parse", "HEAD")[:10]
    assert transition(fw, load_ticket(fw, "FW-0001"), "verifying", ALICE, NOW)["status"] == "verifying"


def test_record_failing_check(fw):
    open_active_ticket(fw)
    write_config(fw, fake_config(test={"commands": [FAIL]}))
    assert run(fw, "--record", "FW-0001") == 1
    evidence = load_ticket(fw, "FW-0001")["evidence"][-1]
    assert evidence["passed"] is False and evidence["summary"] == "check failed at test (5/7 passed)"


def test_record_unknown_ticket(fw, capsys):
    assert run(fw, "--record", "FW-0099") == 1
    assert "FW-0099" in capsys.readouterr().err
```

- [ ] **Step 2: Run it and watch it fail**

Run: `py -3 -m pytest tests/scripts/test_check.py`
Expected: FAIL, `ModuleNotFoundError: No module named 'check'`

- [ ] **Step 3: Implement `check.py`**

`SCRIPTS/check.py`:

```python
"""The only implementation of `check` (spec section 4.2). Makefile and the init wrappers call it and add no flags."""
import argparse
import sys
from datetime import datetime
from pathlib import Path

from arch_check import ArchitectureError
from console import use_utf8_stdio
from gitutil import GitError, git, repo_root
from harness_config import ConfigError, load_config
from identity import IdentityError, current_identity
from steps import STEPS, StepResult
from tickets import load_ticket, make_evidence, now_iso, save_ticket, validate_ticket

LOG_DIR = ".verify_logs"


def run_check(repo, config, log):
    results = []
    for name, step in STEPS:
        try:
            result = step(repo, config)
        except (ArchitectureError, GitError, OSError, ValueError) as exc:
            result = StepResult(name, False, f"{type(exc).__name__}: {exc}")
        results.append(result)
        log(f"== {name}: {'passed' if result.passed else 'FAILED'}: {result.summary}")
        if result.output:
            log(result.output)
        if not result.passed:
            break
    return results


def summarize(results):
    passed = sum(1 for result in results if result.passed)
    if passed == len(STEPS):
        return f"check {passed}/{len(STEPS)} passed", True
    return f"check failed at {results[-1].name} ({passed}/{len(STEPS)} passed)", False


def _record(repo, ticket_id, results, now):
    summary, passed = summarize(results)
    ticket = load_ticket(repo, ticket_id)
    commit = git(repo, "rev-parse", "HEAD")[:10]
    ticket["evidence"].append(make_evidence("check", current_identity(repo), now,
                                            commit=commit, summary=summary, passed=passed))
    errors = validate_ticket(ticket, f"{ticket_id}.json")
    if errors:
        raise ValueError("; ".join(errors))
    save_ticket(repo, ticket)


def main(argv=None, cwd=None, now=None):
    use_utf8_stdio()
    parser = argparse.ArgumentParser(prog="check.py",
                                     description="Run the harness gates in order and stop at the first failure.")
    parser.add_argument("--record", metavar="FW-NNNN",
                        help="record the result as check evidence on this ticket (needs a clean working tree)")
    args = parser.parse_args(argv)
    try:
        repo = repo_root(cwd or Path.cwd())
        config = load_config(repo)
        if args.record:
            load_ticket(repo, args.record)
            current_identity(repo)
            if git(repo, "status", "--porcelain"):
                raise ValueError("--record needs a clean working tree so the evidence matches HEAD. "
                                 "Fix: commit or stash your changes first")
    except (ConfigError, GitError, IdentityError, FileNotFoundError, ValueError) as exc:
        print(f"check.py failed: {exc}", file=sys.stderr)
        return 1

    lines = []

    def log(line):
        print(line)
        lines.append(line)

    results = run_check(repo, config, log)
    summary, passed = summarize(results)
    log(summary)
    log_dir = repo / LOG_DIR
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"check-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
    log_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if args.record:
        try:
            _record(repo, args.record, results, now or now_iso())
        except (GitError, IdentityError, FileNotFoundError, ValueError) as exc:
            print(f"check.py --record failed: {exc}", file=sys.stderr)
            return 1
        print(f"Recorded check evidence on {args.record}: {summary}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 4: Run it and watch it pass**

Run: `py -3 -m pytest tests/scripts/test_check.py`
Expected: `10 passed`

- [ ] **Step 5: Commit**

```bash
git add tests plugins
git commit -m "Add check.py runner with logs and --record"
```

---

### Task 7: Commit message rule and git hooks

**Files:**
- Create: `SCRIPTS/commit_msg_check.py`
- Create: `TEMPLATES/.githooks/_python.sh`, `TEMPLATES/.githooks/commit-msg`, `TEMPLATES/.githooks/post-commit`, `TEMPLATES/.githooks/post-merge`
- Test: `tests/scripts/test_commit_msg.py`, `tests/scripts/test_hooks.py`

**Interfaces:**
- Consumes: `index.TICKET_REF_RE`; `tickets.ticket_path`; `gitutil.repo_root`; `console.use_utf8_stdio`
- Produces:
  - `commit_msg_check.check_message(repo, text) -> list[str]`
  - `commit_msg_check.main(argv=None, cwd=None) -> int`
  - Hooks run from the repo root and call `harness/scripts/commit_msg_check.py`, `index.py`, and `ticket_check.py`. `post-commit` and `post-merge` never fail the git operation. `_python.sh` defines `harness_python`, trying `py -3`, then `python3`, then `python`.

- [ ] **Step 1: Write the failing tests**

`tests/scripts/test_commit_msg.py`:

```python
import pytest

from commit_msg_check import check_message, main
from tickets import new_ticket, save_ticket

ALICE = {"name": "Alice Chen", "email": "alice@example.com"}
NOW = "2026-09-15T10:00:00+08:00"


@pytest.fixture
def repo_with_ticket(repo):
    save_ticket(repo, new_ticket("FW-0001", "t", "a", ALICE, NOW))
    return repo


@pytest.mark.parametrize("message", [
    "FW-0001 add DMA receive",
    "fix(uart): overflow\n\nRefs FW-0001",
    "harness: update hooks",
    "chore(ci): tweak",
    "chore!: drop Python 3.8",
    "Merge branch 'feature/x'",
    'Revert "FW-0001 add DMA receive"',
    "fixup! FW-0001 add DMA receive",
    "# comment only\n",
])
def test_accepted(repo_with_ticket, message):
    assert check_message(repo_with_ticket, message) == []


def test_missing_ticket_reference(repo_with_ticket):
    errors = check_message(repo_with_ticket, "tweak things")
    assert len(errors) == 1 and "FW-NNNN" in errors[0]


def test_unknown_ticket(repo_with_ticket):
    assert check_message(repo_with_ticket, "FW-0001 and FW-0099") == [
        "commit message references tickets that do not exist: FW-0099. Fix: open the ticket with ticket.py new first"
    ]


def test_reference_in_comment_line_does_not_count(repo_with_ticket):
    assert check_message(repo_with_ticket, "tweak\n# FW-0001 only in a comment") != []


def test_main_reads_message_file(repo_with_ticket, tmp_path, capsys):
    message = tmp_path / "COMMIT_EDITMSG"
    message.write_text("tweak things\n", encoding="utf-8")
    assert main([str(message)], cwd=repo_with_ticket) == 1
    assert "FW-NNNN" in capsys.readouterr().err
    message.write_text("FW-0001 real work\n", encoding="utf-8")
    assert main([str(message)], cwd=repo_with_ticket) == 0
```

`tests/scripts/test_hooks.py`:

```python
import json
import shutil
import stat
import subprocess

import pytest

from helpers import SCRIPTS, TEMPLATES, commit_all, git
from tickets import new_ticket, save_ticket

ALICE = {"name": "Alice Chen", "email": "alice@example.com"}
NOW = "2026-09-15T10:00:00+08:00"


@pytest.fixture
def hooked(repo):
    shutil.copytree(SCRIPTS, repo / "harness" / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(TEMPLATES / ".githooks", repo / ".githooks")
    for hook in (repo / ".githooks").iterdir():
        hook.chmod(hook.stat().st_mode | stat.S_IEXEC)
    (repo / ".gitignore").write_text("feature_list.json\n__pycache__/\n.verify_logs/\n", encoding="utf-8")
    git(repo, "config", "core.hooksPath", ".githooks")
    commit_all(repo, "harness: install hooks")
    return repo


def try_commit(repo, message):
    return subprocess.run(["git", "commit", "--allow-empty", "-m", message], cwd=repo,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def read_index(repo):
    return json.loads((repo / "feature_list.json").read_text(encoding="utf-8"))


def test_commit_without_ticket_is_rejected(hooked):
    result = try_commit(hooked, "tweak things")
    assert result.returncode != 0 and "FW-NNNN" in result.stderr


def test_valid_commit_builds_index_and_keeps_tree_clean(hooked):
    save_ticket(hooked, new_ticket("FW-0001", "UART DMA", "drivers/uart", ALICE, NOW))
    commit_all(hooked, "harness: open FW-0001")
    result = try_commit(hooked, "FW-0001 start work")
    assert result.returncode == 0, result.stderr
    assert read_index(hooked)["tickets"][0]["commits"][0]["subject"] == "FW-0001 start work"
    assert git(hooked, "status", "--porcelain") == ""


def test_post_merge_rebuilds_index(hooked):
    git(hooked, "checkout", "-b", "side")
    save_ticket(hooked, new_ticket("FW-0001", "UART DMA", "drivers/uart", ALICE, NOW))
    commit_all(hooked, "harness: open FW-0001")
    git(hooked, "checkout", "main")
    (hooked / "feature_list.json").unlink(missing_ok=True)
    git(hooked, "merge", "--no-ff", "--no-edit", "side")
    assert [ticket["id"] for ticket in read_index(hooked)["tickets"]] == ["FW-0001"]
```

- [ ] **Step 2: Run them and watch them fail**

Run: `py -3 -m pytest tests/scripts/test_commit_msg.py tests/scripts/test_hooks.py`
Expected: FAIL, `ModuleNotFoundError: No module named 'commit_msg_check'` (and `FileNotFoundError` for `.githooks` in the hook tests)

- [ ] **Step 3: Implement `commit_msg_check.py`**

`SCRIPTS/commit_msg_check.py`:

```python
"""commit-msg hook check (spec section 4.3): reference existing tickets, or use an exempt prefix."""
import re
import sys
from pathlib import Path

from console import use_utf8_stdio
from gitutil import repo_root
from index import TICKET_REF_RE
from tickets import ticket_path

EXEMPT_PREFIX_RE = re.compile(r"^(harness|chore)(\([^)]*\))?!?:")
GIT_GENERATED_PREFIXES = ("Merge ", "Revert ", "fixup! ", "squash! ", "amend! ")


def check_message(repo, text):
    lines = [line for line in text.splitlines() if not line.startswith("#")]
    message = "\n".join(lines).strip()
    if not message:
        return []
    subject = message.splitlines()[0]
    if subject.startswith(GIT_GENERATED_PREFIXES) or EXEMPT_PREFIX_RE.match(subject):
        return []
    ids = sorted(set(TICKET_REF_RE.findall(message)))
    if not ids:
        return ["commit message must reference a ticket (FW-NNNN) or start with harness: or chore:"]
    missing = [ticket_id for ticket_id in ids if not ticket_path(repo, ticket_id).is_file()]
    if missing:
        return [f"commit message references tickets that do not exist: {', '.join(missing)}. "
                "Fix: open the ticket with ticket.py new first"]
    return []


def main(argv=None, cwd=None):
    use_utf8_stdio()
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: commit_msg_check.py <commit message file>", file=sys.stderr)
        return 2
    repo = repo_root(cwd or Path.cwd())
    errors = check_message(repo, Path(args[0]).read_text(encoding="utf-8", errors="replace"))
    for error in errors:
        print(f"commit-msg: {error}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Create the hooks**

`TEMPLATES/.githooks/_python.sh`:

```sh
# Sourced by the hooks and init.sh. Prints a command that runs Python 3.9+.
# On Windows, python may be the Microsoft Store stub, so the py launcher comes first.
harness_python() {
  for candidate in "py -3" python3 python; do
    if $candidate -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" >/dev/null 2>&1; then
      echo "$candidate"
      return 0
    fi
  done
  return 1
}
```

`TEMPLATES/.githooks/commit-msg`:

```sh
#!/bin/sh
# The commit message must reference an existing ticket or start with harness: or chore:.
. "$(dirname "$0")/_python.sh"
PY=$(harness_python) || { echo "commit-msg: Python 3.9+ not found, cannot check the message" >&2; exit 1; }
exec $PY harness/scripts/commit_msg_check.py "$1"
```

`TEMPLATES/.githooks/post-commit`:

```sh
#!/bin/sh
# Regenerate feature_list.json (gitignored). Touches no tracked file and never fails the commit.
. "$(dirname "$0")/_python.sh"
PY=$(harness_python) || exit 0
$PY harness/scripts/index.py >/dev/null 2>&1 \
  || echo "post-commit: warning: feature_list.json was not regenerated; run harness/scripts/index.py" >&2
exit 0
```

`TEMPLATES/.githooks/post-merge`:

```sh
#!/bin/sh
# Regenerate the index and check ticket consistency after a merge. Warns only; never fails the merge.
. "$(dirname "$0")/_python.sh"
PY=$(harness_python) || exit 0
$PY harness/scripts/index.py >/dev/null 2>&1
$PY harness/scripts/ticket_check.py \
  || echo "post-merge: ticket_check failed after the merge; fix the problems above (for clashing IDs, use ticket.py renumber)" >&2
exit 0
```

Make the hooks executable in git, so Linux and macOS clones can run them:

```bash
git add plugins/fw-c-harness/skills/fw-harness-init/templates/.githooks
git update-index --chmod=+x plugins/fw-c-harness/skills/fw-harness-init/templates/.githooks/commit-msg plugins/fw-c-harness/skills/fw-harness-init/templates/.githooks/post-commit plugins/fw-c-harness/skills/fw-harness-init/templates/.githooks/post-merge
```

- [ ] **Step 5: Run the tests and watch them pass**

Run: `py -3 -m pytest tests/scripts/test_commit_msg.py tests/scripts/test_hooks.py`
Expected: `16 passed`

- [ ] **Step 6: Commit**

```bash
git add tests plugins
git commit -m "Add commit message rule and git hooks"
```

---

### Task 8: `init_check` and the wrappers

**Files:**
- Create: `SCRIPTS/init_check.py`
- Create: `TEMPLATES/Makefile`, `TEMPLATES/init.sh`, `TEMPLATES/init.ps1`
- Test: `tests/scripts/test_init_check.py`, `tests/scripts/test_wrappers.py`

**Interfaces:**
- Consumes: `check.main`; `arch_check.load_architecture`, `ArchitectureError`; `harness_config.load_config`, `ConfigError`; `identity.current_identity`, `IdentityError`; `gitutil.git`, `repo_root`; `console.use_utf8_stdio`
- Produces:
  - `init_check.REQUIRED_FILES`, `init_check.REQUIRED_DIRS`
  - `init_check.check_python() -> tuple[bool, str]`
  - `init_check.check_identity(repo) -> tuple[bool, str]` (`(True, "git identity: <name> <<email>>")`)
  - `init_check.check_hooks_path(repo) -> tuple[bool, str]`
  - `init_check.check_layout(repo) -> tuple[bool, str]` (`(True, "harness layout and JSON files valid")`)
  - `init_check.tool_versions(repo, tools) -> list[tuple[bool, str]]` (`"<tool>: <first line of --version>"`, or `"<tool> not found on PATH. ..."`)
  - `init_check.main(argv=None, cwd=None) -> int` (prints `[ok] ...` / `[FAIL] ...`, runs `check.main` only when every item passes, otherwise prints `check skipped: ...`; writes `.verify_logs/init-<YYYYmmdd-HHMMSS>.log`)

- [ ] **Step 1: Write the failing tests**

`tests/scripts/test_init_check.py`:

```python
import sys

import pytest

from helpers import fake_config, git, make_fixture_repo, write_config
from init_check import check_hooks_path, check_identity, check_layout, check_python, main, tool_versions


@pytest.fixture
def fw(tmp_path):
    repo = make_fixture_repo(tmp_path / "fw")
    write_config(repo, fake_config())
    git(repo, "config", "core.hooksPath", ".githooks")
    return repo


def test_python_version_ok():
    ok, message = check_python()
    assert ok and message.startswith("Python 3.")


def test_identity(fw):
    assert check_identity(fw) == (True, "git identity: Alice Chen <alice@example.com>")
    git(fw, "config", "--unset", "user.email")
    ok, message = check_identity(fw)
    assert not ok and "git config user.email" in message


def test_hooks_path(fw):
    assert check_hooks_path(fw)[0]
    git(fw, "config", "--unset", "core.hooksPath")
    ok, message = check_hooks_path(fw)
    assert not ok and "git config core.hooksPath .githooks" in message


def test_tool_versions(fw):
    found, missing = tool_versions(fw, [sys.executable, "definitely-not-a-real-tool-xyz"])
    assert found[0] and "Python 3" in found[1]
    assert not missing[0] and "not found on PATH" in missing[1]


def test_layout(fw):
    assert check_layout(fw) == (True, "harness layout and JSON files valid")
    (fw / "harness" / "cppcheck-suppressions.txt").unlink()
    ok, message = check_layout(fw)
    assert not ok and "harness/cppcheck-suppressions.txt" in message


def test_layout_reports_invalid_json(fw):
    (fw / "harness" / "architecture.json").write_text("{", encoding="utf-8")
    ok, message = check_layout(fw)
    assert not ok and "architecture.json" in message


def test_main_runs_check_when_environment_is_ready(fw, capsys):
    assert main([], cwd=fw) == 0
    out = capsys.readouterr().out
    assert "[ok] git identity" in out and "check 7/7 passed" in out
    assert list((fw / ".verify_logs").glob("init-*.log"))


def test_main_skips_check_when_environment_fails(fw, capsys):
    write_config(fw, dict(fake_config(), required_tools=["definitely-not-a-real-tool-xyz"]))
    assert main([], cwd=fw) == 1
    out = capsys.readouterr().out
    assert "[FAIL] definitely-not-a-real-tool-xyz" in out
    assert "check skipped" in out and "== format" not in out
```

`tests/scripts/test_wrappers.py`:

```python
import shutil
import subprocess
import sys

import pytest

from helpers import SCRIPTS, TEMPLATES, fake_config, git, make_fixture_repo, write_config


@pytest.fixture
def installed(tmp_path):
    repo = make_fixture_repo(tmp_path / "fw")
    shutil.copytree(SCRIPTS, repo / "harness" / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(TEMPLATES / ".githooks", repo / ".githooks")
    for name in ("Makefile", "init.sh", "init.ps1"):
        shutil.copy(TEMPLATES / name, repo / name)
    write_config(repo, fake_config())
    git(repo, "config", "core.hooksPath", ".githooks")
    return repo


def run(repo, argv):
    return subprocess.run(argv, cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace")


@pytest.mark.skipif(shutil.which("sh") is None, reason="needs a POSIX sh on PATH")
def test_init_sh(installed):
    result = run(installed, ["sh", "init.sh"])
    assert result.returncode == 0, result.stdout + result.stderr
    assert "check 7/7 passed" in result.stdout


@pytest.mark.skipif(shutil.which("pwsh") is None and shutil.which("powershell") is None,
                    reason="needs PowerShell")
def test_init_ps1(installed):
    shell = shutil.which("pwsh") or shutil.which("powershell")
    result = run(installed, [shell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "init.ps1"])
    assert result.returncode == 0, result.stdout + result.stderr
    assert "check 7/7 passed" in result.stdout


@pytest.mark.skipif(shutil.which("make") is None, reason="needs make")
def test_make_check(installed):
    result = run(installed, ["make", "check", f"PYTHON={sys.executable}"])
    assert result.returncode == 0, result.stdout + result.stderr
    assert "check 7/7 passed" in result.stdout
```

- [ ] **Step 2: Run them and watch them fail**

Run: `py -3 -m pytest tests/scripts/test_init_check.py tests/scripts/test_wrappers.py`
Expected: FAIL, `ModuleNotFoundError: No module named 'init_check'`

- [ ] **Step 3: Implement `init_check.py`**

`SCRIPTS/init_check.py`:

```python
"""init (spec section 4.2): verify the environment at session start. It verifies and never installs anything."""
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import check
from arch_check import ArchitectureError, load_architecture
from console import use_utf8_stdio
from gitutil import git, repo_root
from harness_config import ConfigError, load_config
from identity import IdentityError, current_identity

REQUIRED_FILES = ("harness/config.json", "harness/architecture.json", "harness/cppcheck-suppressions.txt")
REQUIRED_DIRS = ("harness/tickets",)
MIN_PYTHON = (3, 9)


def check_python():
    version = ".".join(str(part) for part in sys.version_info[:3])
    if sys.version_info < MIN_PYTHON:
        return False, f"Python {version} is too old; 3.9 or newer is required. Fix: install a newer Python 3"
    return True, f"Python {version}"


def check_identity(repo):
    try:
        who = current_identity(repo)
    except IdentityError as exc:
        return False, str(exc)
    return True, f"git identity: {who['name']} <{who['email']}>"


def check_hooks_path(repo):
    value = git(repo, "config", "core.hooksPath", check=False)
    if value != ".githooks":
        return False, (f"core.hooksPath is {value!r}, so the harness git hooks do not run. "
                       "Fix: git config core.hooksPath .githooks")
    return True, "git hooks: core.hooksPath is .githooks"


def check_layout(repo):
    problems = [f"{path} is missing" for path in REQUIRED_FILES if not (Path(repo) / path).is_file()]
    problems += [f"{path}/ is missing" for path in REQUIRED_DIRS if not (Path(repo) / path).is_dir()]
    if not problems:
        for loader, error_type in ((load_config, ConfigError), (load_architecture, ArchitectureError)):
            try:
                loader(repo)
            except error_type as exc:
                problems.append(str(exc))
    if problems:
        return False, ("harness layout problems: " + "; ".join(problems)
                       + ". Fix: run fw-harness-init or restore the files from git")
    return True, "harness layout and JSON files valid"


def tool_versions(repo, tools):
    results = []
    for tool in tools:
        if shutil.which(tool) is None:
            results.append((False, f"{tool} not found on PATH. Fix: install it (init never installs tools)"))
            continue
        try:
            proc = subprocess.run([tool, "--version"], cwd=repo, capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", timeout=30)
        except subprocess.TimeoutExpired:
            results.append((False, f"{tool} --version did not finish within 30 s. Fix: check the tool installation"))
            continue
        lines = [line.strip() for line in (proc.stdout + proc.stderr).splitlines() if line.strip()]
        results.append((True, f"{tool}: {lines[0] if lines else 'version unknown'}"))
    return results


def main(argv=None, cwd=None):
    use_utf8_stdio()
    repo = repo_root(cwd or Path.cwd())
    lines = []

    def log(line):
        print(line)
        lines.append(line)

    results = [check_python(), check_identity(repo), check_hooks_path(repo), check_layout(repo)]
    if results[-1][0]:
        results += tool_versions(repo, load_config(repo)["required_tools"])
    for ok, message in results:
        log(f"[{'ok' if ok else 'FAIL'}] {message}")

    if all(ok for ok, _ in results):
        log("Running check...")
        code = check.main([], cwd=repo)
    else:
        log("check skipped: fix the [FAIL] items above first")
        code = 1

    log_dir = repo / check.LOG_DIR
    log_dir.mkdir(exist_ok=True)
    (log_dir / f"init-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 4: Create the wrappers**

`TEMPLATES/Makefile` (recipe lines start with a tab):

```make
# Thin wrapper: all gate logic lives in harness/scripts/check.py. Add no flags here.
PYTHON ?= python3

.PHONY: check init
check:
	$(PYTHON) harness/scripts/check.py

init:
	$(PYTHON) harness/scripts/init_check.py
```

`TEMPLATES/init.sh`:

```sh
#!/bin/sh
# Thin wrapper around harness/scripts/init_check.py. It verifies the environment and installs nothing.
cd "$(dirname "$0")" || exit 1
. ./.githooks/_python.sh
PY=$(harness_python) || { echo "init: Python 3.9+ not found. Fix: install Python 3 (on Windows, the py launcher)" >&2; exit 1; }
exec $PY harness/scripts/init_check.py "$@"
```

`TEMPLATES/init.ps1`:

```powershell
# Thin wrapper around harness/scripts/init_check.py. It verifies the environment and installs nothing.
Set-Location -LiteralPath $PSScriptRoot
foreach ($candidate in @('py -3', 'python3', 'python')) {
    $parts = $candidate -split ' '
    $exe = $parts[0]
    $rest = @($parts | Select-Object -Skip 1)
    if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) { continue }
    & $exe @rest -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" 2>$null
    if ($LASTEXITCODE -ne 0) { continue }
    & $exe @rest harness/scripts/init_check.py @args
    exit $LASTEXITCODE
}
[Console]::Error.WriteLine('init: Python 3.9+ not found. Fix: install Python 3 from python.org (it includes the py launcher)')
exit 1
```

Mark `init.sh` executable in git:

```bash
git add plugins/fw-c-harness/skills/fw-harness-init/templates/init.sh
git update-index --chmod=+x plugins/fw-c-harness/skills/fw-harness-init/templates/init.sh
```

- [ ] **Step 5: Run the tests and watch them pass**

Run: `py -3 -m pytest tests/scripts/test_init_check.py tests/scripts/test_wrappers.py -rs`
Expected: `8 passed` from `test_init_check.py`; each wrapper test passes or is skipped with its reason (on Windows without `sh` or `make` on PATH, `test_init_ps1` passes and the other two skip). Report which ones skipped.

- [ ] **Step 6: Run the whole suite and the completion checks**

Run: `py -3 -m pytest -rs`
Expected: `165 passed` plus up to 3 wrapper tests passed or skipped (80 from plan 1, 88 from this plan, 85 of which never skip).

Run: `py -3 -c "import ast,sys,pathlib; p=pathlib.Path(sys.argv[1]); mods={(n.names[0].name if isinstance(n,ast.Import) else (n.module or '')).split('.')[0] for f in p.glob('*.py') for n in ast.walk(ast.parse(f.read_text(encoding='utf-8'))) if isinstance(n,(ast.Import,ast.ImportFrom))}; local={f.stem for f in p.glob('*.py')}; print(sorted(m for m in mods-local if m not in sys.stdlib_module_names))" plugins/fw-c-harness/skills/fw-harness-init/templates/harness/scripts`
Expected: `[]`

Search for Chinese characters outside `docs/` (Grep tool, pattern `[\p{Han}]`, glob `!docs/**`).
Expected: no matches.

- [ ] **Step 7: Commit**

```bash
git add tests plugins
git commit -m "Add init environment check and Makefile, init.sh, init.ps1 wrappers"
```

---

## Completion Criteria

- `py -3 -m pytest -rs` passes: 165 tests always run and pass; the 3 wrapper tests each pass or skip with a stated reason.
- Scripts import only the standard library.
- No Chinese characters outside `docs/`.
- `check.py` is the only place gate logic lives; `Makefile`, `init.sh`, and `init.ps1` contain no flags beyond calling the scripts.

## Left for Later Plans

- Plan 3: the FW repo `.gitignore` template (`feature_list.json`, `.verify_logs/`, `__pycache__/`, `build/`); ARCHITECTURE.md generation and the marked-block consistency row of `arch_check` (spec section 6.3); setting `core.hooksPath` during init; `extraKnownMarketplaces`; end-to-end test that builds the sample firmware with a real toolchain when one is available (skipped otherwise), which needs `CMakeLists.txt`, `CMakePresets.json`, and Unity added to the fixture.
- Plan 4: `fw-session-start` runs `init`; `fw-c-implement` records evidence with `check.py --record`.
