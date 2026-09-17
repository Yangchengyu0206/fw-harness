import pytest

from helpers import ROOT
from skilltools import DOCS, PLUGINS, all_skills, plugin_dir

HEADINGS = ("## What it does", "## When to reach for it", "## Common questions", "## It is working if")
README = ROOT / "README.md"
README_ZH = ROOT / "README.zh-TW.md"
NOTICES = ROOT / "THIRD_PARTY_NOTICES.md"
CHECKLIST = ROOT / "docs" / "manual-checklist.md"
CJK_FIRST, CJK_LAST = chr(0x4E00), chr(0x9FFF)


def has_cjk(text):
    return any(CJK_FIRST <= ch <= CJK_LAST for ch in text)


@pytest.mark.parametrize("plugin,name", all_skills())
def test_every_skill_has_a_page(plugin, name):
    page = DOCS / f"{name}.md"
    assert page.is_file(), f"docs/skills/{name}.md is missing"
    text = page.read_text(encoding="utf-8")
    assert text.startswith(f"# {name}\n")
    for heading in HEADINGS:
        assert heading in text, f"{name}: {heading} is missing"


def test_no_page_without_a_skill():
    pages = sorted(path.stem for path in DOCS.glob("*.md") if path.name != "README.md")
    assert pages == sorted(name for _, name in all_skills())


@pytest.mark.parametrize("plugin", sorted(PLUGINS))
def test_plugin_readme_covers_both_tools(plugin):
    text = (plugin_dir(plugin) / "README.md").read_text(encoding="utf-8")
    assert "/plugin marketplace add" in text and "copilot plugin marketplace add" in text
    assert f"{plugin}@fw-harness" in text
    assert "disable-model-invocation" in text, "the invocation difference between the tools is stated"
    for name in PLUGINS[plugin]["skills"]:
        assert name in text, f"{name} is not listed in the {plugin} README"


def test_readme_pair_covers_the_same_sections():
    english = README.read_text(encoding="utf-8")
    chinese = README_ZH.read_text(encoding="utf-8")
    for fragment in ("fw-c-harness", "cdev", "/plugin marketplace add", "copilot plugin marketplace add", "MIT"):
        assert fragment in english and fragment in chinese, fragment
    assert "README.zh-TW.md" in english and "README.md" in chinese


def test_readme_is_english_and_the_translation_is_not():
    assert not has_cjk(README.read_text(encoding="utf-8"))
    assert has_cjk(README_ZH.read_text(encoding="utf-8"))


def test_notices_credit_every_adapted_source():
    text = NOTICES.read_text(encoding="utf-8")
    for source in ("github/awesome-copilot", "mattpocock/skills", "MIT"):
        assert source in text
    for path in ("expert-embedded-c-engineer.agent.md", "test-gap-audit", "security-review",
                 "code-review-generic.instructions.md", "code-review", "diagnosing-bugs",
                 "hitl-loop.template.sh", "bug-reproduction-brief", "gem-debugger.agent.md",
                 "gem-reviewer.agent.md"):
        assert path in text, f"{path} is adapted but not credited"
    for plugin in PLUGINS:
        assert f"plugins/{plugin}/" in text, f"{plugin} has adapted files and no entry"


def test_checklist_covers_every_user_invoked_skill():
    text = CHECKLIST.read_text(encoding="utf-8")
    assert "Claude Code" in text and "Copilot" in text
    for plugin, spec in PLUGINS.items():
        for name in sorted(spec["user_invoked"]):
            assert name in text, f"{name} is typed by a human and is not in the checklist"
