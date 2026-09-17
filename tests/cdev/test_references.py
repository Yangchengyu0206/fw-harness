import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CDEV = ROOT / "plugins" / "cdev"
REFS = CDEV / "skills" / "cdev-implement" / "references"
INIT = CDEV / "skills" / "cdev-init"
DOMAINS = ("c", "firmware", "linux-driver", "windows-driver", "python")
SECTIONS = ("## Rules", "## Review checklist", "## Debugging anchors", "## Build and test")
SEVERITIES = ("### Critical", "### Important", "### Suggestion")
PLACEHOLDER_RE = re.compile(r"\{\{([A-Z_]+)\}\}")


@pytest.mark.parametrize("domain", DOMAINS)
def test_reference_has_the_four_sections_in_order(domain):
    text = (REFS / f"{domain}.md").read_text(encoding="utf-8")
    positions = [text.find(section) for section in SECTIONS]
    assert all(position >= 0 for position in positions), f"{domain}: missing a section"
    assert positions == sorted(positions), f"{domain}: sections are out of order"


@pytest.mark.parametrize("domain", DOMAINS)
def test_review_checklist_has_the_three_severities(domain):
    text = (REFS / f"{domain}.md").read_text(encoding="utf-8")
    checklist = text[text.find("## Review checklist"):text.find("## Debugging anchors")]
    for severity in SEVERITIES:
        assert severity in checklist, f"{domain}: {severity} is missing from the review checklist"


def test_every_template_placeholder_is_explained_by_cdev_init():
    skill = (INIT / "SKILL.md").read_text(encoding="utf-8")
    for template in (INIT / "templates").glob("*.md"):
        for name in PLACEHOLDER_RE.findall(template.read_text(encoding="utf-8")):
            token = "{{" + name + "}}"
            assert token in skill, f"{template.name}: {token} is not explained in cdev-init"
