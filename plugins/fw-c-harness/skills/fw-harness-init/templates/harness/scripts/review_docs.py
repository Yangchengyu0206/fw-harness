"""Review checklist source and the Copilot instructions generated from it (spec section 7)."""
import json
from pathlib import Path

from jsonio import read_json

CHECKLIST_PATH = "harness/review-checklist.json"
POLICY_PATH = "harness/review-policy.json"
INSTRUCTIONS_PATH = ".github/instructions/c-fw-review.instructions.md"
MISRA_MODES = ("off", "advisory", "required")
MODE_NOTES = {
    "off": "MISRA is not part of this review.",
    "advisory": "MISRA findings rank at most the lowest severity and never block a merge.",
    "required": "Breaking a required MISRA rule without a record in docs/deviations/ is a critical finding.",
}


class ReviewDocsError(ValueError):
    pass


def _is_str_list(value):
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item for item in value)


def validate_checklist(checklist):
    if not isinstance(checklist, dict):
        return ["checklist must be a JSON object"]
    errors = []
    if checklist.get("version") != 1:
        errors.append("version must be 1")
    axes = checklist.get("axes")
    if not (isinstance(axes, list) and axes):
        errors.append("axes must be a non-empty array")
    else:
        for index, axis in enumerate(axes):
            if not (isinstance(axis, dict) and all(isinstance(axis.get(key), str) and axis.get(key)
                                                   for key in ("key", "title", "question"))):
                errors.append(f"axes[{index}] must have key, title, and question")
    severities = checklist.get("severities")
    if not (isinstance(severities, list) and severities):
        errors.append("severities must be a non-empty array")
    else:
        for index, severity in enumerate(severities):
            if not isinstance(severity, dict):
                errors.append(f"severities[{index}] must be an object")
                continue
            if not all(isinstance(severity.get(key), str) and severity.get(key)
                       for key in ("level", "icon", "label")):
                errors.append(f"severities[{index}] must have level, icon, and label")
            if not _is_str_list(severity.get("items")):
                errors.append(f"severities[{index}].items must be a non-empty array of strings")
    if not _is_str_list(checklist.get("finding_fields")):
        errors.append("finding_fields must be a non-empty array of strings")
    return errors


def validate_policy(policy):
    if not isinstance(policy, dict):
        return ["policy must be a JSON object"]
    errors = []
    misra = policy.get("misra")
    if not isinstance(misra, dict):
        errors.append("misra must be an object with standard and mode")
    else:
        if not isinstance(misra.get("standard"), str) or not misra.get("standard"):
            errors.append("misra.standard must be the standard name")
        if misra.get("mode") not in MISRA_MODES:
            errors.append(f"misra.mode must be one of {', '.join(MISRA_MODES)}")
    if not _is_str_list(policy.get("block_on")):
        errors.append("block_on must be a non-empty array of severity levels")
    if not isinstance(policy.get("forbid_self_review"), bool):
        errors.append("forbid_self_review must be true or false")
    return errors


def _load(repo, relative, validator):
    path = Path(repo) / relative
    if not path.is_file():
        raise ReviewDocsError(f"{relative} not found. Fix: run fw-harness-init to create it")
    try:
        data = read_json(path)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ReviewDocsError(f"{relative} is not valid JSON ({exc}). Fix: repair it or restore it from git") from exc
    errors = validator(data)
    if errors:
        raise ReviewDocsError(f"{relative} is invalid:\n- " + "\n- ".join(errors))
    return data


def load_checklist(repo):
    return _load(repo, CHECKLIST_PATH, validate_checklist)


def load_policy(repo):
    return _load(repo, POLICY_PATH, validate_policy)


def render_instructions(checklist, policy):
    mode = policy["misra"]["mode"]
    lines = ["---", 'applyTo: "**/*.{c,h}"', "---", "",
             "# C firmware review",
             "",
             f"Generated from {CHECKLIST_PATH} and {POLICY_PATH}. Edit those files, not this one.",
             "",
             "Review every changed C file along the axes below and report them separately, "
             "without merging or reranking them.",
             ""]
    for axis in checklist["axes"]:
        lines += [f"## {axis['title']}", "", axis["question"], ""]
    lines += ["## Severity", ""]
    for severity in checklist["severities"]:
        lines += [f"### {severity['icon']} {severity['label']}", ""]
        lines += [f"- {item}" for item in severity["items"]]
        lines.append("")
    lines += ["## MISRA", "",
              f"Standard: {policy['misra']['standard']}. Mode: {mode}. {MODE_NOTES[mode]}",
              "",
              "## Reporting", "",
              "Each finding carries: " + ", ".join(checklist["finding_fields"]) + ".",
              "",
              "Verify each finding before reporting it: re-read the code and rule out a problem "
              "that is already handled before this point. Propose a patch and leave applying it to a human.",
              ""]
    return "\n".join(lines)
