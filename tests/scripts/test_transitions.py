import pytest

from helpers import commit_all, git
from tickets import make_evidence, new_ticket, save_ticket
from transitions import (
    TransitionError, block, done_problems, transition, unblock,
)

ALICE = {"name": "Alice Chen", "email": "alice@example.com"}
BOB = {"name": "Bob Lin", "email": "bob@example.com"}
NOW = "2026-09-15T10:00:00+08:00"


def ticket_at(repo, ticket_id, status, assignee=ALICE, **overrides):
    ticket = new_ticket(ticket_id, "t", "drivers/uart", ALICE, NOW)
    ticket["status"] = status
    if status in ("active", "verifying", "done"):
        ticket["assignee"] = dict(assignee)
    ticket.update(overrides)
    save_ticket(repo, ticket)
    return ticket


def test_forward_path_sets_assignee_and_history(repo):
    ticket = ticket_at(repo, "FW-0001", "backlog")
    ticket = transition(repo, ticket, "next", ALICE, NOW)
    ticket = transition(repo, ticket, "active", BOB, NOW, note="taking it")
    assert ticket["status"] == "active"
    assert ticket["assignee"] == BOB
    assert ticket["history"][-1] == {"by": BOB, "at": NOW, "from": "next", "to": "active", "note": "taking it"}


def test_illegal_skip_rejected(repo):
    ticket = ticket_at(repo, "FW-0001", "backlog")
    with pytest.raises(TransitionError, match="backlog -> active is not allowed"):
        transition(repo, ticket, "active", ALICE, NOW)


def test_transition_does_not_mutate_input(repo):
    ticket = ticket_at(repo, "FW-0001", "backlog")
    transition(repo, ticket, "next", ALICE, NOW)
    assert ticket["status"] == "backlog" and len(ticket["history"]) == 1


def test_blocked_only_via_block_and_unblock(repo):
    ticket = ticket_at(repo, "FW-0001", "next")
    with pytest.raises(TransitionError, match="block"):
        transition(repo, ticket, "blocked", ALICE, NOW)


def test_one_active_per_person(repo):
    ticket_at(repo, "FW-0001", "active", assignee=ALICE)
    second = ticket_at(repo, "FW-0002", "next")
    with pytest.raises(TransitionError, match="already has active ticket FW-0001"):
        transition(repo, second, "active", ALICE, NOW)
    assert transition(repo, second, "active", BOB, NOW)["assignee"] == BOB


def test_verifying_requires_passing_check_on_head_ancestry(repo):
    ticket = ticket_at(repo, "FW-0001", "active")
    with pytest.raises(TransitionError, match="kind: check"):
        transition(repo, ticket, "verifying", ALICE, NOW)

    git(repo, "checkout", "-b", "side")
    (repo / "side.txt").write_text("x", encoding="utf-8")
    side_commit = commit_all(repo, "chore: side")
    git(repo, "checkout", "main")
    ticket["evidence"] = [make_evidence("check", ALICE, NOW, commit=side_commit, summary="check 7/7 passed", passed=True)]
    with pytest.raises(TransitionError, match="kind: check"):
        transition(repo, ticket, "verifying", ALICE, NOW)

    head = git(repo, "rev-parse", "--short", "HEAD")
    ticket["evidence"].append(make_evidence("check", ALICE, NOW, commit=head, summary="check 5/7", passed=False))
    with pytest.raises(TransitionError, match="passed: true"):
        transition(repo, ticket, "verifying", ALICE, NOW)

    ticket["evidence"].append(make_evidence("check", ALICE, NOW, commit=head, summary="check 7/7 passed", passed=True))
    assert transition(repo, ticket, "verifying", ALICE, NOW)["status"] == "verifying"


def test_done_problems_lists_every_gap(repo):
    ticket = ticket_at(repo, "FW-0001", "verifying", dod_pending=["on-board loopback verification"])
    problems = done_problems(ticket)
    assert len(problems) == 3
    assert "dod_pending" in problems[0]
    assert "kind: hil" in problems[1]
    assert "kind: review" in problems[2]


def test_self_review_and_open_critical_rejected(repo):
    ticket = ticket_at(repo, "FW-0001", "verifying")
    ticket["evidence"] = [make_evidence("review", ALICE, NOW, ref="r1.md", open_critical=0)]
    assert any("the assignee" in p for p in done_problems(ticket))
    ticket["evidence"].append(make_evidence("review", BOB, NOW, ref="r2.md", open_critical=2))
    assert any("2 open critical" in p for p in done_problems(ticket))


def test_latest_review_wins_and_hil_optional(repo):
    ticket = ticket_at(repo, "FW-0001", "verifying", requires_hil=False)
    ticket["evidence"] = [
        make_evidence("review", BOB, NOW, ref="r1.md", open_critical=1),
        make_evidence("review", BOB, NOW, ref="r2.md", open_critical=0),
    ]
    assert done_problems(ticket) == []
    ticket["requires_hil"] = True
    assert done_problems(ticket) == [
        "requires_hil is true but there is no kind: hil evidence. Fix: use fw-hil-verify"
    ]


def test_done_happy_path(repo):
    ticket = ticket_at(repo, "FW-0001", "verifying")
    ticket["evidence"] = [
        make_evidence("hil", ALICE, NOW, ref="harness/evidence/FW-0001/loopback.log"),
        make_evidence("review", BOB, NOW, ref="harness/reviews/FW-0001_bob_2026-09-16.md", open_critical=0),
    ]
    assert transition(repo, ticket, "done", ALICE, NOW)["status"] == "done"


def test_block_and_unblock_returns_to_previous(repo):
    ticket = ticket_at(repo, "FW-0001", "verifying")
    with pytest.raises(TransitionError, match="blocked_reason"):
        block(ticket, ALICE, NOW, "  ")
    blocked = block(ticket, ALICE, NOW, "waiting for hardware")
    assert blocked["status"] == "blocked" and blocked["blocked_reason"] == "waiting for hardware"
    restored = unblock(repo, blocked, ALICE, NOW)
    assert restored["status"] == "verifying" and restored["blocked_reason"] is None
    done = ticket_at(repo, "FW-0002", "done")
    with pytest.raises(TransitionError):
        block(done, ALICE, NOW, "x")


def test_unblock_to_active_respects_one_active(repo):
    first = block(ticket_at(repo, "FW-0001", "active"), ALICE, NOW, "waiting for spec")
    save_ticket(repo, first)
    second = transition(repo, ticket_at(repo, "FW-0002", "next"), "active", ALICE, NOW)
    save_ticket(repo, second)
    with pytest.raises(TransitionError, match="already has active ticket FW-0002"):
        unblock(repo, first, ALICE, NOW)
