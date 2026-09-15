import re

import pytest

from tickets import (
    format_id, load_all, load_ticket, make_evidence, new_ticket, now_iso,
    parse_id, save_ticket, ticket_path, validate_ticket,
)

ALICE = {"name": "Alice Chen", "email": "alice@example.com"}
NOW = "2026-09-15T10:02:00+08:00"


def sample(ticket_id="FW-0042", **overrides):
    ticket = new_ticket(ticket_id, "UART driver: DMA receive at 115200 baud ±2%", "drivers/uart", ALICE, NOW,
                        priority=2, user_visible_behavior="Receives 4 KB continuously without dropping a byte",
                        verification_steps=["host test", "on board: 4 KB loopback"],
                        dod_pending=["on-board loopback verification"])
    ticket.update(overrides)
    return ticket


def test_id_helpers():
    assert format_id(7) == "FW-0007"
    assert format_id(12345) == "FW-12345"
    assert parse_id("FW-0042") == 42
    with pytest.raises(ValueError):
        parse_id("FW-42")


def test_now_iso_has_offset_and_seconds():
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d[+-]\d\d:\d\d", now_iso())


def test_new_ticket_is_valid_backlog():
    ticket = sample()
    assert validate_ticket(ticket, "FW-0042.json") == []
    assert ticket["status"] == "backlog"
    assert ticket["assignee"] is None
    assert ticket["evidence"] == []
    assert ticket["history"] == [{"by": ALICE, "at": NOW, "from": None, "to": "backlog", "note": "opened"}]


def test_filename_must_match_id():
    errors = validate_ticket(sample(), "FW-0043.json")
    assert any("does not match file name" in e for e in errors)


@pytest.mark.parametrize("overrides, fragment", [
    ({"id": "FW-42"}, "id must match FW-NNNN"),
    ({"status": "doing"}, "status must be one of"),
    ({"priority": "high"}, "priority"),
    ({"requires_hil": "yes"}, "requires_hil"),
    ({"status": "blocked"}, "blocked_reason"),
    ({"status": "active"}, "requires an assignee"),
    ({"dod_pending": "on board"}, "dod_pending"),
    ({"evidence": [{"kind": "commit", "by": ALICE, "at": NOW}]}, "derived from git log"),
    ({"evidence": [{"kind": "review", "by": ALICE, "at": NOW, "ref": "r.md"}]}, "open_critical"),
    ({"evidence": [{"kind": "check", "by": ALICE, "at": NOW, "commit": "abc1234", "summary": "s", "passed": "yes"}]}, "passed"),
    ({"history": [{"by": ALICE, "at": NOW, "to": "nowhere"}]}, "history[0]"),
])
def test_validation_errors(overrides, fragment):
    errors = validate_ticket(sample(**overrides))
    assert any(fragment in e for e in errors), errors


def test_errors_are_prefixed_with_label():
    errors = validate_ticket(sample(status="doing"), "FW-0042.json")
    assert errors and all(e.startswith("FW-0042.json: ") for e in errors)


def test_save_load_roundtrip_and_load_all_sorted(repo):
    save_ticket(repo, sample("FW-0002"))
    save_ticket(repo, sample("FW-0001"))
    assert ticket_path(repo, "FW-0001").exists()
    assert load_ticket(repo, "FW-0002")["id"] == "FW-0002"
    assert [t["id"] for _, t in load_all(repo)] == ["FW-0001", "FW-0002"]


def test_load_ticket_missing(repo):
    with pytest.raises(FileNotFoundError):
        load_ticket(repo, "FW-0099")


def test_make_evidence():
    ev = make_evidence("review", ALICE, NOW, ref="harness/reviews/x.md", open_critical=0)
    assert ev == {"kind": "review", "by": ALICE, "at": NOW, "ref": "harness/reviews/x.md", "open_critical": 0}
    failed = make_evidence("check", ALICE, NOW, commit="abc1234", summary="check 5/7", passed=False)
    assert failed["passed"] is False
    with pytest.raises(ValueError):
        make_evidence("check", ALICE, NOW, commit="abc1234", summary="check 7/7 passed")
    with pytest.raises(ValueError):
        make_evidence("check", ALICE, NOW, commit="abc")
    with pytest.raises(ValueError):
        make_evidence("commit", ALICE, NOW)
