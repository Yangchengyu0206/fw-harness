from jsonio import write_json_atomic
from ticket_check import check_tickets, main
from tickets import make_evidence, new_ticket, save_ticket, ticket_path

ALICE = {"name": "Alice Chen", "email": "alice@example.com"}
BOB = {"name": "Bob Lin", "email": "bob@example.com"}
NOW = "2026-09-15T10:00:00+08:00"


def put(repo, ticket_id, status="backlog", assignee=None, **overrides):
    ticket = new_ticket(ticket_id, "t", "drivers/uart", ALICE, NOW)
    ticket.update(status=status, assignee=assignee, **overrides)
    save_ticket(repo, ticket)
    return ticket


def test_empty_and_valid_pass(repo):
    assert check_tickets(repo) == []
    put(repo, "FW-0001")
    put(repo, "FW-0002", "active", ALICE)
    assert check_tickets(repo) == []


def test_schema_error_reported_with_filename(repo):
    put(repo, "FW-0001", status="doing")
    assert any(e.startswith("FW-0001.json: ") and "status" in e for e in check_tickets(repo))


def test_broken_json_reported(repo):
    ticket_path(repo, "FW-0001").write_text("{ broken", encoding="utf-8")
    errors = check_tickets(repo)
    assert len(errors) == 1 and "FW-0001.json" in errors[0] and "JSON" in errors[0]


def test_duplicate_id_reported(repo):
    ticket = put(repo, "FW-0001")
    write_json_atomic(ticket_path(repo, "FW-0002"), ticket)
    assert any("duplicate" in e and "FW-0001" in e for e in check_tickets(repo))


def test_two_active_for_same_assignee(repo):
    put(repo, "FW-0001", "active", ALICE)
    put(repo, "FW-0002", "active", {"name": "Alice", "email": "ALICE@example.com"})
    put(repo, "FW-0003", "active", BOB)
    errors = check_tickets(repo)
    assert len(errors) == 1 and "FW-0001, FW-0002" in errors[0]


def test_done_without_dod_reported(repo):
    put(repo, "FW-0001", "done", ALICE, requires_hil=False)
    ok = put(repo, "FW-0002", "done", ALICE, requires_hil=False,
             evidence=[make_evidence("review", BOB, NOW, ref="r.md", open_critical=0)])
    errors = check_tickets(repo)
    assert len(errors) == 1 and errors[0].startswith("FW-0001.json: ") and "kind: review" in errors[0]
    assert ok["id"] == "FW-0002"


def test_main_exit_codes(repo, monkeypatch, capsys):
    monkeypatch.chdir(repo)
    put(repo, "FW-0001")
    assert main([]) == 0
    assert "passed (1 ticket" in capsys.readouterr().out
    put(repo, "FW-0002", status="blocked")
    assert main([]) == 1
    assert "blocked_reason" in capsys.readouterr().err
