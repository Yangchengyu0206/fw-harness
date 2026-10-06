"""Keep a personal harness out of every commit, while the team does not share it yet.

Adds `*.md` to `.git/info/exclude` of this repository and of every checked-out submodule, and the
harness's other files (its scripts, feature list, hook, and editor settings) to this repository's.
That file is local to this clone: it is never committed or pushed, so no repository changes for it,
and a file already tracked (a README) stays tracked. Safe to run again; --check only reports.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
PATTERN = "*.md"
# the harness's files that are not markdown, excluded in the repository it was set up in
ROOT_PATTERNS = ("/feature_list.json", "/tools/feature.py", "/tools/doc_check.py", "/tools/hooks.py",
                 "/tools/mcp_list.py", "/tools/value_check.py", "/tools/personal.py", "/tools/__pycache__/",
                 "/.github/hooks/cdev.json", "/.vscode/settings.json")
HEADER = "# cdev personal harness: these stay on this machine"


def exclude_file(repo):
    """The info/exclude path git uses for this repository or submodule, or None outside git."""
    try:
        result = subprocess.run(["git", "rev-parse", "--git-path", "info/exclude"], cwd=repo, capture_output=True)
    except OSError:
        return None
    if result.returncode != 0:
        return None
    path = Path(result.stdout.decode("utf-8").strip())
    return path if path.is_absolute() else Path(repo) / path


def submodules(root):
    path = Path(root) / ".gitmodules"
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    return [p.replace("\\", "/").strip("/") for p in re.findall(r"^\s*path\s*=\s*(.+?)\s*$", text, re.MULTILINE)]


def repositories(root):
    root = Path(root)
    found = [(".", root)]
    for module in submodules(root):
        if (root / module / ".git").exists():
            found.append((module, root / module))
    return found


def wanted(name):
    return (PATTERN,) + (ROOT_PATTERNS if name == "." else ())


def lines_of(path):
    return path.read_text(encoding="utf-8", errors="replace").splitlines() if path.is_file() else []


def excluded(path, patterns=(PATTERN,)):
    have = lines_of(path)
    return all(pattern in have for pattern in patterns)


def ensure(root, check=False):
    """[(name, state)] with state one of: set, already, missing, not a repository."""
    states = []
    for name, repo in repositories(root):
        path = exclude_file(repo)
        if path is None:
            states.append((name, "not a repository"))
            continue
        have = lines_of(path)
        add = [pattern for pattern in wanted(name) if pattern not in have]
        if not add:
            states.append((name, "already"))
        elif check:
            states.append((name, "missing"))
        else:
            if HEADER not in have:
                add.insert(0, HEADER)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "a", encoding="utf-8", newline="\n") as f:
                if have and not path.read_text(encoding="utf-8", errors="replace").endswith("\n"):
                    f.write("\n")
                f.write("\n".join(add) + "\n")
            states.append((name, "set"))
    return states


def share(root):
    """Undo ensure: take out only the lines it added, so the harness's files can be committed for the team."""
    states = []
    ours = {HEADER, PATTERN, *ROOT_PATTERNS}
    for name, repo in repositories(root):
        path = exclude_file(repo)
        have = lines_of(path) if path else []
        kept = [line for line in have if line not in ours]
        if path is None or kept == have:
            states.append((name, "nothing to remove"))
            continue
        path.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8", newline="\n")
        states.append((name, "removed"))
    return states


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(prog="personal.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=str(DEFAULT_ROOT))
    parser.add_argument("--check", action="store_true", help="report only; change nothing")
    parser.add_argument("--team", action="store_true",
                        help="share the harness: remove these lines again, so its files can be committed")
    args = parser.parse_args(argv)
    if args.team:
        for name, state in share(args.root):
            print(f"- {name}: {state}")
        print("personal: the harness's files can now be committed. Set `Sharing: team` in AGENTS.md, "
              "then add and commit them, in each edited submodule first")
        return 0
    states = ensure(args.root, check=args.check)
    for name, state in states:
        print(f"- {name}: {state}")
    missing = [name for name, state in states if state == "missing"]
    if missing:
        print(f"personal: the harness can still be committed in {', '.join(missing)}. Fix: py -3 tools/personal.py")
        return 1
    print("personal: the harness in this repository and its submodules stays out of commits")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
