"""Ticket ID allocation and renumbering. An ID is claimed only once the commit creating it is merged into main."""
import json
import sys
from pathlib import Path

from gitutil import git, git_ok
from tickets import TICKET_ID_RE, format_id, load_ticket, parse_id, save_ticket, ticket_path, tickets_dir

OFFLINE_WARNING = (
    "Warning: git fetch origin main failed (offline or no origin). "
    "Ticket IDs come from local tickets only and may clash at merge time."
)


class RenumberError(RuntimeError):
    pass


def _warn_stderr(message):
    print(message, file=sys.stderr)


def local_ids(repo):
    directory = tickets_dir(repo)
    if not directory.exists():
        return set()
    return {parse_id(path.stem) for path in directory.glob("FW-*.json") if TICKET_ID_RE.match(path.stem)}


def remote_ids(repo, warn=_warn_stderr):
    if not git_ok(repo, "fetch", "origin", "main"):
        warn(OFFLINE_WARNING)
        return None
    listing = git(repo, "ls-tree", "--name-only", "origin/main", "harness/tickets/")
    ids = set()
    for line in listing.splitlines():
        path = Path(line)
        if path.suffix == ".json" and TICKET_ID_RE.match(path.stem):
            ids.add(parse_id(path.stem))
    return ids


def next_ticket_id(repo, warn=_warn_stderr):
    remote = remote_ids(repo, warn) or set()
    return format_id(max(local_ids(repo) | remote | {0}) + 1)


def _same_ticket(a, b):
    return (a.get("created_at") == b.get("created_at")
            and (a.get("created_by") or {}).get("email") == (b.get("created_by") or {}).get("email"))


def renumber(repo, ticket_id, by, now, warn=_warn_stderr):
    remote = remote_ids(repo, warn)
    if remote is None:
        raise RenumberError(
            "renumber needs origin/main to tell which ticket came later. "
            "Fix: check the network and the origin remote, then retry"
        )
    if parse_id(ticket_id) not in remote:
        raise RenumberError(f"{ticket_id} is not on origin/main, so there is no clash to renumber")
    local = load_ticket(repo, ticket_id)
    on_main = json.loads(git(repo, "show", f"origin/main:harness/tickets/{ticket_id}.json"))
    if _same_ticket(local, on_main):
        raise RenumberError(
            f"Local {ticket_id} and {ticket_id} on origin/main are the same ticket "
            "(same created_by and created_at); no renumber needed"
        )
    new_id = format_id(max(local_ids(repo) | remote) + 1)
    local["id"] = new_id
    local["history"].append({
        "by": dict(by), "at": now, "from": local["status"], "to": local["status"],
        "note": f"renumber: {ticket_id} -> {new_id}",
    })
    save_ticket(repo, local)
    ticket_path(repo, ticket_id).unlink()
    return new_id


def commits_mentioning(repo, ticket_id):
    output = git(repo, "log", "origin/main..HEAD", "--fixed-strings", f"--grep={ticket_id}", "--format=%h %s")
    return [line for line in output.splitlines() if line]


def find_collisions(repo, warn=_warn_stderr):
    remote = remote_ids(repo, warn)
    if remote is None:
        return []
    found = []
    for number in sorted(local_ids(repo) & remote):
        ticket_id = format_id(number)
        on_main = json.loads(git(repo, "show", f"origin/main:harness/tickets/{ticket_id}.json"))
        if not _same_ticket(load_ticket(repo, ticket_id), on_main):
            found.append(ticket_id)
    return found
