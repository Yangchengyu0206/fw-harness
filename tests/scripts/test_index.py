from helpers import commit_all, git
from index import INDEX_NAME, build_index, commit_evidence, main, write_index
from jsonio import read_json
from tickets import make_evidence, new_ticket, save_ticket

ALICE = {"name": "Alice Chen", "email": "alice@example.com"}
BOB = {"name": "Bob Lin", "email": "bob@example.com"}
NOW = "2026-09-15T10:00:00+08:00"


def seed(repo):
    first = new_ticket("FW-0001", "UART DMA", "drivers/uart", ALICE, NOW, priority=2)
    first.update(status="active", assignee=ALICE, dod_pending=["on board"])
    first["evidence"] = [
        make_evidence("check", ALICE, NOW, commit="abc1234", summary="check 7/7 passed", passed=True),
        make_evidence("review", BOB, NOW, ref="r.md", open_critical=1),
    ]
    save_ticket(repo, first)
    save_ticket(repo, new_ticket("FW-0002", "SPI", "drivers/spi", BOB, NOW))
    commit_all(repo, "FW-0001 open ticket")
    (repo / "a.txt").write_text("a", encoding="utf-8")
    git(repo, "add", "-A")
    # µ is a word character like CJK text, so \b would miss µFW-0001; XFW-0003 must not match
    git(repo, "commit", "-m", "harness: tweak", "-m", "also covers FW-0002 and µFW-0001, but not XFW-0003")


def test_commit_evidence_scans_subject_and_body(repo):
    seed(repo)
    evidence = commit_evidence(repo)
    assert [c["subject"] for c in evidence["FW-0001"]] == ["harness: tweak", "FW-0001 open ticket"]
    assert [c["subject"] for c in evidence["FW-0002"]] == ["harness: tweak"]
    assert "FW-0003" not in evidence
    item = evidence["FW-0001"][1]
    assert item["kind"] == "commit" and len(item["commit"]) == 10
    assert item["by"] == ALICE and item["at"].startswith("20")


def test_build_index_summary(repo):
    seed(repo)
    tickets = {t["id"]: t for t in build_index(repo)["tickets"]}
    first = tickets["FW-0001"]
    assert first["status"] == "active" and first["assignee"] == ALICE
    assert first["requires_hil"] is True
    assert first["evidence_counts"] == {"check": 1, "hil": 0, "review": 1}
    assert first["latest_review_open_critical"] == 1
    assert len(first["commits"]) == 2
    assert tickets["FW-0002"]["latest_review_open_critical"] is None


def test_write_index_leaves_tracked_files_untouched(repo):
    seed(repo)
    path = write_index(repo)
    assert path == repo / INDEX_NAME
    assert read_json(path)["tickets"][0]["id"] == "FW-0001"
    assert git(repo, "status", "--porcelain") == f"?? {INDEX_NAME}"


def test_main_prints_count(repo, monkeypatch, capsys):
    seed(repo)
    monkeypatch.chdir(repo)
    assert main([]) == 0
    assert "2 tickets" in capsys.readouterr().out
