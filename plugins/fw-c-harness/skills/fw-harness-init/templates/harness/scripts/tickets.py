"""Ticket files: one file per ticket at harness/tickets/FW-NNNN.json."""
import re
from datetime import datetime
from pathlib import Path

from jsonio import read_json, write_json_atomic

TICKET_ID_RE = re.compile(r"^FW-(\d{4,})$")
STATUSES = ("backlog", "next", "active", "verifying", "done", "blocked")
EVIDENCE_KINDS = ("check", "hil", "review")
EVIDENCE_FIELDS = {"check": ("commit", "summary", "passed"), "hil": ("ref",), "review": ("ref", "open_critical")}
ASSIGNED_STATUSES = ("active", "verifying", "done")


def tickets_dir(repo):
    return Path(repo) / "harness" / "tickets"


def ticket_path(repo, ticket_id):
    return tickets_dir(repo) / f"{ticket_id}.json"


def format_id(number):
    return f"FW-{number:04d}"


def parse_id(ticket_id):
    match = TICKET_ID_RE.match(ticket_id)
    if not match:
        raise ValueError(f"Invalid ticket ID {ticket_id!r}; expected FW-NNNN")
    return int(match.group(1))


def now_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def load_ticket(repo, ticket_id):
    path = ticket_path(repo, ticket_id)
    if not path.exists():
        raise FileNotFoundError(f"Ticket {ticket_id} not found: {path}")
    return read_json(path)


def load_all(repo):
    directory = tickets_dir(repo)
    if not directory.exists():
        return []
    return [(path, read_json(path)) for path in sorted(directory.glob("FW-*.json"))]


def save_ticket(repo, ticket):
    write_json_atomic(ticket_path(repo, ticket["id"]), ticket)


def _is_person(value):
    return (isinstance(value, dict) and isinstance(value.get("name"), str)
            and isinstance(value.get("email"), str) and bool(value["email"]))


def _is_str_list(value):
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _is_count(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def validate_ticket(ticket, filename=None):
    if not isinstance(ticket, dict):
        return [f"{filename or '<ticket>'}: ticket file must contain a JSON object"]
    label = Path(filename).name if filename else (ticket.get("id") or "<ticket>")
    errors = []

    def err(message):
        errors.append(f"{label}: {message}")

    ticket_id = ticket.get("id")
    if not isinstance(ticket_id, str) or not TICKET_ID_RE.match(ticket_id):
        err("id must match FW-NNNN")
    elif filename is not None and Path(filename).stem != ticket_id:
        err(f"id {ticket_id} does not match file name {Path(filename).name}. "
            "Fix: rename the file, or run ticket.py renumber")

    for key in ("title", "area", "created_at", "user_visible_behavior", "notes"):
        if not isinstance(ticket.get(key), str):
            err(f"{key} must be a string")

    status = ticket.get("status")
    if status not in STATUSES:
        err(f"status must be one of {'/'.join(STATUSES)}")
    if not _is_count(ticket.get("priority")):
        err("priority must be a non-negative integer")
    if not isinstance(ticket.get("requires_hil"), bool):
        err("requires_hil must be true or false")
    if not _is_person(ticket.get("created_by")):
        err("created_by must have name and email")
    assignee = ticket.get("assignee")
    if assignee is not None and not _is_person(assignee):
        err("assignee must be null or have name and email")
    if status in ASSIGNED_STATUSES and assignee is None:
        err(f"status {status} requires an assignee")

    for key in ("verification_steps", "dod_pending"):
        if not _is_str_list(ticket.get(key)):
            err(f"{key} must be an array of strings")

    reason = ticket.get("blocked_reason")
    if reason is not None and not isinstance(reason, str):
        err("blocked_reason must be null or a string")
    if status == "blocked" and not (isinstance(reason, str) and reason.strip()):
        err('a blocked ticket needs a blocked_reason. Fix: ticket.py block <id> --reason "..."')

    evidence = ticket.get("evidence")
    if not isinstance(evidence, list):
        err("evidence must be an array")
    else:
        for index, item in enumerate(evidence):
            where = f"evidence[{index}]"
            if not isinstance(item, dict) or item.get("kind") not in EVIDENCE_KINDS:
                err(f"{where}.kind must be one of check/hil/review "
                    "(commit evidence is derived from git log and never stored in ticket files)")
                continue
            if not _is_person(item.get("by")) or not isinstance(item.get("at"), str):
                err(f"{where} must have by and at")
            for field in EVIDENCE_FIELDS[item["kind"]]:
                if field == "open_critical":
                    if not _is_count(item.get(field)):
                        err(f"{where}.open_critical must be a non-negative integer")
                elif field == "passed":
                    if not isinstance(item.get(field), bool):
                        err(f"{where}.passed must be true or false")
                elif not (isinstance(item.get(field), str) and item[field]):
                    err(f"{where}.{field} must be a non-empty string")

    history = ticket.get("history")
    if not isinstance(history, list):
        err("history must be an array")
    else:
        for index, item in enumerate(history):
            if (not isinstance(item, dict) or not _is_person(item.get("by"))
                    or not isinstance(item.get("at"), str) or item.get("to") not in STATUSES
                    or (item.get("from") is not None and item.get("from") not in STATUSES)):
                err(f"history[{index}] must have by, at, from (null or a status), and to (a status)")
    return errors


def new_ticket(ticket_id, title, area, by, now, priority=3, user_visible_behavior="",
               verification_steps=(), dod_pending=(), requires_hil=True):
    return {
        "id": ticket_id,
        "title": title,
        "area": area,
        "status": "backlog",
        "priority": priority,
        "requires_hil": requires_hil,
        "created_by": dict(by),
        "created_at": now,
        "assignee": None,
        "user_visible_behavior": user_visible_behavior,
        "verification_steps": list(verification_steps),
        "dod_pending": list(dod_pending),
        "evidence": [],
        "history": [{"by": dict(by), "at": now, "from": None, "to": "backlog", "note": "opened"}],
        "blocked_reason": None,
        "notes": "",
    }


def make_evidence(kind, by, now, **fields):
    if kind not in EVIDENCE_KINDS:
        raise ValueError(f"evidence kind must be one of check/hil/review, got {kind!r}")
    missing = [field for field in EVIDENCE_FIELDS[kind] if fields.get(field) in (None, "")]
    if missing:
        raise ValueError(f"{kind} evidence is missing {', '.join(missing)}")
    return {"kind": kind, "by": dict(by), "at": now, **fields}
