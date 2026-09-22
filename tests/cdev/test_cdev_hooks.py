"""The hooks answer VS Code, so they always print valid JSON and never stop a session."""
import json
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[2] / "plugins" / "cdev" / "skills" / "cdev-init" / "templates" / "tools"
sys.path.insert(0, str(TOOLS))

import feature  # noqa: E402
import hooks  # noqa: E402

PROGRESS = """# Progress

## Now

- Feature: F-001
- Confirmed facts: the retry fires after 3 ms
- Next step: measure it on the board

## Log

### 2026-09-22

- something older
"""
ROOT_DOC = "# Architecture\n\n## Map\n\n| [src](src/ARCHITECTURE.md) | code |\n"
FOLDER_DOC = "# src\n\n## Files\n\n- `main.c`: entry\n"


def write(root, name, text=""):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def repo(tmp_path):
    write(tmp_path, "PROGRESS.md", PROGRESS)
    write(tmp_path, "ARCHITECTURE.md", ROOT_DOC)
    write(tmp_path, "src/ARCHITECTURE.md", FOLDER_DOC)
    write(tmp_path, "src/main.c")
    feature.main(["--file", str(tmp_path / "feature_list.json"), "add",
                  "--title", "retry on timeout", "--status", "active"], today="2026-09-22")
    return tmp_path


def run(event, root, capsys):
    assert hooks.main([event, "--root", str(root)]) == 0
    return json.loads(capsys.readouterr().out)


def test_session_start_hands_over_the_state(repo, capsys):
    context = run("session-start", repo, capsys)["hookSpecificOutput"]["additionalContext"]
    assert "F-001" in context and "retry on timeout" in context
    assert "the retry fires after 3 ms" in context
    assert "measure it on the board" in context
    assert "the architecture documents match the files" in context
    assert "## Log" not in context, "only ## Now belongs in the opening context"


def test_session_start_names_the_event(repo, capsys):
    assert run("session-start", repo, capsys)["hookSpecificOutput"]["hookEventName"] == "SessionStart"


def test_session_start_reports_drift_and_stubs(repo, capsys):
    write(repo, "src/extra.c")
    write(repo, "lib/ARCHITECTURE.md", "# lib\n\n## Files\n\nNot documented yet.\n")
    context = run("session-start", repo, capsys)["hookSpecificOutput"]["additionalContext"]
    assert "drift" in context and "not documented yet: lib" in context


def test_a_repository_without_the_harness_still_answers(tmp_path, capsys):
    context = run("session-start", tmp_path, capsys)["hookSpecificOutput"]["additionalContext"]
    assert "PROGRESS.md is missing" in context and "feature_list.json is missing" in context


def test_stop_warns_only_when_the_documents_drifted(repo, capsys):
    assert "systemMessage" not in run("stop", repo, capsys)
    write(repo, "src/extra.c")
    answer = run("stop", repo, capsys)
    assert answer["continue"] is True
    assert "cdev-architecture-sync" in answer["systemMessage"]


def test_a_broken_progress_file_does_not_stop_the_session(repo, capsys):
    write(repo, "PROGRESS.md", "# Progress\n\nno sections here\n")
    context = run("session-start", repo, capsys)["hookSpecificOutput"]["additionalContext"]
    assert "cdev-upgrade" in context


def test_the_context_stays_small(repo, capsys):
    write(repo, "PROGRESS.md", PROGRESS.replace("## Log", "x " * 20000 + "\n## Log"))
    context = run("session-start", repo, capsys)["hookSpecificOutput"]["additionalContext"]
    assert len(context) <= hooks.LIMIT
