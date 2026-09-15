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
