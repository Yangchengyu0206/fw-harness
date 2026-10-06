"""Answer the agent hooks in .github/hooks/cdev.json. Never blocks; a failure here stays out of the way.

  session-start   put where the work stands in front of the agent before its first answer
  stop            say whether the architecture documents drifted during the session

Safe to run by hand: it does not read stdin, and it always exits 0.
"""
import argparse
import json
import sys
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

LIMIT = 5000
SECTION_LIMIT = 1800
NOTES_LIMIT = 1200
EVENTS = ("session-start", "stop")
# Drift counted at session start, so the stop hook speaks only about drift this session added.
BASELINE = Path(".git") / "cdev-drift-baseline"


def read(path):
    """Text of a file whatever its encoding: a BOM is dropped and bytes that are not UTF-8 are replaced."""
    return Path(path).read_text(encoding="utf-8-sig", errors="replace")


def clip(text, limit=SECTION_LIMIT):
    return text if len(text) <= limit else text[:limit].rstrip() + "\n(truncated)"


def now_section(root):
    path = Path(root) / "PROGRESS.md"
    if not path.is_file():
        return "PROGRESS.md is missing. Fix: run cdev-init."
    lines = read(path).splitlines()
    start = next((i for i, text in enumerate(lines) if text.strip() == "## Now"), None)
    if start is None:
        return "PROGRESS.md has no ## Now section. Fix: run cdev-upgrade."
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return clip("\n".join(lines[start:end]).strip())


def feature_lines(root):
    try:
        import feature
    except ImportError:
        return "tools/feature.py is missing. Fix: run cdev-upgrade."
    path = Path(root) / "feature_list.json"
    if not path.is_file():
        return "feature_list.json is missing. Fix: run cdev-init."
    try:
        data = feature.load(path)
    except feature.FeatureError as exc:
        return clip(f"feature_list.json cannot be read, so the features are unknown, not absent. {exc}\n"
                    "Fix: repair it, then run py -3 tools/feature.py check.")
    items = data["features"]
    return clip("\n".join(feature.line(item) for item in items)) if items else "no features yet"


def notes_index(root):
    """The topic lines of NOTES.md: what the next conversation should know exists, not the notes themselves."""
    path = Path(root) / "NOTES.md"
    if not path.is_file():
        return "NOTES.md is missing. Fix: run cdev-upgrade."
    lines = [line.strip() for line in read(path).splitlines() if line.strip().startswith("- [")]
    if not lines:
        return "no notes yet"
    return clip("Open a note when its line matches the work.\n" + "\n".join(lines), NOTES_LIMIT)


def tool_servers(root):
    """The MCP servers configured here, so the agent knows what to reach for before it answers from memory."""
    try:
        import mcp_list
    except ImportError:
        return "tools/mcp_list.py is missing. Fix: run cdev-upgrade."
    servers = mcp_list.names(root)
    if not servers:
        return "no MCP server is configured for this repository or this machine"
    return clip(f"configured: {', '.join(servers)}. Reach for them first, as `## Tools beyond this repository` "
                "in AGENTS.md says; a server missing from your tool list is configured but not enabled.", 600)


def drift(root):
    """(problems, waiting) from doc_check; raises ImportError when the script is missing."""
    import doc_check
    return doc_check.check(root)


def documents(root):
    try:
        problems, waiting = drift(root)
    except ImportError:
        return "tools/doc_check.py is missing. Fix: run cdev-upgrade."
    remember_baseline(root, len(problems))
    parts = []
    if problems:
        parts.append(f"{len(problems)} drift(s): " + "; ".join(problems[:5]))
    if waiting:
        parts.append(f"not documented yet: {', '.join(waiting)}")
    return clip("\n".join(parts)) if parts else "the architecture documents match the files"


def remember_baseline(root, count):
    path = Path(root) / BASELINE
    if path.parent.is_dir():
        try:
            path.write_text(str(count), encoding="utf-8")
        except OSError:
            pass


def baseline(root):
    try:
        return int((Path(root) / BASELINE).read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return 0


def guarded(section, root):
    """One section's text; its own failure is reported in its place, and the others still arrive."""
    try:
        return section(root)
    except Exception as exc:  # noqa: BLE001 - a hook must never take the session down
        return f"could not be read ({type(exc).__name__}: {exc})"


def session_context(root):
    text = (
        "The cdev harness reports where this repository's work stands. "
        "Use it instead of reading PROGRESS.md and the feature list again. "
        "When the user has not said what to work on, ask which feature to take before writing code.\n\n"
        f"{guarded(now_section, root)}\n\n"
        f"## Features\n\n{guarded(feature_lines, root)}\n\n"
        f"## Notes\n\n{guarded(notes_index, root)}\n\n"
        f"## MCP servers\n\n{guarded(tool_servers, root)}\n\n"
        f"## Architecture documents\n\n{guarded(documents, root)}"
    )
    return text[:LIMIT]


def stop_answer(root):
    answer = {"continue": True}
    try:
        problems, _ = drift(root)
    except Exception:  # noqa: BLE001
        return answer
    if len(problems) > baseline(root):
        answer["systemMessage"] = (f"cdev: the architecture documents drifted this session "
                                   f"({len(problems)} drift(s) now). "
                                   "Fix: update the documents, or run cdev-architecture-sync.")
    return answer


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(prog="hooks.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("event", choices=EVENTS)
    parser.add_argument("--root", default=str(DEFAULT_ROOT))
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        if exc.code == 0:  # --help
            return 0
        # Exit code 2 makes VS Code treat a hook as a blocking error, so answer nothing instead.
        print("{}")
        return 0

    if args.event == "session-start":
        answer = {"hookSpecificOutput": {"hookEventName": "SessionStart",
                                         "additionalContext": session_context(args.root)}}
    else:
        answer = stop_answer(args.root)
    print(json.dumps(answer, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
