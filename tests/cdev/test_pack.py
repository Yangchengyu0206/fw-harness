"""The offline package is what a colleague without marketplace access installs, so its contents are pinned."""
import json
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import pack_cdev  # noqa: E402

PLUGIN = ROOT / "plugins" / "cdev"
REQUIRED = (
    "cdev/plugin.json",
    "cdev/.claude-plugin/plugin.json",
    "cdev/README.md",
    "cdev/README.zh-TW.md",
    "cdev/INSTALL.md",
    "cdev/INSTALL.zh-TW.md",
    "cdev/LICENSE",
    "cdev/THIRD_PARTY_NOTICES.md",
    "cdev/install_local.py",
    "cdev/skills/cdev-init/templates/tools/feature.py",
    "cdev/skills/cdev-init/templates/tools/doc_check.py",
    "cdev/skills/cdev-init/templates/.vscode/settings.json",
    "cdev/skills/cdev-init/templates/.github/instructions/architecture.instructions.md",
    "cdev/skills/cdev-init/templates/.github/hooks/cdev.json",
    "cdev/skills/cdev-init/templates/.github/agents/cdev-explorer.agent.md",
    "cdev/skills/cdev-init/templates/tools/hooks.py",
)


@pytest.fixture(scope="module")
def names(tmp_path_factory):
    target = pack_cdev.build(tmp_path_factory.mktemp("dist"))
    assert target.name == f"cdev-{pack_cdev.version()}.zip"
    with zipfile.ZipFile(target) as archive:
        return archive.namelist()


@pytest.mark.parametrize("name", REQUIRED)
def test_the_package_holds_what_an_install_needs(name, names):
    assert name in names


def test_every_skill_ships(names):
    packed = sorted(name.split("/")[2] for name in names if name.endswith("/SKILL.md"))
    listed = sorted(path.rsplit("/", 1)[-1]
                    for path in json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["skills"])
    assert packed == listed


def test_no_build_leftovers_ship(names):
    assert [name for name in names if name.endswith(".pyc") or "__pycache__" in name] == []


def test_the_installer_offers_both_routes():
    text = (ROOT / "scripts" / "install_local.py").read_text(encoding="utf-8")
    assert "chat.pluginLocations" in text
    assert ".github/skills" in text and ".claude/skills" in text


def test_the_install_guide_names_the_setting_and_both_routes():
    for name in ("INSTALL.md", "INSTALL.zh-TW.md"):
        text = (PLUGIN / name).read_text(encoding="utf-8")
        assert "chat.pluginLocations" in text, name
        assert "--repo" in text and "cdev-init" in text and "cdev-upgrade" in text, name
