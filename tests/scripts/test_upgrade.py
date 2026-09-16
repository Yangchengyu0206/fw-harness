import json
import shutil

import pytest

import install
import manifest
import upgrade
from helpers import TEMPLATES, commit_all, make_fixture_repo


@pytest.fixture
def installed(tmp_path):
    repo = make_fixture_repo(tmp_path / "fw")
    for path in (".gitignore", "harness/architecture.json", "harness/cppcheck-suppressions.txt"):
        (repo / path).unlink()
    commit_all(repo, "harness: clear installable files")
    install.install(repo, TEMPLATES)
    return repo


@pytest.fixture
def newer(tmp_path):
    """A copy of the shipped templates with a higher version and one changed file of each kind."""
    target = tmp_path / "templates-0.2.0"
    shutil.copytree(TEMPLATES, target, ignore=shutil.ignore_patterns("__pycache__"))
    (target / "VERSION").write_text("0.2.0\n", encoding="utf-8")
    makefile = target / "Makefile"
    makefile.write_text(makefile.read_text(encoding="utf-8") + "\n# new managed line\n", encoding="utf-8")
    agents = target / "AGENTS.md"
    agents.write_text(agents.read_text(encoding="utf-8") + "\nNew guardrail.\n", encoding="utf-8")
    return target


def test_upgrade_without_an_install_explains_the_fix(tmp_path):
    repo = make_fixture_repo(tmp_path / "bare")
    with pytest.raises(upgrade.UpgradeError, match="fw-harness-init"):
        upgrade.upgrade(repo, TEMPLATES)


def test_upgrade_updates_a_managed_file(installed, newer):
    report = upgrade.upgrade(installed, newer)
    assert report["from_version"] == "0.1.0" and report["to_version"] == "0.2.0"
    assert "Makefile" in report["updated"]
    assert "# new managed line" in (installed / "Makefile").read_text(encoding="utf-8")


def test_upgrade_proposes_a_team_owned_change(installed, newer):
    report = upgrade.upgrade(installed, newer)
    assert "AGENTS.md" in report["proposed"]
    assert "New guardrail." not in (installed / "AGENTS.md").read_text(encoding="utf-8")
    assert "New guardrail." in (installed / ("AGENTS.md" + manifest.PROPOSED_SUFFIX)).read_text(encoding="utf-8")


def test_upgrade_keeps_a_locally_edited_managed_file(installed, newer):
    makefile = installed / "Makefile"
    makefile.write_text(makefile.read_text(encoding="utf-8") + "\n# local tweak\n", encoding="utf-8")
    report = upgrade.upgrade(installed, newer)
    assert "Makefile" in report["proposed"] and "Makefile" not in report["updated"]
    assert "# local tweak" in makefile.read_text(encoding="utf-8")
    assert "# new managed line" in (installed / ("Makefile" + manifest.PROPOSED_SUFFIX)).read_text(encoding="utf-8")


def test_upgrade_recreates_a_deleted_managed_file(installed, newer):
    (installed / "harness" / "scripts" / "ratchet.py").unlink()
    report = upgrade.upgrade(installed, newer)
    assert "harness/scripts/ratchet.py" in report["created"]
    assert (installed / "harness" / "scripts" / "ratchet.py").is_file()


def test_upgrade_rewrites_the_version_record(installed, newer):
    upgrade.upgrade(installed, newer)
    record = json.loads((installed / manifest.VERSION_PATH).read_text(encoding="utf-8"))
    assert record["version"] == "0.2.0"
    assert record["managed"]["Makefile"] == manifest.digest((installed / "Makefile").read_bytes())
    assert record["team_owned"]["AGENTS.md"] == manifest.digest((newer / "AGENTS.md").read_bytes())


def test_upgrade_is_idempotent(installed, newer):
    upgrade.upgrade(installed, newer)
    report = upgrade.upgrade(installed, newer)
    assert report["updated"] == [] and report["created"] == []


def test_dry_run_writes_nothing(installed, newer):
    before = (installed / "Makefile").read_bytes()
    report = upgrade.upgrade(installed, newer, dry_run=True)
    assert "Makefile" in report["updated"]
    assert (installed / "Makefile").read_bytes() == before
    assert json.loads((installed / manifest.VERSION_PATH).read_text(encoding="utf-8"))["version"] == "0.1.0"


def test_main_reports_each_group(installed, newer, capsys):
    assert upgrade.main(["--templates", str(newer)], cwd=installed) == 0
    output = capsys.readouterr().out
    assert "0.1.0 to 0.2.0" in output and "AGENTS.md" in output
