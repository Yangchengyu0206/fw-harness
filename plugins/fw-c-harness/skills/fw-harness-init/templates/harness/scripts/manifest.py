"""The files the harness owns, split into managed and team-owned (spec sections 3.1 and 4)."""
import hashlib
from pathlib import Path

from review_docs import INSTRUCTIONS_PATH

VERSION_PATH = "harness/.harness-version"
PROPOSED_SUFFIX = ".harness-proposed"

MANAGED = (
    ".githooks/_python.sh",
    ".githooks/commit-msg",
    ".githooks/post-commit",
    ".githooks/post-merge",
    ".github/copilot-instructions.md",
    "Makefile",
    "init.ps1",
    "init.sh",
)
TEAM_OWNED = (
    ".clang-format",
    ".gitignore",
    "AGENTS.md",
    "CLAUDE.md",
    "docs/deviations/README.md",
    "docs/references/README.md",
    "harness/architecture.json",
    "harness/config.json",
    "harness/cppcheck-suppressions.txt",
    "harness/review-checklist.json",
    "harness/review-policy.json",
)
GENERATED = (INSTRUCTIONS_PATH,)
DIRS = (
    "harness/tickets",
    "harness/progress",
    "harness/handoff",
    "harness/reviews",
    "harness/evidence",
)
EXECUTABLE = (
    ".githooks/commit-msg",
    ".githooks/post-commit",
    ".githooks/post-merge",
    "init.sh",
)


def managed_files(templates):
    scripts = sorted("harness/scripts/" + path.name
                     for path in (Path(templates) / "harness" / "scripts").glob("*.py"))
    return sorted(set(MANAGED) | set(scripts))


def read_version(templates):
    return (Path(templates) / "VERSION").read_text(encoding="utf-8").strip()


def digest(data):
    return hashlib.sha256(data).hexdigest()
