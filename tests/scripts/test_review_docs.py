import json

import pytest

from helpers import TEMPLATES, make_repo
from review_docs import (CHECKLIST_PATH, POLICY_PATH, ReviewDocsError, load_checklist, load_policy,
                         render_instructions, validate_checklist, validate_policy)

CHECKLIST = json.loads((TEMPLATES / "harness" / "review-checklist.json").read_text(encoding="utf-8"))
POLICY = json.loads((TEMPLATES / "harness" / "review-policy.json").read_text(encoding="utf-8"))


@pytest.fixture
def repo(tmp_path):
    fw = make_repo(tmp_path / "fw", "Alice Chen", "alice@example.com")
    for name in (CHECKLIST_PATH, POLICY_PATH):
        (fw / name).write_text((TEMPLATES / name).read_text(encoding="utf-8"), encoding="utf-8")
    return fw


def test_shipped_checklist_and_policy_are_valid():
    assert validate_checklist(CHECKLIST) == [] and validate_policy(POLICY) == []


def test_validate_checklist_names_the_broken_key():
    broken = {"version": 1, "axes": [], "severities": [{"level": "critical"}]}
    errors = validate_checklist(broken)
    assert any("axes" in error for error in errors)
    assert any("severities[0]" in error for error in errors)


def test_validate_policy_rejects_an_unknown_misra_mode():
    policy = json.loads(json.dumps(POLICY))
    policy["misra"]["mode"] = "strict"
    assert any("misra.mode" in error for error in validate_policy(policy))


def test_load_reports_a_missing_file_with_a_fix(tmp_path):
    empty = make_repo(tmp_path / "empty", "Alice Chen", "alice@example.com")
    with pytest.raises(ReviewDocsError, match="fw-harness-init"):
        load_checklist(empty)


def test_render_instructions_covers_every_axis_and_severity(repo):
    text = render_instructions(load_checklist(repo), load_policy(repo))
    assert text.startswith('---\napplyTo: "**/*.{c,h}"\n---\n')
    assert "harness/review-checklist.json" in text
    for axis in CHECKLIST["axes"]:
        assert f"## {axis['title']}" in text
    for severity in CHECKLIST["severities"]:
        assert severity["label"] in text
        for item in severity["items"]:
            assert item in text
    assert "MISRA C:2012" in text and "advisory" in text


def test_render_instructions_is_deterministic(repo):
    checklist, policy = load_checklist(repo), load_policy(repo)
    assert render_instructions(checklist, policy) == render_instructions(checklist, policy)
