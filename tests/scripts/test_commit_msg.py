import pytest

from commit_msg_check import check_message, main
from tickets import new_ticket, save_ticket

ALICE = {"name": "Alice Chen", "email": "alice@example.com"}
NOW = "2026-09-15T10:00:00+08:00"


@pytest.fixture
def repo_with_ticket(repo):
    save_ticket(repo, new_ticket("FW-0001", "t", "a", ALICE, NOW))
    return repo


@pytest.mark.parametrize("message", [
    "FW-0001 add DMA receive",
    "fix(uart): overflow\n\nRefs FW-0001",
    "harness: update hooks",
    "chore(ci): tweak",
    "chore!: drop Python 3.8",
    "Merge branch 'feature/x'",
    'Revert "FW-0001 add DMA receive"',
    "fixup! FW-0001 add DMA receive",
    "# comment only\n",
])
def test_accepted(repo_with_ticket, message):
    assert check_message(repo_with_ticket, message) == []


def test_missing_ticket_reference(repo_with_ticket):
    errors = check_message(repo_with_ticket, "tweak things")
    assert len(errors) == 1 and "FW-NNNN" in errors[0]


def test_unknown_ticket(repo_with_ticket):
    assert check_message(repo_with_ticket, "FW-0001 and FW-0099") == [
        "commit message references tickets that do not exist: FW-0099. Fix: open the ticket with ticket.py new first"
    ]


def test_reference_in_comment_line_does_not_count(repo_with_ticket):
    assert check_message(repo_with_ticket, "tweak\n# FW-0001 only in a comment") != []


def test_main_reads_message_file(repo_with_ticket, tmp_path, capsys):
    message = tmp_path / "COMMIT_EDITMSG"
    message.write_text("tweak things\n", encoding="utf-8")
    assert main([str(message)], cwd=repo_with_ticket) == 1
    assert "FW-NNNN" in capsys.readouterr().err
    message.write_text("FW-0001 real work\n", encoding="utf-8")
    assert main([str(message)], cwd=repo_with_ticket) == 0
