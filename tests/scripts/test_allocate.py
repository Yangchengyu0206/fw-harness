import pytest

from allocate import (
    OFFLINE_WARNING, RenumberError, commits_mentioning, find_collisions, next_ticket_id, renumber,
)
from helpers import commit_all, git
from tickets import load_ticket, new_ticket, save_ticket, ticket_path

ALICE = {"name": "Alice Chen", "email": "alice@example.com"}
BOB = {"name": "Bob Lin", "email": "bob@example.com"}


def open_ticket(repo, who, now, title="t"):
    ticket_id = next_ticket_id(repo, warn=lambda m: None)
    save_ticket(repo, new_ticket(ticket_id, title, "drivers/uart", who, now))
    commit_all(repo, f"{ticket_id} open ticket")
    return ticket_id


def test_offline_uses_local_and_warns(repo):
    warnings = []
    assert next_ticket_id(repo, warn=warnings.append) == "FW-0001"
    assert warnings == [OFFLINE_WARNING]


def test_local_max_plus_one(repo):
    save_ticket(repo, new_ticket("FW-0003", "t", "a", ALICE, "2026-09-15T10:00:00+08:00"))
    assert next_ticket_id(repo, warn=lambda m: None) == "FW-0004"


def test_remote_max_plus_one(team):
    _, clones = team
    bob = clones["bob"]
    save_ticket(bob, new_ticket("FW-0005", "t", "a", BOB, "2026-09-15T10:00:00+08:00"))
    commit_all(bob, "FW-0005 open ticket")
    git(bob, "push", "origin", "main")
    warnings = []
    assert next_ticket_id(clones["alice"], warn=warnings.append) == "FW-0006"
    assert warnings == []


def collide(team):
    _, clones = team
    alice, bob = clones["alice"], clones["bob"]
    assert open_ticket(alice, ALICE, "2026-09-15T10:00:00+08:00", "alice's ticket") == "FW-0001"
    assert open_ticket(bob, BOB, "2026-09-15T10:00:05+08:00", "bob's ticket") == "FW-0001"
    git(bob, "push", "origin", "main")
    return alice, bob


def test_renumber_later_ticket_and_merge_cleanly(team):
    alice, _ = collide(team)
    new_id = renumber(alice, "FW-0001", ALICE, "2026-09-15T10:05:00+08:00", warn=lambda m: None)
    assert new_id == "FW-0002"
    assert not ticket_path(alice, "FW-0001").exists()
    moved = load_ticket(alice, "FW-0002")
    assert moved["id"] == "FW-0002" and moved["title"] == "alice's ticket"
    assert moved["history"][-1]["note"] == "renumber: FW-0001 -> FW-0002"
    assert commits_mentioning(alice, "FW-0001")[0].endswith("FW-0001 open ticket")
    commit_all(alice, "harness: renumber FW-0001 -> FW-0002")
    git(alice, "merge", "--no-edit", "origin/main")
    assert load_ticket(alice, "FW-0001")["title"] == "bob's ticket"
    assert load_ticket(alice, "FW-0002")["title"] == "alice's ticket"


def test_find_collisions_before_and_after_renumber(team):
    alice, _ = collide(team)
    assert find_collisions(alice, warn=lambda m: None) == ["FW-0001"]
    renumber(alice, "FW-0001", ALICE, "2026-09-15T10:05:00+08:00", warn=lambda m: None)
    commit_all(alice, "harness: renumber FW-0001 -> FW-0002")
    git(alice, "merge", "--no-edit", "origin/main")
    assert find_collisions(alice, warn=lambda m: None) == []


def test_find_collisions_offline_warns(repo):
    open_ticket(repo, ALICE, "2026-09-15T10:00:00+08:00")
    warnings = []
    assert find_collisions(repo, warn=warnings.append) == []
    assert warnings == [OFFLINE_WARNING]


def test_renumber_refuses_when_not_on_main(team):
    _, clones = team
    open_ticket(clones["alice"], ALICE, "2026-09-15T10:00:00+08:00")
    with pytest.raises(RenumberError, match="not on origin/main"):
        renumber(clones["alice"], "FW-0001", ALICE, "now", warn=lambda m: None)


def test_renumber_refuses_same_ticket(team):
    _, clones = team
    open_ticket(clones["bob"], BOB, "2026-09-15T10:00:00+08:00")
    git(clones["bob"], "push", "origin", "main")
    git(clones["alice"], "pull", "--no-edit", "origin", "main")
    with pytest.raises(RenumberError, match="same ticket"):
        renumber(clones["alice"], "FW-0001", ALICE, "now", warn=lambda m: None)


def test_renumber_refuses_offline(repo):
    open_ticket(repo, ALICE, "2026-09-15T10:00:00+08:00")
    with pytest.raises(RenumberError, match="origin/main"):
        renumber(repo, "FW-0001", ALICE, "now", warn=lambda m: None)
