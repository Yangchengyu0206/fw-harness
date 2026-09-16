import re

import pytest

from skilltools import (SKILLS, SKILL_NAMES, USER_INVOKED, body, existing_skills, frontmatter,
                        prose_files, skill_path)

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def test_every_skill_folder_is_expected():
    folders = sorted(path.name for path in SKILLS.iterdir() if path.is_dir())
    assert folders == sorted(SKILL_NAMES)


@pytest.mark.parametrize("name", SKILL_NAMES)
def test_skill_exists(name):
    assert skill_path(name).is_file(), f"{name}/SKILL.md is missing"


@pytest.mark.parametrize("name", existing_skills())
def test_name_matches_the_folder(name):
    fields = frontmatter(skill_path(name))
    assert fields["name"] == name and NAME_RE.match(fields["name"])
    assert len(fields["name"]) <= 64


@pytest.mark.parametrize("name", existing_skills())
def test_description_length_suits_both_tools(name):
    description = frontmatter(skill_path(name))["description"]
    assert 10 <= len(description) <= 1024, f"{name}: description is {len(description)} characters"


@pytest.mark.parametrize("name", existing_skills())
def test_invocation_matches_the_plan(name):
    fields = frontmatter(skill_path(name))
    if name in USER_INVOKED:
        assert fields.get("disable-model-invocation") == "true"
        assert "Use when" not in fields["description"], "a user-invoked description carries no trigger list"
    else:
        assert "disable-model-invocation" not in fields
        assert "Use when" in fields["description"], "a model-invoked description names its triggers"


@pytest.mark.parametrize("name", existing_skills())
def test_skill_body_holds_no_unfinished_marker(name):
    text = body(skill_path(name))
    assert "TODO" not in text and "TBD" not in text


@pytest.mark.parametrize("name", existing_skills())
def test_relative_links_resolve(name):
    path = skill_path(name)
    for target in LINK_RE.findall(body(path)):
        if target.startswith(("http://", "https://", "#")):
            continue
        assert (path.parent / target.split("#")[0]).exists(), f"{name}: broken link {target}"


def test_no_em_dash_in_shipped_prose():
    offenders = [str(path) for path in prose_files() if "—" in path.read_text(encoding="utf-8")]
    assert offenders == []
