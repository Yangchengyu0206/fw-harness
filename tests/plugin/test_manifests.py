import json

import pytest

from helpers import ROOT, TEMPLATES
from skilltools import PLUGINS, plugin_dir

CLAUDE_MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
COPILOT_MARKETPLACE = ROOT / ".github" / "plugin" / "marketplace.json"
COPILOT_KEYS = {"$schema", "name", "version", "description", "author", "homepage",
                "repository", "license", "keywords", "extensions"}
MARKETPLACE_NAME = "fw-harness"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def claude_manifest(plugin):
    return plugin_dir(plugin) / ".claude-plugin" / "plugin.json"


def copilot_manifest(plugin):
    return plugin_dir(plugin) / "plugin.json"


def plugin_version(plugin):
    if plugin == "fw-c-harness":
        return (TEMPLATES / "VERSION").read_text(encoding="utf-8").strip()
    return load(claude_manifest(plugin))["version"]


def entries(path):
    return {entry["name"]: entry for entry in load(path)["plugins"]}


def test_claude_marketplace_lists_every_plugin():
    data = load(CLAUDE_MARKETPLACE)
    assert data["name"] == MARKETPLACE_NAME and data["owner"]["name"]
    listed = entries(CLAUDE_MARKETPLACE)
    assert sorted(listed) == sorted(PLUGINS)
    for name, entry in listed.items():
        assert (ROOT / entry["source"].lstrip("./")).is_dir(), name
        assert entry["description"] and entry["keywords"]


def test_copilot_marketplace_lists_every_plugin():
    data = load(COPILOT_MARKETPLACE)
    assert data["name"] == MARKETPLACE_NAME and data["metadata"]["description"]
    listed = entries(COPILOT_MARKETPLACE)
    assert sorted(listed) == sorted(PLUGINS)
    for name, entry in listed.items():
        assert (ROOT / entry["source"]).is_dir(), name
        assert entry["version"] == plugin_version(name)


@pytest.mark.parametrize("plugin", sorted(PLUGINS))
def test_claude_plugin_lists_every_skill_once(plugin):
    data = load(claude_manifest(plugin))
    assert data["name"] == plugin and data["license"] == "MIT"
    listed = data["skills"]
    assert listed == sorted(listed) and len(listed) == len(set(listed))
    assert sorted(path.rsplit("/", 1)[-1] for path in listed) == sorted(PLUGINS[plugin]["skills"])
    for path in listed:
        assert (plugin_dir(plugin) / path.lstrip("./")).is_dir(), path


@pytest.mark.parametrize("plugin", sorted(PLUGINS))
def test_copilot_plugin_uses_only_schema_keys(plugin):
    data = load(copilot_manifest(plugin))
    assert data["$schema"] == "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
    assert data["name"] == plugin
    assert set(data) <= COPILOT_KEYS, f"keys outside the schema: {set(data) - COPILOT_KEYS}"


@pytest.mark.parametrize("plugin", sorted(PLUGINS))
def test_both_manifests_carry_the_same_version(plugin):
    assert load(claude_manifest(plugin))["version"] == plugin_version(plugin)
    assert load(copilot_manifest(plugin))["version"] == plugin_version(plugin)
