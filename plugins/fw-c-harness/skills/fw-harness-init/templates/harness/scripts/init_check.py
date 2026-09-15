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
    log_file = log_dir / f"init-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
    log_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
