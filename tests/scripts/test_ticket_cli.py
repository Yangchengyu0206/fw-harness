import json

import pytest

from helpers import git
from ticket import main
from tickets import load_ticket, make_evidence, save_ticket

NOW = "2026-09-15T10:00:00+08:00"
BOB = {"name": "Bob Lin", "email": "bob@example.com"}


def run(repo, *argv):
    return main(list(argv), cwd=repo, now=NOW, confirm=lambda ticket_id: True)


def test_new_uses_git_identity_and_warns_offline(repo, capsys):
    assert run(repo, "new", "--title", "UART DMA", "--area", "drivers/uart",
               "--step", "on board: loopback", "--dod", "on-board loopback verification") == 0
    out = capsys.readouterr()
    assert "Opened FW-0001" in out.out
    assert "offline" in out.err
    ticket = load_ticket(repo, "FW-0001")
    assert ticket["created_by"] == {"name": "Alice Chen", "email": "alice@example.com"}
    assert ticket["verification_steps"] == ["on board: loopback"]
    assert ticket["requires_hil"] is True


def test_identity_cannot_be_passed_as_argument(repo):
    with pytest.raises(SystemExit):
        run(repo, "new", "--title", "t", "--area", "a", "--by", "bob@example.com")


def test_claim_from_backlog_goes_through_next(repo):
    run(repo, "new", "--title", "t", "--area", "a")
    assert run(repo, "claim", "FW-0001") == 0
    ticket = load_ticket(repo, "FW-0001")
    assert ticket["status"] == "active"
    assert [h["to"] for h in ticket["history"]] == ["backlog", "next", "active"]


def test_move_failure_message(repo, capsys):
    run(repo, "new", "--title", "t", "--area", "a")
    run(repo, "claim", "FW-0001")
    assert run(repo, "move", "FW-0001", "verifying") == 1
    err = capsys.readouterr().err
    assert "ticket.py move failed" in err and "kind: check" in err


def test_check_evidence_resolves_commit_then_verifying(repo, capsys):
    run(repo, "new", "--title", "t", "--area", "a")
    run(repo, "claim", "FW-0001")
    assert run(repo, "evidence", "FW-0001", "check", "--commit", "nope", "--summary", "s", "--passed") == 1
    assert run(repo, "evidence", "FW-0001", "check", "--commit", "HEAD", "--summary", "check 7/7 passed") == 1
    assert "--passed or --failed" in capsys.readouterr().err
    assert run(repo, "evidence", "FW-0001", "check", "--commit", "HEAD", "--summary", "check 7/7 passed", "--passed") == 0
    head = git(repo, "rev-parse", "HEAD")
    evidence = load_ticket(repo, "FW-0001")["evidence"][0]
    assert evidence["commit"] == head[:10] and evidence["passed"] is True
    assert run(repo, "move", "FW-0001", "verifying") == 0


def test_review_evidence_requires_open_critical(repo, capsys):
    run(repo, "new", "--title", "t", "--area", "a")
    assert run(repo, "evidence", "FW-0001", "review", "--ref", "r.md") == 1
    assert "open_critical" in capsys.readouterr().err
    assert run(repo, "evidence", "FW-0001", "review", "--ref", "r.md", "--open-critical", "0") == 0


def test_dod_add_remove(repo, capsys):
    run(repo, "new", "--title", "t", "--area", "a", "--dod", "on board")
    assert run(repo, "dod", "FW-0001", "--add", "review", "--remove", "on board") == 0
    ticket = load_ticket(repo, "FW-0001")
    assert ticket["dod_pending"] == ["review"]
    assert ticket["history"][-1]["note"] == "dod: add review; done on board"
    assert run(repo, "dod", "FW-0001", "--remove", "missing item") == 1


def test_block_unblock(repo):
    run(repo, "new", "--title", "t", "--area", "a")
    with pytest.raises(SystemExit):
        run(repo, "block", "FW-0001")
    assert run(repo, "block", "FW-0001", "--reason", "waiting for hardware") == 0
    assert load_ticket(repo, "FW-0001")["status"] == "blocked"
    assert run(repo, "unblock", "FW-0001") == 0
    assert load_ticket(repo, "FW-0001")["status"] == "backlog"


def ready_for_done(repo):
    run(repo, "new", "--title", "t", "--area", "a", "--no-hil")
    run(repo, "claim", "FW-0001")
    run(repo, "evidence", "FW-0001", "check", "--commit", "HEAD", "--summary", "ok", "--passed")
    run(repo, "move", "FW-0001", "verifying")
    ticket = load_ticket(repo, "FW-0001")
    ticket["evidence"].append(make_evidence("review", BOB, NOW, ref="r.md", open_critical=0))
    save_ticket(repo, ticket)


def test_done_via_cli_after_review_by_other(repo):
    ready_for_done(repo)
    assert load_ticket(repo, "FW-0001")["requires_hil"] is False
    assert run(repo, "move", "FW-0001", "done") == 0
    assert load_ticket(repo, "FW-0001")["status"] == "done"


def test_done_refused_without_tty(repo, capsys):
    ready_for_done(repo)
    capsys.readouterr()
    # No confirm injected: pytest's stdin is not a TTY, which is what an agent's shell looks like
    assert main(["move", "FW-0001", "done"], cwd=repo, now=NOW) == 1
    assert "interactive terminal" in capsys.readouterr().err
    assert load_ticket(repo, "FW-0001")["status"] == "verifying"


def test_collisions_offline_reports_none(repo, capsys):
    assert run(repo, "collisions") == 0
    out = capsys.readouterr()
    assert "No ticket ID clashes" in out.out and "offline" in out.err


def test_show_prints_utf8_json(repo, capsys):
    run(repo, "new", "--title", "µC driver ±2%", "--area", "a")
    capsys.readouterr()
    assert run(repo, "show", "FW-0001") == 0
    assert json.loads(capsys.readouterr().out)["title"] == "µC driver ±2%"


def test_missing_identity(repo, capsys):
    git(repo, "config", "--unset", "user.name")
    assert run(repo, "new", "--title", "t", "--area", "a") == 1
    assert "git config user.name" in capsys.readouterr().err
