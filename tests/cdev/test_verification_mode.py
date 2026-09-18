"""The Verification line in AGENTS.md is the one switch between the three levels, so it stays consistent."""
import pytest

from helpers import ROOT

CDEV = ROOT / "plugins" / "cdev"
SKILLS = CDEV / "skills"
AGENTS = SKILLS / "cdev-init" / "templates" / "AGENTS.md"
INIT = SKILLS / "cdev-init" / "SKILL.md"
MODES = ("off", "light", "full")
READERS = ("cdev-implement", "cdev-done", "cdev-target-verify", "cdev-feature")


def text(path):
    return path.read_text(encoding="utf-8")


def test_the_template_carries_the_line_and_explains_every_mode():
    body = text(AGENTS)
    assert "Verification: {{VERIFICATION}}" in body
    for mode in MODES:
        assert f"- `{mode}`:" in body, f"{mode} is not explained in AGENTS.md"


def test_init_fills_the_line_with_off():
    body = text(INIT)
    assert "{{VERIFICATION}}" in body
    row = next(line for line in body.splitlines() if "{{VERIFICATION}}" in line)
    assert "`off`" in row, "cdev-init starts every repository at off"


def test_init_offers_the_other_modes_in_the_one_question():
    body = text(INIT)
    handover = body[body.index("### 4. Hand the whole result over"):]
    for mode in MODES:
        assert f"`{mode}`" in handover, f"the handover does not offer {mode}"


@pytest.mark.parametrize("name", READERS)
def test_every_skill_that_acts_on_it_reads_the_line(name):
    assert "Verification:" in text(SKILLS / name / "SKILL.md"), f"{name} ignores the mode"
