"""Ratchet lists may only shrink. Entries are compared with the same file at a baseline ref (spec section 4.2)."""
from gitutil import git, git_ok

BASE_REF = "origin/main"


def parse_entries(text):
    entries = set()
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            entries.add(line)
    return entries


def baseline_ref(repo):
    if git_ok(repo, "rev-parse", "--verify", "--quiet", f"{BASE_REF}^{{commit}}"):
        return BASE_REF, None
    return "HEAD", (
        f"Warning: {BASE_REF} not found, so ratchets compare against HEAD and only catch uncommitted additions. "
        "Fix: add the origin remote and fetch main"
    )


def baseline_text(repo, ref, path):
    if not git_ok(repo, "cat-file", "-e", f"{ref}:{path}"):
        return None
    return git(repo, "show", f"{ref}:{path}")


def new_entries(current, baseline):
    """Entries in current that the baseline lacks. A list absent at the baseline is being introduced, so nothing is new."""
    if baseline is None:
        return []
    return sorted(set(current) - set(baseline))
