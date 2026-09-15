"""Identity comes only from git config user.name and user.email."""
import re
from pathlib import Path

from gitutil import git
from jsonio import read_json


class IdentityError(RuntimeError):
    pass


def slugify_email(email):
    local = email.split("@", 1)[0]
    if "+" in local:
        local = local.split("+", 1)[1]
    return re.sub(r"[^a-z0-9-]", "-", local.lower())


def current_identity(repo):
    name = git(repo, "config", "user.name", check=False)
    email = git(repo, "config", "user.email", check=False)
    missing = [key for key, value in (("user.name", name), ("user.email", email)) if not value]
    if missing:
        unset = ", ".join(f"git config {key}" for key in missing)
        raise IdentityError(
            f"Identity check failed: {unset} not set. "
            'Fix: git config user.name "Your Name"; git config user.email you@example.com'
        )
    return {"name": name, "email": email}


def slug_for(repo, email):
    people_path = Path(repo) / "harness" / "people.json"
    if people_path.exists():
        people = {key.lower(): value for key, value in read_json(people_path).items()}
        entry = people.get(email.lower())
        if entry and entry.get("slug"):
            return entry["slug"]
    return slugify_email(email)
