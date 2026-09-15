import pytest

from gitutil import GitError, git, git_ok, repo_root


def test_git_returns_stripped_stdout(repo):
    assert git(repo, "log", "-1", "--format=%s") == "harness: init"


def test_git_raises_with_command_and_stderr(repo):
    with pytest.raises(GitError) as exc:
        git(repo, "rev-parse", "no-such-ref")
    assert "git rev-parse no-such-ref" in str(exc.value)


def test_git_check_false_does_not_raise(repo):
    assert git(repo, "config", "no.such-key", check=False) == ""


def test_git_ok(repo):
    assert git_ok(repo, "rev-parse", "HEAD")
    assert not git_ok(repo, "rev-parse", "no-such-ref")


def test_repo_root_from_subdir(repo):
    assert repo_root(repo / "harness" / "tickets").resolve() == repo.resolve()
