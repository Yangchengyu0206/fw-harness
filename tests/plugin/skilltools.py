from pathlib import Path

from helpers import ROOT

DOCS = ROOT / "docs" / "skills"

PLUGINS = {
    "fw-c-harness": {
        "skills": (
            "fw-harness-init", "fw-harness-upgrade", "fw-architecture-sync", "fw-session-start",
            "fw-ticket", "fw-hil-verify", "fw-done", "fw-c-implement", "fw-c-review",
            "fw-c-test-gap", "fw-c-debug", "fw-misra-deviation", "fw-review-respond", "fw-guide",
        ),
        "user_invoked": {
            "fw-harness-init", "fw-harness-upgrade", "fw-session-start",
            "fw-hil-verify", "fw-done", "fw-guide",
        },
    },
    "cdev": {
        "skills": (
            "cdev-init", "cdev-session-start", "cdev-feature", "cdev-architecture-sync",
            "cdev-implement", "cdev-review", "cdev-test-gap", "cdev-debug",
            "cdev-target-verify", "cdev-checkpoint", "cdev-done", "cdev-guide",
        ),
        "user_invoked": {
            "cdev-init", "cdev-session-start", "cdev-target-verify", "cdev-checkpoint", "cdev-done",
            "cdev-guide",
        },
    },
}


def plugin_dir(plugin):
    return ROOT / "plugins" / plugin


def skills_dir(plugin):
    return plugin_dir(plugin) / "skills"


def skill_path(plugin, name):
    return skills_dir(plugin) / name / "SKILL.md"


def all_skills():
    return [(plugin, name) for plugin, spec in PLUGINS.items() for name in spec["skills"]]


def existing_skills():
    return [(plugin, name) for plugin, name in all_skills() if skill_path(plugin, name).is_file()]


def split(path):
    text = Path(path).read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path} has no frontmatter block"
    end = text.index("\n---\n", 3)
    return text[4:end], text[end + 5:]


def frontmatter(path):
    block, _ = split(path)
    fields = {}
    for line in block.splitlines():
        if not line.strip():
            continue
        key, _, value = line.partition(":")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        fields[key.strip()] = value
    return fields


def body(path):
    return split(path)[1]


def prose_files():
    """Every Markdown file this repository ships, minus the specs and local plans."""
    found = []
    for plugin in PLUGINS:
        if skills_dir(plugin).is_dir():
            found += list(skills_dir(plugin).rglob("*.md"))
        found.append(plugin_dir(plugin) / "README.md")
    found += list(DOCS.glob("*.md"))
    found += [ROOT / "README.md", ROOT / "README.zh-TW.md",
              ROOT / "THIRD_PARTY_NOTICES.md", ROOT / "docs" / "manual-checklist.md"]
    return [path for path in found if path.is_file()]
