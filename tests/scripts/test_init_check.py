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
