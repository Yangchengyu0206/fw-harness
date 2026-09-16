import pytest

from skilltools import DOCS, PLUGIN, SKILL_NAMES

HEADINGS = ("## What it does", "## When to reach for it", "## Common questions", "## It is working if")


@pytest.mark.parametrize("name", SKILL_NAMES)
def test_every_skill_has_a_page(name):
    page = DOCS / f"{name}.md"
    assert page.is_file(), f"docs/skills/{name}.md is missing"
    text = page.read_text(encoding="utf-8")
    assert text.startswith(f"# {name}\n")
    for heading in HEADINGS:
        assert heading in text, f"{name}: {heading} is missing"


def test_no_page_without_a_skill():
    pages = sorted(path.stem for path in DOCS.glob("*.md") if path.name != "README.md")
    assert pages == sorted(SKILL_NAMES)


def test_plugin_readme_covers_both_tools():
    text = (PLUGIN / "README.md").read_text(encoding="utf-8")
    assert "/plugin marketplace add" in text and "copilot plugin marketplace add" in text
    assert "disable-model-invocation" in text, "the invocation difference between the tools is stated"
    for name in SKILL_NAMES:
        assert name in text, f"{name} is not listed in the plugin README"
