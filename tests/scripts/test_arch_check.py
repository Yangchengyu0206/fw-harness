import json

import pytest

from arch_check import (
    ArchitectureError, check_architecture, dependencies, load_architecture, main, module_of,
    source_files, validate_architecture,
)
from helpers import TEMPLATES, add_origin, commit_all, make_fixture_repo


def edit_arch(repo, mutate):
    path = repo / "harness" / "architecture.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    mutate(data)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


@pytest.fixture
def fw(tmp_path):
    return make_fixture_repo(tmp_path / "fw")


def test_template_architecture_is_valid():
    data = json.loads((TEMPLATES / "harness" / "architecture.json").read_text(encoding="utf-8"))
    assert validate_architecture(data) == []


@pytest.mark.parametrize("mutate, fragment", [
    (lambda a: a.update(version=2), "version"),
    (lambda a: a["modules"]["src/app"].update(kind="library"), "kind"),
    (lambda a: a["modules"]["src/app"].update(allowed_deps=["src/nowhere"]), "src/nowhere"),
    (lambda a: a["modules"].update({"src/app/": {"kind": "owned", "allowed_deps": []}}), "src/app/"),
    (lambda a: a.update(grandfathered=["src/hal to src/app"]), "grandfathered"),
    (lambda a: a.update(include_dirs="src"), "include_dirs"),
])
def test_invalid_architecture(fw, mutate, fragment):
    data = load_architecture(fw)
    mutate(data)
    assert any(fragment in e for e in validate_architecture(data))


def test_module_of_uses_longest_prefix():
    modules = {"src": {}, "src/drivers": {}}
    assert module_of("src/drivers/uart.c", modules) == "src/drivers"
    assert module_of("src/main.c", modules) == "src"
    assert module_of("srcx/main.c", modules) is None


def test_dependencies_resolve_relative_and_include_dir_paths(fw):
    deps = dependencies(fw, load_architecture(fw), source_files(fw))
    assert deps[("src/hal", "src/app")] == ["src/hal/hal_gpio.c:2"]
    assert ("src/app", "src/drivers") in deps
    assert ("src/hal", "third_party/cmsis") in deps
    assert not any(source == "test" for source, _ in deps)


def test_sample_firmware_passes_with_grandfathered_reverse_dependency(fw):
    errors, warnings = check_architecture(fw)
    assert errors == []
    assert any("origin/main not found" in w for w in warnings)


def test_unapproved_dependency_fails_with_location(fw):
    edit_arch(fw, lambda a: a.update(grandfathered=[]))
    errors, _ = check_architecture(fw)
    assert len(errors) == 1
    assert errors[0].startswith("src/hal -> src/app: dependency not approved (src/hal/hal_gpio.c:2)")


def test_new_grandfather_entry_fails_ratchet_and_stale_entry_warns(fw):
    edit_arch(fw, lambda a: a["grandfathered"].append("src/app -> src/hal"))
    errors, warnings = check_architecture(fw)
    assert any("may only shrink" in e and "src/app -> src/hal" in e for e in errors)
    assert any(w.startswith("src/app -> src/hal: grandfathered but no longer violated") for w in warnings)


def test_ratchet_compares_with_origin_main(fw, tmp_path):
    add_origin(fw, tmp_path)
    edit_arch(fw, lambda a: a["grandfathered"].append("src/app -> src/hal"))
    commit_all(fw, "harness: sneak in a grandfather entry")
    errors, _ = check_architecture(fw)
    assert any("not on origin/main" in e and "may only shrink" in e for e in errors)


def test_uncovered_folder_fails(fw):
    (fw / "src" / "net").mkdir()
    (fw / "src" / "net" / "net.c").write_text("int net_init(void) { return 0; }\n", encoding="utf-8")
    errors, _ = check_architecture(fw)
    assert any(e.startswith("src/net:") and "fw-architecture-sync" in e for e in errors)


def test_ignored_build_output_is_not_scanned(fw):
    (fw / "build").mkdir()
    (fw / "build" / "generated.c").write_text("int x;\n", encoding="utf-8")
    assert check_architecture(fw)[0] == []


def test_missing_architecture_md_fails_and_deleted_folder_warns(fw):
    (fw / "src" / "drivers" / "ARCHITECTURE.md").unlink()
    edit_arch(fw, lambda a: a["modules"].update({"src/legacy": {"kind": "owned", "allowed_deps": []}}))
    errors, warnings = check_architecture(fw)
    assert any(e.startswith("src/drivers:") and "ARCHITECTURE.md" in e for e in errors)
    assert any(w.startswith("src/legacy:") and "no longer exists" in w for w in warnings)


def test_load_architecture_errors(repo):
    with pytest.raises(ArchitectureError, match="fw-harness-init"):
        load_architecture(repo)
    (repo / "harness" / "architecture.json").write_text("{", encoding="utf-8")
    with pytest.raises(ArchitectureError, match="not valid JSON"):
        load_architecture(repo)


def test_main_exit_codes(fw, monkeypatch, capsys):
    monkeypatch.chdir(fw)
    assert main([]) == 0
    assert "arch_check: passed" in capsys.readouterr().out
    edit_arch(fw, lambda a: a.update(grandfathered=[]))
    assert main([]) == 1
    assert "src/hal -> src/app" in capsys.readouterr().err
