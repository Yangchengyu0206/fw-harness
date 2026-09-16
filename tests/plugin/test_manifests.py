import json

from helpers import ROOT, TEMPLATES
from skilltools import PLUGIN, SKILL_NAMES

CLAUDE_MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
CLAUDE_PLUGIN = PLUGIN / ".claude-plugin" / "plugin.json"
COPILOT_MARKETPLACE = ROOT / ".github" / "plugin" / "marketplace.json"
COPILOT_PLUGIN = PLUGIN / "plugin.json"
COPILOT_KEYS = {"$schema", "name", "version", "description", "author", "homepage",
                "repository", "license", "keywords", "extensions"}
PLUGIN_NAME = "fw-c-harness"
MARKETPLACE_NAME = "fw-harness"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def version():
    return (TEMPLATES / "VERSION").read_text(encoding="utf-8").strip()


def test_claude_marketplace_points_at_the_plugin():
    data = load(CLAUDE_MARKETPLACE)
    assert data["name"] == MARKETPLACE_NAME and data["owner"]["name"]
    entry, = data["plugins"]
    assert entry["name"] == PLUGIN_NAME
    assert (ROOT / entry["source"].lstrip("./")).is_dir()
    assert entry["description"] and entry["keywords"]


def test_claude_plugin_lists_every_skill_once():
    data = load(CLAUDE_PLUGIN)
    assert data["name"] == PLUGIN_NAME and data["license"] == "MIT"
    listed = data["skills"]
    assert listed == sorted(listed) and len(listed) == len(set(listed))
    assert sorted(path.rsplit("/", 1)[-1] for path in listed) == sorted(SKILL_NAMES)
    for path in listed:
        assert (PLUGIN / path.lstrip("./")).is_dir(), path


def test_copilot_marketplace_points_at_the_plugin():
    data = load(COPILOT_MARKETPLACE)
    assert data["name"] == MARKETPLACE_NAME and data["metadata"]["description"]
    entry, = data["plugins"]
    assert entry["name"] == PLUGIN_NAME and entry["version"] == version()
    assert (ROOT / entry["source"]).is_dir()


def test_copilot_plugin_uses_only_schema_keys():
    data = load(COPILOT_PLUGIN)
    assert data["$schema"] == "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
    assert data["name"] == PLUGIN_NAME
    assert set(data) <= COPILOT_KEYS, f"keys outside the schema: {set(data) - COPILOT_KEYS}"


def test_both_manifests_carry_the_template_version():
    assert load(CLAUDE_PLUGIN)["version"] == version()
    assert load(COPILOT_PLUGIN)["version"] == version()
