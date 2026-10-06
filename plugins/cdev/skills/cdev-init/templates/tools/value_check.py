"""Report hardware values added since the last commit that name no source. Reports only; blocks nothing.

A register address, a bit mask, or a timing written as a hex constant in C has to come from a
datasheet, an application note, or the user. This finds the ones added without saying which:
a `#define NAME 0x..` or an `enum` member `NAME = 0x..` with no source marker on its line or the
line above. An agent that could not look a value up marks it `/* UNVERIFIED: <what to check> */`,
which this accepts, so the reader can tell a looked-up value from a guess.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
C_SUFFIXES = (".c", ".h", ".cpp", ".hpp", ".cc", ".hh")
# `#define NAME 0x..` anywhere, or an enum member `NAME = 0x..,` (a statement ending in `;` is not one)
VALUE_RE = re.compile(r"^\s*(?:#\s*define\s+(\w+)\s+\(?\s*(0[xX][0-9A-Fa-f]+)"
                      r"|(\w+)\s*=\s*(0[xX][0-9A-Fa-f]+)\w*\s*,?\s*(?:/[/*].*)?$)")
SOURCE_RE = re.compile(
    r"UNVERIFIED|datasheet|data sheet|app(?:lication)?[ -]?note|AP[- ]?note|errata|"
    r"\btable\s*[\w.-]+|\bp(?:age|\.)\s*\d+|\bsec(?:tion)?\.?\s*\d+|§\s*\d+|\bref(?:erence)?\s*manual\b|\brev\.?\s*[A-Z0-9]",
    re.IGNORECASE)


def git(root, *args):
    try:
        result = subprocess.run(["git", *args], cwd=root, capture_output=True)
    except OSError:
        return None
    return result.stdout.decode("utf-8", "replace") if result.returncode == 0 else None


def added_lines(root):
    """{path: [(line number, text, text of the line above)]} for C files changed since HEAD."""
    found = {}
    diff = git(root, "diff", "HEAD", "--unified=1", "--no-color", "--", *[f"*{s}" for s in C_SUFFIXES])
    if diff is None:
        diff = git(root, "diff", "--unified=1", "--no-color") or ""
    path, number, previous = None, 0, ""
    for line in diff.splitlines():
        if line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else None
        elif line.startswith("@@"):
            match = re.search(r"\+(\d+)", line)
            number, previous = (int(match.group(1)) if match else 1), ""
        elif path and line.startswith("+"):
            found.setdefault(path, []).append((number, line[1:], previous))
            previous, number = line[1:], number + 1
        elif path and line.startswith(" "):
            previous, number = line[1:], number + 1
    untracked = git(root, "ls-files", "--others", "--exclude-standard") or ""
    for name in untracked.splitlines():
        if name.endswith(C_SUFFIXES) and (Path(root) / name).is_file():
            text = (Path(root) / name).read_text(encoding="utf-8", errors="replace").splitlines()
            found[name] = [(i + 1, t, text[i - 1] if i else "") for i, t in enumerate(text)]
    return found


def submodules(root):
    """Submodule paths from .gitmodules; most of a project's edits can happen inside one."""
    path = Path(root) / ".gitmodules"
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    return [p.replace("\\", "/").strip("/") for p in re.findall(r"^\s*path\s*=\s*(.+?)\s*$", text, re.MULTILINE)]


def all_added_lines(root):
    """added_lines for this repository and for each checked-out submodule, keyed by path from the root."""
    found = added_lines(root)
    for module in submodules(root):
        if (Path(root) / module / ".git").exists():
            for path, lines in added_lines(Path(root) / module).items():
                found[f"{module}/{path}"] = lines
    return found


def unsourced(root):
    """[(path, line, name, value)] for added hex constants with no source marker."""
    problems = []
    for path, lines in all_added_lines(root).items():
        for number, text, previous in lines:
            match = VALUE_RE.match(text)
            if not match:
                continue
            name = match.group(1) or match.group(3)
            value = match.group(2) or match.group(4)
            # the line above counts only when it is a comment of its own, not another value's trailing note
            above = previous.strip()
            comment_above = above.startswith(("/*", "//", "*"))
            if not (SOURCE_RE.search(text) or (comment_above and SOURCE_RE.search(above))):
                problems.append((path, number, name, value))
    return problems


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(prog="value_check.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=str(DEFAULT_ROOT))
    args = parser.parse_args(argv)
    problems = unsourced(args.root)
    if not problems:
        print("value_check: every hardware value added since the last commit names a source")
        return 0
    print(f"value_check: {len(problems)} hardware value(s) added without a source. "
          "Fix: look each up with a document tool and cite it in a comment, "
          "or mark it /* UNVERIFIED: <what to check> */ and tell the user")
    for path, number, name, value in problems:
        print(f"- {path}:{number} {name} = {value}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
