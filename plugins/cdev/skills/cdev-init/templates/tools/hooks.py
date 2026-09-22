"""Answer the agent hooks in .github/hooks/cdev.json. Never blocks; a failure here stays out of the way.

  session-start   put where the work stands in front of the agent before its first answer
  stop            say whether the architecture documents drifted during the session
"""
import argparse
import io
import json
import sys
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

LIMIT = 4000


def read_stdin():
    try:
        raw = sys.stdin.read()
    except (OSError, ValueError):
        return {}
    try:
        return json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return {}


def now_section(root):
    path = Path(root) / "PROGRESS.md"
    if not path.is_file():
        return "PROGRESS.md is missing. Fix: run cdev-init."
    lines = path.read_text(encoding="utf-8").splitlines()
    try:
        start = lines.index("## Now")
    except ValueError:
        return "PROGRESS.md has no ## Now section. Fix: run cdev-upgrade."
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return "\n".join(lines[start:end]).strip()


def feature_lines(root):
    try:
        import feature
    except ImportError:
        return "tools/feature.py is missing. Fix: run cdev-upgrade."
    path = Path(root) / "feature_list.json"
    if not path.is_file():
        return "feature_list.json is missing. Fix: run cdev-init."
    out = io.StringIO()
    stdout, sys.stdout = sys.stdout, out
    try:
        feature.main(["--file", str(path), "show"])
    except BaseException:
        return "feature.py could not read feature_list.json. Fix: run py -3 tools/feature.py check."
    finally:
        sys.stdout = stdout
    return out.getvalue().strip() or "no features"


def documents(root):
    try:
        import doc_check
    except ImportError:
        return "tools/doc_check.py is missing. Fix: run cdev-upgrade."
    try:
        problems, waiting = doc_check.check(root)
    except BaseException as exc:
        return f"doc_check could not run ({exc})."
    parts = []
    if problems:
        parts.append(f"{len(problems)} drift(s): " + "; ".join(problems[:5]))
    if waiting:
        parts.append(f"not documented yet: {', '.join(waiting)}")
    return "\n".join(parts) if parts else "the architecture documents match the files"


def session_context(root):
    text = (
        "The cdev harness reports where this repository's work stands. "
        "Use it instead of reading PROGRESS.md and the feature list again, and ask the user "
        "which feature to take before writing code.\n\n"
        f"{now_section(root)}\n\n"
        f"## Features\n\n{feature_lines(root)}\n\n"
        f"## Architecture documents\n\n{documents(root)}"
    )
    return text[:LIMIT]


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(prog="hooks.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("event", choices=("session-start", "stop"))
    parser.add_argument("--root", default=str(DEFAULT_ROOT))
    args = parser.parse_args(argv)
    read_stdin()

    try:
        if args.event == "session-start":
            answer = {"hookSpecificOutput": {"hookEventName": "SessionStart",
                                             "additionalContext": session_context(args.root)}}
        else:
            summary = documents(args.root)
            answer = {"continue": True}
            if "drift" in summary:
                answer["systemMessage"] = (
                    f"cdev: {summary}. Fix: update the documents, or run cdev-architecture-sync.")
    except BaseException as exc:  # a hook that fails stays out of the way
        answer = {"continue": True, "systemMessage": f"cdev hook failed: {exc}"}

    print(json.dumps(answer, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
