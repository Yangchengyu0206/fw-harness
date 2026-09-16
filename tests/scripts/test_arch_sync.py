import json

import pytest

import arch_sync
from arch_check import check_architecture
from arch_docs import block_of, render_block
from helpers import fake_config, make_fixture_repo, make_repo, write_config


@pytest.fixture
def fw(tmp_path):
    repo = make_fixture_repo(tmp_path / "fw")
    write_config(repo, fake_config())
    return repo


@pytest.fixture
def bare(tmp_path):
    """A repo with the sample sources but no architecture.json and no documents."""
    repo = make_fixture_repo(tmp_path / "bare")
    (repo / "harness" / "architecture.json").unlink()
    (repo / "ARCHITECTURE.md").unlink()
    for folder in ("src/app", "src/drivers", "src/hal", "test", "third_party/cmsis"):
        (repo / folder / "ARCHITECTURE.md").unlink()
    write_config(repo, fake_config())
    return repo


def test_scan_writes_the_architecture_when_none_exists(bare):
    written, arch, report = arch_sync.scan(bare)
    assert written == "harness/architecture.json"
    assert json.loads((bare / written).read_text(encoding="utf-8"))["modules"] == arch["modules"]
    assert report["reverse"] == [("src/hal", "src/app")]


def test_scan_proposes_instead_of_overwriting_an_approved_architecture(fw):
    written, _, _ = arch_sync.scan(fw)
    assert written == "harness/architecture.json.harness-proposed"
    assert (fw / written).is_file()
    assert json.loads((fw / "harness" / "architecture.json").read_text(encoding="utf-8"))["grandfathered"] == [
        "src/hal -> src/app"]


def test_scan_force_overwrites(fw):
    written, _, _ = arch_sync.scan(fw, force=True)
    assert written == "harness/architecture.json"


def test_docs_creates_every_missing_document_and_passes_arch_check(bare):
    arch_sync.scan(bare)
    written = arch_sync.docs(bare)
    assert "ARCHITECTURE.md" in written and "src/app/ARCHITECTURE.md" in written
    errors, _ = check_architecture(bare)
    assert errors == []


def test_docs_keeps_human_text_and_refreshes_only_the_block(fw):
    doc = fw / "src" / "app" / "ARCHITECTURE.md"
    doc.write_text(doc.read_text(encoding="utf-8") + "\n## Notes\n\nKeep me.\n", encoding="utf-8")
    arch = json.loads((fw / "harness" / "architecture.json").read_text(encoding="utf-8"))
    arch["modules"]["src/app"]["allowed_deps"] = ["src/drivers", "src/hal"]
    (fw / "harness" / "architecture.json").write_text(json.dumps(arch, indent=2), encoding="utf-8")
    assert "src/app/ARCHITECTURE.md" in arch_sync.docs(fw)
    text = doc.read_text(encoding="utf-8")
    assert "Keep me." in text and block_of(text) == render_block("src/app", arch)


def test_docs_is_idempotent(fw):
    assert arch_sync.docs(fw) == []


def test_main_reports_what_it_wrote(bare, capsys):
    assert arch_sync.main(["scan"], cwd=bare) == 0
    assert arch_sync.main(["docs"], cwd=bare) == 0
    output = capsys.readouterr().out
    assert "harness/architecture.json" in output and "ARCHITECTURE.md" in output


def test_main_without_sources_explains_the_problem(tmp_path, capsys):
    repo = make_repo(tmp_path / "empty", "Alice Chen", "alice@example.com")
    write_config(repo, fake_config())
    assert arch_sync.main(["scan"], cwd=repo) == 1
    assert "no C sources" in capsys.readouterr().err
