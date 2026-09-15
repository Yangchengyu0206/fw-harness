import pytest

from check import main, summarize
from helpers import PY, commit_all, fake_config, git, make_fixture_repo, write_config
from steps import StepResult
from tickets import load_ticket, new_ticket, save_ticket
from transitions import transition

NOW = "2026-09-15T10:00:00+08:00"
ALICE = {"name": "Alice Chen", "email": "alice@example.com"}
FAIL = [PY, "-c", "import sys; print('boom'); sys.exit(1)"]


@pytest.fixture
def fw(tmp_path):
    repo = make_fixture_repo(tmp_path / "fw")
    write_config(repo, fake_config())
    return repo


def run(repo, *argv):
    return main(list(argv), cwd=repo, now=NOW)


def test_all_steps_pass_and_log_is_written(fw, capsys):
    assert run(fw) == 0
    assert "check 7/7 passed" in capsys.readouterr().out
    logs = list((fw / ".verify_logs").glob("check-*.log"))
    assert len(logs) == 1 and "check 7/7 passed" in logs[0].read_text(encoding="utf-8")
    assert git(fw, "status", "--porcelain") == ""


def test_stops_at_first_failure(fw, capsys):
    write_config(fw, fake_config(build={"commands": [FAIL]}))
    assert run(fw) == 1
    out = capsys.readouterr().out
    assert "check failed at build (4/7 passed)" in out
    assert "boom" in out and "== test" not in out


def test_missing_tool_fails_its_step(fw, capsys):
    write_config(fw, fake_config(cppcheck={"command": ["definitely-not-a-real-tool-xyz"], "paths": ["src"]}))
    assert run(fw) == 1
    out = capsys.readouterr().out
    assert "check failed at cppcheck" in out and "not found on PATH" in out


def test_size_over_budget_fails_the_last_step(fw, capsys):
    size = fake_config()["check"]["size"]
    write_config(fw, fake_config(size=dict(size, flash_budget=10)))
    assert run(fw) == 1
    assert "check failed at size (6/7 passed)" in capsys.readouterr().out


def test_missing_config(tmp_path, capsys):
    repo = make_fixture_repo(tmp_path / "noconfig")
    assert run(repo) == 1
    assert "harness/config.json not found" in capsys.readouterr().err


def test_summarize():
    names = ("format", "cppcheck", "arch", "tickets", "build", "test", "size")
    passing = [StepResult(name, True, "") for name in names]
    assert summarize(passing) == ("check 7/7 passed", True)
    assert summarize(passing[:3] + [StepResult("tickets", False, "")]) == ("check failed at tickets (3/7 passed)", False)


def open_active_ticket(repo):
    ticket = new_ticket("FW-0001", "UART DMA", "drivers/uart", ALICE, NOW)
    ticket = transition(repo, transition(repo, ticket, "next", ALICE, NOW), "active", ALICE, NOW)
    save_ticket(repo, ticket)
    commit_all(repo, "FW-0001 claim")


def test_record_needs_clean_tree(fw, capsys):
    open_active_ticket(fw)
    (fw / "src" / "app" / "main.c").write_text("int main(void) { return 0; }\n", encoding="utf-8")
    assert run(fw, "--record", "FW-0001") == 1
    assert "clean working tree" in capsys.readouterr().err
    assert load_ticket(fw, "FW-0001")["evidence"] == []


def test_record_passing_check_enables_verifying(fw):
    open_active_ticket(fw)
    assert run(fw, "--record", "FW-0001") == 0
    evidence = load_ticket(fw, "FW-0001")["evidence"][-1]
    assert evidence["passed"] is True and evidence["summary"] == "check 7/7 passed"
    assert evidence["by"] == ALICE and evidence["commit"] == git(fw, "rev-parse", "HEAD")[:10]
    assert transition(fw, load_ticket(fw, "FW-0001"), "verifying", ALICE, NOW)["status"] == "verifying"


def test_record_failing_check(fw):
    open_active_ticket(fw)
    write_config(fw, fake_config(test={"commands": [FAIL]}))
    assert run(fw, "--record", "FW-0001") == 1
    evidence = load_ticket(fw, "FW-0001")["evidence"][-1]
    assert evidence["passed"] is False and evidence["summary"] == "check failed at test (5/7 passed)"


def test_record_unknown_ticket(fw, capsys):
    assert run(fw, "--record", "FW-0099") == 1
    assert "FW-0099" in capsys.readouterr().err
