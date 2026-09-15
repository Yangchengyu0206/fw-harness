"""check step 4: consistency check across all ticket files (spec section 5.5)."""
import json
import sys
from collections import defaultdict
from pathlib import Path

from gitutil import repo_root
from jsonio import read_json
from tickets import tickets_dir, validate_ticket
from transitions import done_problems


def _load(repo):
    loaded, errors = [], []
    directory = tickets_dir(repo)
    for path in sorted(directory.glob("FW-*.json")) if directory.exists() else []:
        try:
            loaded.append((path, read_json(path)))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            errors.append(f"{path.name}: not valid UTF-8 JSON ({exc}). Fix: repair the file or restore it from git")
    return loaded, errors


def check_tickets(repo):
    loaded, errors = _load(repo)
    by_id = defaultdict(list)
    active_by_email = defaultdict(list)
    for path, ticket in loaded:
        problems = validate_ticket(ticket, path.name)
        errors.extend(problems)
        if not isinstance(ticket, dict):
            continue
        by_id[ticket.get("id")].append(path.name)
        if problems:
            continue
        if ticket["status"] == "active":
            active_by_email[ticket["assignee"]["email"].lower()].append(ticket["id"])
        if ticket["status"] == "done":
            errors.extend(f"{path.name}: done conditions not met: {p}" for p in done_problems(ticket))
    for ticket_id, names in by_id.items():
        if len(names) > 1:
            errors.append(f"Ticket ID {ticket_id} is duplicated in {', '.join(names)}. Fix: ticket.py renumber {ticket_id}")
    for email, ids in active_by_email.items():
        if len(ids) > 1:
            errors.append(
                f"{email} has several active tickets: {', '.join(ids)}. "
                "Fix: keep one active and move the others to verifying or blocked"
            )
    return errors


def main(argv=None):
    repo = repo_root(Path.cwd())
    errors = check_tickets(repo)
    if errors:
        for error in errors:
            print(f"ticket_check failed: {error}", file=sys.stderr)
        return 1
    count = len(list(tickets_dir(repo).glob("FW-*.json"))) if tickets_dir(repo).exists() else 0
    print(f"ticket_check: passed ({count} ticket{'' if count == 1 else 's'})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
