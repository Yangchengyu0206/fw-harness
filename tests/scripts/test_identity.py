import pytest

from identity import IdentityError, current_identity, slug_for, slugify_email
from jsonio import write_json_atomic


@pytest.mark.parametrize("email, slug", [
    ("alice@example.com", "alice"),
    ("Alice.Chen@example.com", "alice-chen"),
    ("team+bob_lin@example.com", "bob-lin"),
    ("x-y9@example.com", "x-y9"),
])
def test_slugify_email(email, slug):
    assert slugify_email(email) == slug


def test_current_identity_reads_git_config(repo):
    assert current_identity(repo) == {"name": "Alice Chen", "email": "alice@example.com"}


def test_current_identity_fails_with_fix_hint(repo, tmp_path, monkeypatch):
    from helpers import git
    git(repo, "config", "--unset", "user.email")
    empty = tmp_path / "empty-gitconfig"
    empty.write_text("", encoding="utf-8")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(empty))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    with pytest.raises(IdentityError) as exc:
        current_identity(repo)
    assert "git config user.email" in str(exc.value)


def test_slug_for_uses_people_json_case_insensitive(repo):
    write_json_atomic(repo / "harness" / "people.json",
                      {"alice@example.com": {"slug": "achen", "display_name": "Alice"}})
    assert slug_for(repo, "ALICE@example.com") == "achen"
    assert slug_for(repo, "bob@example.com") == "bob"


def test_slug_for_without_people_json(repo):
    assert slug_for(repo, "team+Bob@example.com") == "bob"
