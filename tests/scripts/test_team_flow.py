from helpers import commit_all, git
from index import build_index
from ticket import main
from ticket_check import check_tickets
from tickets import load_ticket

NOW = "2026-09-15T10:00:00+08:00"


def run(repo, *argv):
    # This test plays humans at a terminal, so confirmation is injected;
    # the TTY refusal case lives in test_ticket_cli.py
    return main(list(argv), cwd=repo, now=NOW, confirm=lambda ticket_id: True)


def test_two_people_collide_claim_review_and_finish(team):
    _, clones = team
    alice, bob = clones["alice"], clones["bob"]

    # 1. Both open a ticket before either pushes, and get the same ID
    assert run(alice, "new", "--title", "UART DMA", "--area", "drivers/uart",
               "--step", "on board: 4 KB loopback", "--dod", "on-board loopback verification") == 0
    commit_all(alice, "FW-0001 open ticket: UART DMA")
    assert run(bob, "new", "--title", "SPI flash", "--area", "drivers/spi") == 0
    commit_all(bob, "FW-0001 open ticket: SPI flash")
    git(bob, "push", "origin", "main")

    # 2. Alice's pre-merge check finds the clash; she came later, renumbers, and merges cleanly
    assert run(alice, "collisions") == 1
    assert run(alice, "renumber", "FW-0001") == 0
    commit_all(alice, "harness: renumber FW-0001 -> FW-0002")
    git(alice, "merge", "--no-edit", "origin/main")
    assert load_ticket(alice, "FW-0001")["title"] == "SPI flash"
    assert load_ticket(alice, "FW-0002")["title"] == "UART DMA"
    git(alice, "push", "origin", "main")
    git(bob, "pull", "--no-edit", "origin", "main")

    # 3. Each claims one ticket; nobody holds two active tickets
    assert run(alice, "claim", "FW-0002") == 0
    commit_all(alice, "FW-0002 claim")
    assert run(alice, "claim", "FW-0001") == 1
    assert run(bob, "claim", "FW-0001") == 0
    commit_all(bob, "FW-0001 claim")

    # 4. Alice finishes, check passes -> verifying; her own review cannot take it to done
    (alice / "uart.c").write_text("int uart_init(void) { return 0; }\n", encoding="utf-8")
    head = commit_all(alice, "FW-0002 implement DMA receive")
    assert run(alice, "evidence", "FW-0002", "check", "--commit", head, "--summary", "check 7/7 passed", "--passed") == 0
    assert run(alice, "move", "FW-0002", "verifying") == 0
    assert run(alice, "evidence", "FW-0002", "review", "--ref", "harness/reviews/self.md", "--open-critical", "0") == 0
    assert run(alice, "dod", "FW-0002", "--remove", "on-board loopback verification") == 0
    assert run(alice, "evidence", "FW-0002", "hil", "--ref", "harness/evidence/FW-0002/loopback.log") == 0
    assert run(alice, "move", "FW-0002", "done") == 1
    commit_all(alice, "FW-0002 check and hil evidence")
    git(alice, "pull", "--no-edit", "origin", "main")
    git(alice, "push", "origin", "main")

    # 5. Bob reviews: one critical first, zero after the re-review; only then can Alice finish
    git(bob, "pull", "--no-edit", "origin", "main")
    assert run(bob, "evidence", "FW-0002", "review", "--ref", "harness/reviews/FW-0002_bob_2026-09-16.md", "--open-critical", "1") == 0
    assert run(bob, "evidence", "FW-0002", "review", "--ref", "harness/reviews/FW-0002_bob_2026-09-17.md", "--open-critical", "0") == 0
    commit_all(bob, "FW-0002 review evidence")
    git(bob, "push", "origin", "main")
    git(alice, "pull", "--no-edit", "origin", "main")
    assert run(alice, "move", "FW-0002", "done") == 0
    commit_all(alice, "FW-0002 done")

    # 6. The global check passes and the index shows commit evidence from both people
    assert check_tickets(alice) == []
    entry = {t["id"]: t for t in build_index(alice)["tickets"]}["FW-0002"]
    authors = {c["by"]["email"] for c in entry["commits"]}
    assert authors == {"alice@example.com", "bob@example.com"}
    assert entry["status"] == "done"
