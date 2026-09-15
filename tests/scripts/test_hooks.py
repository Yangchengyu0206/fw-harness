import json
import shutil
import stat
import subprocess

import pytest

from helpers import SCRIPTS, TEMPLATES, commit_all, git
from tickets import new_ticket, save_ticket

ALICE = {"name": "Alice Chen", "email": "alice@example.com"}
NOW = "2026-09-15T10:00:00+08:00"


@pytest.fixture
def hooked(repo):
    shutil.copytree(SCRIPTS, repo / "harness" / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(TEMPLATES / ".githooks", repo / ".githooks")
    for hook in (repo / ".githooks").iterdir():
        hook.chmod(hook.stat().st_mode | stat.S_IEXEC)
    (repo / ".gitignore").write_text("feature_list.json\n__pycache__/\n.verify_logs/\n", encoding="utf-8")
    git(repo, "config", "core.hooksPath", ".githooks")
    commit_all(repo, "harness: install hooks")
    return repo


def try_commit(repo, message):
    return subprocess.run(["git", "commit", "--allow-empty", "-m", message], cwd=repo,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def read_index(repo):
    return json.loads((repo / "feature_list.json").read_text(encoding="utf-8"))


def test_commit_without_ticket_is_rejected(hooked):
    result = try_commit(hooked, "tweak things")
    assert result.returncode != 0 and "FW-NNNN" in result.stderr


def test_valid_commit_builds_index_and_keeps_tree_clean(hooked):
    save_ticket(hooked, new_ticket("FW-0001", "UART DMA", "drivers/uart", ALICE, NOW))
    commit_all(hooked, "harness: open FW-0001")
    result = try_commit(hooked, "FW-0001 start work")
    assert result.returncode == 0, result.stderr
    assert read_index(hooked)["tickets"][0]["commits"][0]["subject"] == "FW-0001 start work"
    assert git(hooked, "status", "--porcelain") == ""


def test_post_merge_rebuilds_index(hooked):
    git(hooked, "checkout", "-b", "side")
    save_ticket(hooked, new_ticket("FW-0001", "UART DMA", "drivers/uart", ALICE, NOW))
    commit_all(hooked, "harness: open FW-0001")
    git(hooked, "checkout", "main")
    (hooked / "feature_list.json").unlink(missing_ok=True)
    git(hooked, "merge", "--no-ff", "--no-edit", "side")
    assert [ticket["id"] for ticket in read_index(hooked)["tickets"]] == ["FW-0001"]
