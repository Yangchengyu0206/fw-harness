"""install_local.py runs from the unzipped package, so it is tested there."""
import importlib.util
import json
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import pack_cdev  # noqa: E402


@pytest.fixture(scope="module")
def installer(tmp_path_factory):
    out = tmp_path_factory.mktemp("pkg")
    with zipfile.ZipFile(pack_cdev.build(out)) as archive:
        archive.extractall(out)
    spec = importlib.util.spec_from_file_location("install_local", out / "cdev" / "install_local.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def shipped():
    return sorted(path.parent.name for path in (ROOT / "plugins" / "cdev" / "skills").glob("*/SKILL.md"))


def test_the_settings_snippet_enables_plugins_with_a_forward_slash_path(installer, capsys):
    assert installer.main([]) == 0
    out = capsys.readouterr().out
    snippet = json.loads(out[out.index("{"):out.rindex("}") + 1])
    assert snippet["chat.plugins.enabled"] is True
    [path] = snippet["chat.pluginLocations"]
    assert "\\" not in path and path.endswith("/cdev")


@pytest.mark.parametrize("tool, folder", [("copilot", ".github/skills"), ("claude", ".claude/skills")])
def test_repo_copies_every_skill_and_the_licence(installer, tmp_path, capsys, tool, folder):
    assert installer.main(["--repo", str(tmp_path), "--tool", tool]) == 0
    target = tmp_path / folder
    assert sorted(path.parent.name for path in target.glob("*/SKILL.md")) == shipped()
    assert (target / "LICENSE").is_file() and (target / "THIRD_PARTY_NOTICES.md").is_file()
    assert not list(target.rglob("__pycache__"))


def test_a_rerun_names_what_it_replaced_and_what_is_no_longer_shipped(installer, tmp_path, capsys):
    installer.main(["--repo", str(tmp_path)])
    (tmp_path / ".github" / "skills" / "cdev-retired").mkdir()
    capsys.readouterr()
    assert installer.main(["--repo", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert f"Replaced {len(shipped())}" in out
    assert "cdev-retired" in out and (tmp_path / ".github" / "skills" / "cdev-retired").is_dir()


def test_a_missing_folder_is_refused(installer, tmp_path):
    with pytest.raises(SystemExit, match="is not a folder"):
        installer.main(["--repo", str(tmp_path / "nope")])
