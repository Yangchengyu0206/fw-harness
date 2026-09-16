import json
import shutil

import pytest

import arch_sync
import check
import init_check
import install
from helpers import FIXTURES, TEMPLATES, commit_all, fake_config, git, make_repo, write_config


@pytest.fixture
def firmware(tmp_path):
    """A firmware repo holding sources only: no harness, no architecture, no documents."""
    repo = make_repo(tmp_path / "fw", "Alice Chen", "alice@example.com")
    for folder in ("src", "test", "third_party"):
        shutil.copytree(FIXTURES / "sample-fw" / folder, repo / folder)
    for doc in repo.rglob("ARCHITECTURE.md"):
        doc.unlink()
    commit_all(repo, "harness: add firmware sources")
    return repo


def test_generate_a_harness_and_pass_check(firmware, capsys):
    report = install.install(firmware, TEMPLATES)
    assert report["proposed"] == []

    write_config(firmware, fake_config())

    written, arch, scan_report = arch_sync.scan(firmware)
    assert written == "harness/architecture.json"
    assert sorted(arch["modules"]) == ["src/app", "src/drivers", "src/hal", "test", "third_party/cmsis"]
    assert scan_report["reverse"] == [("src/hal", "src/app")]

    documents = arch_sync.docs(firmware)
    assert "ARCHITECTURE.md" in documents
    assert (firmware / "src" / "hal" / "ARCHITECTURE.md").is_file()

    assert check.main([], cwd=firmware) == 0
    assert "check 7/7 passed" in capsys.readouterr().out


def test_generated_harness_passes_init_and_commits_cleanly(firmware, capsys):
    install.install(firmware, TEMPLATES)
    write_config(firmware, fake_config())
    arch_sync.scan(firmware)
    arch_sync.docs(firmware)

    assert init_check.main([], cwd=firmware) == 0
    assert git(firmware, "config", "core.hooksPath") == ".githooks"

    commit_all(firmware, "harness: add the generated harness")
    assert git(firmware, "status", "--porcelain") == ""

    record = json.loads((firmware / "harness" / ".harness-version").read_text(encoding="utf-8"))
    assert record["version"] == (TEMPLATES / "VERSION").read_text(encoding="utf-8").strip()


def test_a_new_folder_fails_arch_check_until_it_is_synced(firmware):
    install.install(firmware, TEMPLATES)
    write_config(firmware, fake_config())
    arch_sync.scan(firmware)
    arch_sync.docs(firmware)
    commit_all(firmware, "harness: add the generated harness")

    new = firmware / "src" / "sensors"
    new.mkdir()
    (new / "sensor.c").write_text('#include "uart.h"\n\nint sensor_init(void) { return 0; }\n', encoding="utf-8")
    assert check.main([], cwd=firmware) == 1

    arch_sync.scan(firmware, force=True)
    arch_sync.docs(firmware)
    assert check.main([], cwd=firmware) == 0
