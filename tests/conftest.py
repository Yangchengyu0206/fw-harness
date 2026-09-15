import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins" / "fw-c-harness" / "skills" / "fw-harness-init" / "templates" / "harness" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from helpers import git, make_repo, set_identity  # noqa: E402


@pytest.fixture(autouse=True)
def isolated_git_config(tmp_path_factory, monkeypatch):
    """Keep a contributor's own ~/.gitconfig (hooksPath, signing, identity) from affecting results."""
    empty = tmp_path_factory.mktemp("gitconfig") / "gitconfig"
    empty.write_text("", encoding="utf-8")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(empty))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_TERMINAL_PROMPT", "0")


@pytest.fixture
def repo(tmp_path):
    return make_repo(tmp_path / "fw", "Alice Chen", "alice@example.com")


@pytest.fixture
def team(tmp_path):
    seed = make_repo(tmp_path / "seed", "Seed", "seed@example.com")
    origin = tmp_path / "origin.git"
    git(tmp_path, "clone", "--bare", str(seed), str(origin))
    clones = {}
    for slug, name in [("alice", "Alice Chen"), ("bob", "Bob Lin")]:
        path = tmp_path / slug
        git(tmp_path, "clone", str(origin), str(path))
        set_identity(path, name, f"{slug}@example.com")
        clones[slug] = path
    return origin, clones
