import re

import pytest

from skilltools import (PLUGINS, all_skills, body, existing_skills, frontmatter, prose_files,
                        skill_path, skills_dir)

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


@pytest.mark.parametrize("plugin", sorted(PLUGINS))
def test_every_skill_folder_is_expected(plugin):
    folders = sorted(path.name for path in skills_dir(plugin).iterdir() if path.is_dir())
    assert folders == sorted(PLUGINS[plugin]["skills"])


@pytest.mark.parametrize("plugin,name", all_skills())
def test_skill_exists(plugin, name):
    assert skill_path(plugin, name).is_file(), f"{plugin}/{name}/SKILL.md is missing"


@pytest.mark.parametrize("plugin,name", existing_skills())
def test_name_matches_the_folder(plugin, name):
    fields = frontmatter(skill_path(plugin, name))
    assert fields["name"] == name and NAME_RE.match(fields["name"])
    assert len(fields["name"]) <= 64


@pytest.mark.parametrize("plugin,name", existing_skills())
def test_description_length_suits_both_tools(plugin, name):
    description = frontmatter(skill_path(plugin, name))["description"]
    assert 10 <= len(description) <= 1024, f"{name}: description is {len(description)} characters"


@pytest.mark.parametrize("plugin,name", existing_skills())
def test_invocation_matches_the_plan(plugin, name):
    fields = frontmatter(skill_path(plugin, name))
    if name in PLUGINS[plugin]["user_invoked"]:
        assert fields.get("disable-model-invocation") == "true"
        assert "Use when" not in fields["description"], "a user-invoked description carries no trigger list"
    else:
        assert "disable-model-invocation" not in fields
        assert "Use when" in fields["description"], "a model-invoked description names its triggers"


@pytest.mark.parametrize("plugin,name", existing_skills())
def test_skill_body_holds_no_unfinished_marker(plugin, name):
    text = body(skill_path(plugin, name))
    assert "TODO" not in text and "TBD" not in text


@pytest.mark.parametrize("plugin,name", existing_skills())
def test_relative_links_resolve(plugin, name):
    path = skill_path(plugin, name)
    for target in LINK_RE.findall(body(path)):
        if target.startswith(("http://", "https://", "#")):
            continue
        assert (path.parent / target.split("#")[0]).exists(), f"{name}: broken link {target}"


def test_no_em_dash_in_shipped_prose():
    offenders = [str(path) for path in prose_files() if chr(0x2014) in path.read_text(encoding="utf-8")]
    assert offenders == []


# Every ticket.py command line we ship must parse with the real CLI parser.
TICKET_LINE_RE = re.compile(r"ticket\.py ([^`\n]+)")
PLACEHOLDERS = {
    "FW-NNNN": "FW-0001", "<id>": "FW-0001", "<status>": "active", "<title>": "a title",
    "<area>": "drivers/uart", "<reason>": "waiting for the board", "<path>": "harness/reviews/r.md",
    "<file>": "harness/reviews/r.md", "<count>": "0", "<sub>": "show", "N": "0",
    "<step>": "loopback", "<date>": "2026-09-16", "<your-slug>": "alice",
}


def sanitize(tokens):
    cleaned = []
    for token in tokens:
        token = token.strip("[]")
        if not token:
            continue
        if token in PLACEHOLDERS:
            token = PLACEHOLDERS[token]
        elif token.startswith("<") or "<" in token:
            token = re.sub(r"<[^>]*>", "x", token)
        cleaned.append(token)
    return cleaned


def documented_ticket_commands():
    import shlex
    found = []
    for path in prose_files():
        for match in TICKET_LINE_RE.finditer(path.read_text(encoding="utf-8")):
            line = match.group(1).strip().rstrip("`.,")
            if not line or line.startswith("--"):
                continue
            found.append((path.name, line, sanitize(shlex.split(line))))
    return found


def test_documented_ticket_commands_parse():
    from ticket import build_parser
    parser = build_parser()
    broken = []
    for name, line, argv in documented_ticket_commands():
        try:
            parser.parse_args(argv)
        except SystemExit:
            broken.append(f"{name}: ticket.py {line}")
    assert broken == []


# Every feature.py command line we ship must parse with the real CLI parser.
FEATURE_LINE_RE = re.compile(r"feature\.py ([^`\n]+)")
FEATURE_PLACEHOLDERS = {"F-NNN": "F-001", "...": "x", "<id>": "F-001", "<status>": "active"}


def documented_feature_commands():
    import shlex
    found = []
    for path in prose_files():
        for match in FEATURE_LINE_RE.finditer(path.read_text(encoding="utf-8")):
            text = match.group(1).strip().rstrip("`.,")
            if not text or text.startswith("--file"):
                continue
            tokens = []
            for token in shlex.split(text):
                token = token.strip("[]")
                if token:
                    tokens.append(FEATURE_PLACEHOLDERS.get(token, re.sub(r"<[^>]*>", "x", token)))
            found.append((path.name, text, tokens))
    return found


def test_documented_feature_commands_parse():
    import sys
    from helpers import ROOT
    sys.path.insert(0, str(ROOT / "plugins" / "cdev" / "skills" / "cdev-init" / "templates" / "tools"))
    from feature import build_parser
    parser = build_parser()
    broken = []
    for name, text, argv in documented_feature_commands():
        try:
            parser.parse_args(argv)
        except SystemExit:
            broken.append(f"{name}: feature.py {text}")
    assert broken == []
