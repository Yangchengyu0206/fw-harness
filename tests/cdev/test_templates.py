"""The JSON templates cdev-init writes must parse once filled, and the guard rules must match what they claim."""
import json
import re
from pathlib import Path

import pytest

TEMPLATES = Path(__file__).resolve().parents[2] / "plugins" / "cdev" / "skills" / "cdev-init" / "templates"


def settings():
    text = (TEMPLATES / ".vscode" / "settings.json").read_text(encoding="utf-8")
    return json.loads(text.replace("{{READ_ONLY_GLOBS}}", '{"vendor/**": true}'))


def git_rule():
    rules = settings()["chat.tools.terminal.autoApprove"]
    key = next(key for key in rules if key.startswith("/^git"))
    assert rules[key] is False
    return re.compile(key[1:key.rindex("/")])


def test_settings_parse_once_filled():
    assert settings()["files.readonlyInclude"] == {"vendor/**": True}


@pytest.mark.parametrize("command", [
    "git push", "git push origin main", "git clean -fd", "git reset --hard HEAD~1",
    "git rebase main", "git filter-branch --all", "git checkout -- src/main.c",
])
def test_destructive_git_commands_wait_for_approval(command):
    assert git_rule().search(command)


@pytest.mark.parametrize("command", ["git status", "git checkout main", "git diff", "git pushd", "git log"])
def test_everyday_git_commands_are_not_held(command):
    assert not git_rule().search(command)


def test_hook_file_parses_and_names_both_events():
    hooks = json.loads((TEMPLATES / ".github" / "hooks" / "cdev.json").read_text(encoding="utf-8"))
    assert set(hooks["hooks"]) == {"SessionStart", "Stop"}
    for entries in hooks["hooks"].values():
        for entry in entries:
            assert "tools/hooks.py" in entry["command"] and entry["windows"].startswith("py -3")


def test_the_explorer_agent_holds_only_read_and_search_tools():
    text = (TEMPLATES / ".github" / "agents" / "cdev-explorer.agent.md").read_text(encoding="utf-8")
    front = text.split("---")[1]
    assert re.search(r"^tools:\s*\['read', 'search'\]\s*$", front, re.M)


def test_the_notes_index_starts_empty_and_hooks_can_read_it():
    text = (TEMPLATES / "NOTES.md").read_text(encoding="utf-8")
    assert "## Topics" in text and "none yet" in text
    assert not [line for line in text.splitlines() if line.startswith("- [")]


def section(heading):
    text = (TEMPLATES / "AGENTS.md").read_text(encoding="utf-8")
    return text.split(f"\n{heading}\n")[1].split("\n## ")[0]


def test_agents_md_says_where_notes_go_and_what_stays_out():
    text = section("## Notes that outlive a feature")
    assert "docs/notes/<topic>.md" in text and "NOTES.md" in text
    assert "one person's machine" in text, "personal facts must be kept out of the repository"


def test_agents_md_routes_by_what_the_answer_is_made_of():
    text = section("## Tools beyond this repository")
    assert "first" in text and "memory" in text
    assert "even when the question names a chip" in text


def test_agents_md_keeps_git_to_changes_and_history():
    text = section("## Using git")
    assert "git grep" in text and "git branch -a" in text
