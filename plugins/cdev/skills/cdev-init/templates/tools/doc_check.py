"""Report where the architecture documents have drifted from the files. Reports only; blocks nothing."""
import argparse
import fnmatch
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import unquote

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
DOC = "ARCHITECTURE.md"
UNLISTED = {DOC, "AGENTS.md"}
FILE_LINE_RE = re.compile(r"^\s*[-*]\s+`([^`]+)`")
STUB = "Not documented yet"
# [x](a/ARCHITECTURE.md), [x](./a/ARCHITECTURE.md), [x](<a b/ARCHITECTURE.md>) or [x](a%20b/ARCHITECTURE.md)
LINK_RE = re.compile(r"\]\(\s*(?:<([^>]*ARCHITECTURE\.md)>|([^)#\s]*ARCHITECTURE\.md))")
NOTES = "NOTES.md"
NOTES_DIR = "docs/notes"
NOTE_LINK_RE = re.compile(r"\]\(\s*(?:<(?:\./)?(docs/notes/[^>]+\.md)>|(?:\./)?(docs/notes/[^)#\s]+\.md))")


def repository_files(root):
    """Every file git would show (tracked or untracked, not ignored), including those of checked-out
    submodules, or every file outside dot folders. A submodule worked in here is documented like any
    folder, so its files are part of what the documents must match."""
    root = Path(root)
    found = own_files(root)
    for module in submodules(root):
        if (root / module / ".git").exists():
            found += [f"{module}/{name}" for name in own_files(root / module)]
    return sorted(set(found))


def personal_markdown(root):
    """Markdown a personal harness keeps out of commits through info/exclude (tools/personal.py).
    Hidden from git's usual listing, it is still the documents this check compares."""
    try:
        where = subprocess.run(["git", "rev-parse", "--git-path", "info/exclude"], cwd=root, capture_output=True)
        exclude = Path(where.stdout.decode("utf-8").strip())
        exclude = exclude if exclude.is_absolute() else Path(root) / exclude
        if where.returncode != 0 or not exclude.is_file():
            return []
        result = subprocess.run(["git", "ls-files", "--others", "--ignored", f"--exclude-from={exclude}", "-z",
                                 "--", "*.md"], cwd=root, capture_output=True)
    except OSError:
        return []
    return result.stdout.decode("utf-8").split("\0") if result.returncode == 0 else []


def own_files(root):
    root = Path(root)
    if (root / ".git").exists():
        try:
            result = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
                                    cwd=root, capture_output=True)
        except OSError:  # git is not on PATH; walk the tree instead
            result = None
        if result is not None and result.returncode == 0:
            names = result.stdout.decode("utf-8").split("\0")
            names += personal_markdown(root)
            return sorted({name for name in names if name and (root / name).is_file()})
    found = []
    for folder, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for name in files:
            found.append((Path(folder) / name).relative_to(root).as_posix())
    return sorted(found)


def read(path):
    """Text of a file whatever its encoding: a BOM is dropped and bytes that are not UTF-8 are replaced."""
    return Path(path).read_text(encoding="utf-8-sig", errors="replace")


def section(text, heading):
    lines = text.splitlines()
    start = next((i + 1 for i, line in enumerate(lines) if line.strip() == heading), None)
    if start is None:
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


def matches(name, pattern):
    """A pattern with * or ? is a glob; anything else, such as foo[1].c, is a file name."""
    if "*" in pattern or "?" in pattern:
        return fnmatch.fnmatchcase(name, pattern)
    return name == pattern


def linked_documents(text):
    links = set()
    for bracketed, plain in LINK_RE.findall(text):
        link = unquote(bracketed or plain)
        links.add(PurePosixPath(link[2:] if link.startswith("./") else link).as_posix())
    return links


def submodules(root):
    """The submodule paths .gitmodules declares. Their files belong to their own repositories, so this
    repository documents them only as rows in the root map, never with files inside them."""
    path = Path(root) / ".gitmodules"
    if not path.is_file():
        return []
    found = re.findall(r"^\s*path\s*=\s*(.+?)\s*$", read(path), re.MULTILINE)
    return [PurePosixPath(p.replace("\\", "/")).as_posix() for p in found]


def note_problems(root, files):
    """NOTES.md links a note that is gone, or a note in docs/notes/ has no line in NOTES.md."""
    notes = [name for name in files if name.startswith(NOTES_DIR + "/") and name.endswith(".md")]
    index = Path(root) / NOTES
    if not index.is_file():
        return [f"{NOTES} is missing, so {len(notes)} note(s) in {NOTES_DIR}/ have no index"] if notes else []
    linked = {unquote(bracketed or plain) for bracketed, plain in NOTE_LINK_RE.findall(read(index))}
    problems = [f"{NOTES}: links {link}, which does not exist" for link in sorted(linked) if link not in files]
    problems += [f"{NOTES}: {name} has no line" for name in notes if name not in linked]
    return problems


def check(root):
    root = Path(root)
    files = repository_files(root)
    problems = []
    waiting = []
    folder_docs = [name for name in files if PurePosixPath(name).name == DOC and "/" in name]
    for doc in folder_docs:
        folder = str(PurePosixPath(doc).parent)
        patterns = listed_patterns(read(root / doc))
        if patterns is None:
            problems.append(f"{doc}: has no ## Files section")
            continue
        if patterns == STUB:
            waiting.append(folder)
            continue
        present = [PurePosixPath(name).name for name in files
                   if str(PurePosixPath(name).parent) == folder and PurePosixPath(name).name not in UNLISTED]
        for pattern in patterns:
            if not any(matches(name, pattern) for name in present):
                problems.append(f"{doc}: lists {pattern}, which is not in {folder}/")
        for name in present:
            if not any(matches(name, pattern) for pattern in patterns):
                problems.append(f"{doc}: {folder}/{name} is not listed")

    root_doc = root / DOC
    if not root_doc.is_file():
        problems.append(f"{DOC} is missing at the repository root")
    else:
        text = read(root_doc)
        linked = linked_documents(text)
        modules = submodules(root)
        for link in sorted(linked):
            if link not in files:
                problems.append(f"{DOC}: the map links {link}, which does not exist")
        for doc in folder_docs:
            if doc not in linked:
                problems.append(f"{DOC}: the map does not link {doc}")
        for path in modules:
            if not re.search(r"(?<![\w/.-])" + re.escape(path) + r"(?![\w.-])", text):
                problems.append(f"{DOC}: the map does not mention the submodule {path}")
    problems += note_problems(root, files)
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
