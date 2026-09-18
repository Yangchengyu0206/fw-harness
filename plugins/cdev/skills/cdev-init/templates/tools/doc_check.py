"""Report where the architecture documents have drifted from the files. Reports only; blocks nothing."""
import argparse
import fnmatch
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
DOC = "ARCHITECTURE.md"
UNLISTED = {DOC, "AGENTS.md"}
FILE_LINE_RE = re.compile(r"^\s*[-*]\s+`([^`]+)`")
STUB = "Not documented yet"
LINK_RE = re.compile(r"\]\(([^)#\s]*ARCHITECTURE\.md)\)")


def repository_files(root):
    """Every file git would show (tracked or untracked, not ignored), or every file outside dot folders."""
    root = Path(root)
    if (root / ".git").exists():
        result = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
                                cwd=root, capture_output=True)
        if result.returncode == 0:
            names = result.stdout.decode("utf-8").split("\0")
            return sorted({name for name in names if name and (root / name).is_file()})
    found = []
    for folder, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for name in files:
            found.append((Path(folder) / name).relative_to(root).as_posix())
    return sorted(found)


def section(text, heading):
    lines = text.splitlines()
    try:
        start = lines.index(heading) + 1
    except ValueError:
        return None
    end = next((i for i in range(start, len(lines)) if lines[i].startswith("## ")), len(lines))
    return lines[start:end]


def listed_patterns(text):
    """The globs a document lists, None when it has no ## Files, or STUB when the folder is not documented yet."""
    lines = section(text, "## Files")
    if lines is None:
        return None
    if any(STUB in line for line in lines):
        return STUB
    return [match.group(1) for match in map(FILE_LINE_RE.match, lines) if match]


def check(root):
    root = Path(root)
    files = repository_files(root)
    problems = []
    waiting = []
    folder_docs = [name for name in files if PurePosixPath(name).name == DOC and "/" in name]

    for doc in folder_docs:
        folder = str(PurePosixPath(doc).parent)
        patterns = listed_patterns((root / doc).read_text(encoding="utf-8"))
        if patterns is None:
            problems.append(f"{doc}: has no ## Files section")
            continue
        if patterns == STUB:
            waiting.append(folder)
            continue
        present = [PurePosixPath(name).name for name in files
                   if str(PurePosixPath(name).parent) == folder and PurePosixPath(name).name not in UNLISTED]
        for pattern in patterns:
            if not fnmatch.filter(present, pattern):
                problems.append(f"{doc}: lists {pattern}, which is not in {folder}/")
        for name in present:
            if not any(fnmatch.fnmatch(name, pattern) for pattern in patterns):
                problems.append(f"{doc}: {folder}/{name} is not listed")

    root_doc = root / DOC
    if not root_doc.is_file():
        problems.append(f"{DOC} is missing at the repository root")
    else:
        linked = {PurePosixPath(link).as_posix() for link in LINK_RE.findall(root_doc.read_text(encoding="utf-8"))}
        for link in sorted(linked):
            if link not in files:
                problems.append(f"{DOC}: the map links {link}, which does not exist")
        for doc in folder_docs:
            if doc not in linked:
                problems.append(f"{DOC}: the map does not link {doc}")
    return problems, sorted(waiting)


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(prog="doc_check.py", description=__doc__)
    parser.add_argument("--root", default=str(DEFAULT_ROOT), help="repository root")
    args = parser.parse_args(argv)
    problems, waiting = check(args.root)
    if waiting:
        print(f"doc_check: {len(waiting)} folder(s) not documented yet: {', '.join(waiting)}")
        print("  Fix: run cdev-architecture-sync for a folder before working in it or answering about it")
    if not problems:
        print("doc_check: the architecture documents match the files")
        return 0
    print(f"doc_check: {len(problems)} drift(s). Fix: update the documents, or run cdev-architecture-sync")
    for problem in problems:
        print(f"- {problem}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
