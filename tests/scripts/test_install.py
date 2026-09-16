import json
import stat
import sys

import pytest

import install
import manifest
from helpers import TEMPLATES, commit_all, git, make_fixture_repo, make_repo


@pytest.fixture
def fresh(tmp_path):
    """A firmware repo with sources but no file the harness would install."""
    repo = make_fixture_repo(tmp_path / "fw")
    for path in (".gitignore", "harness/architecture.json", "harness/cppcheck-suppressions.txt"):
        (repo / path).unlink()
    commit_all(repo, "harness: clear installable files")
    return repo


def test_install_creates_every_manifest_file(fresh):
    report = install.install(fresh, TEMPLATES)
    for path in manifest.managed_files(TEMPLATES) + list(manifest.TEAM_OWNED) + list(manifest.GENERATED):
        assert (fresh / path).is_file(), path
    assert report["proposed"] == []
    assert report["version"] == manifest.read_version(TEMPLATES)


def test_install_creates_state_folders_with_gitkeep(fresh):
    install.install(fresh, TEMPLATES)
    for folder in manifest.DIRS:
        assert (fresh / folder / ".gitkeep").is_file()


def test_install_sets_the_hooks_path(fresh):
    install.install(fresh, TEMPLATES)
    assert git(fresh, "config", "core.hooksPath") == ".githooks"


def test_install_never_overwrites_and_proposes_instead(fresh):
    (fresh / "AGENTS.md").write_text("Our own entry point.\n", encoding="utf-8")
    report = install.install(fresh, TEMPLATES)
    assert (fresh / "AGENTS.md").read_text(encoding="utf-8") == "Our own entry point.\n"
    assert "AGENTS.md" in report["proposed"]
    assert (fresh / ("AGENTS.md" + manifest.PROPOSED_SUFFIX)).read_text(encoding="utf-8") == \
        (TEMPLATES / "AGENTS.md").read_text(encoding="utf-8")


def test_install_twice_changes_nothing(fresh):
    install.install(fresh, TEMPLATES)
    report = install.install(fresh, TEMPLATES)
    assert report["created"] == [] and report["proposed"] == []
    assert "AGENTS.md" in report["unchanged"]


def test_install_writes_the_version_record(fresh):
    install.install(fresh, TEMPLATES)
    record = json.loads((fresh / manifest.VERSION_PATH).read_text(encoding="utf-8"))
    assert record["version"] == manifest.read_version(TEMPLATES)
    assert record["marketplace"] == install.DEFAULT_MARKETPLACE
    assert record["managed"]["harness/scripts/check.py"] == manifest.digest(
        (fresh / "harness" / "scripts" / "check.py").read_bytes())
    assert record["team_owned"]["AGENTS.md"] == manifest.digest((TEMPLATES / "AGENTS.md").read_bytes())


def test_settings_merge_keeps_unrelated_keys():
    claude = install.claude_settings({"permissions": {"allow": ["Bash"]}}, "acme/fw-harness")
    assert claude["permissions"] == {"allow": ["Bash"]}
    assert claude["extraKnownMarketplaces"]["fw-harness"]["source"] == {"source": "github", "repo": "acme/fw-harness"}
    assert claude["enabledPlugins"]["fw-c-harness@fw-harness"] is True

    copilot = install.copilot_settings({"extraKnownMarketplaces": [{"name": "other", "source": "a/b"}]},
                                       "acme/fw-harness")
    names = [entry["name"] for entry in copilot["extraKnownMarketplaces"]]
    assert names == ["other", "fw-harness"]
    again = install.copilot_settings(copilot, "acme/fw-harness")
    assert len(again["extraKnownMarketplaces"]) == 2


def test_install_writes_both_settings_files(fresh):
    install.install(fresh, TEMPLATES)
    claude = json.loads((fresh / ".claude" / "settings.json").read_text(encoding="utf-8"))
    copilot = json.loads((fresh / ".github" / "copilot-settings.json").read_text(encoding="utf-8"))
    assert "fw-harness" in claude["extraKnownMarketplaces"]
    assert copilot["extraKnownMarketplaces"][0]["source"] == install.DEFAULT_MARKETPLACE


def test_install_renders_the_review_instructions_from_the_checklist(fresh):
    install.install(fresh, TEMPLATES)
    text = (fresh / manifest.GENERATED[0]).read_text(encoding="utf-8")
    assert 'applyTo: "**/*.{c,h}"' in text and "Critical (blocks merge)" in text


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX file modes")
def test_hooks_are_executable(fresh):
    install.install(fresh, TEMPLATES)
    for path in manifest.EXECUTABLE:
        assert (fresh / path).stat().st_mode & stat.S_IXUSR


def test_hooks_are_staged_with_the_executable_bit(fresh):
    install.install(fresh, TEMPLATES)
    listing = git(fresh, "ls-files", "--stage", ".githooks/commit-msg")
    assert listing.startswith("100755")


def test_main_reports_and_refuses_a_missing_templates_folder(tmp_path, capsys):
    repo = make_repo(tmp_path / "fw", "Alice Chen", "alice@example.com")
    assert install.main(["--templates", str(tmp_path / "nope")], cwd=repo) == 1
    assert "not found" in capsys.readouterr().err
    assert install.main(["--templates", str(TEMPLATES)], cwd=repo) == 0
    assert "created" in capsys.readouterr().out
