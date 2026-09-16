from pathlib import Path

from helpers import ROOT

PLUGIN = ROOT / "plugins" / "fw-c-harness"
SKILLS = PLUGIN / "skills"
DOCS = ROOT / "docs" / "skills"

SKILL_NAMES = (
    "fw-harness-init",
    "fw-harness-upgrade",
    "fw-architecture-sync",
    "fw-session-start",
    "fw-ticket",
    "fw-hil-verify",
    "fw-done",
    "fw-c-implement",
    "fw-c-review",
    "fw-c-test-gap",
    "fw-c-debug",
    "fw-misra-deviation",
    "fw-guide",
)
USER_INVOKED = {
    "fw-harness-init", "fw-harness-upgrade", "fw-session-start",
    "fw-hil-verify", "fw-done", "fw-guide",
}


def skill_path(name):
    return SKILLS / name / "SKILL.md"


def existing_skills():
    return [name for name in SKILL_NAMES if skill_path(name).is_file()]


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
    """Every Markdown file this repository ships, minus the plans and specs."""
    found = list(SKILLS.rglob("*.md"))
    found += list(DOCS.glob("*.md"))
    found += [PLUGIN / "README.md", ROOT / "README.md", ROOT / "README.zh-TW.md",
              ROOT / "THIRD_PARTY_NOTICES.md", ROOT / "docs" / "manual-checklist.md"]
    return [path for path in found if path.is_file()]
