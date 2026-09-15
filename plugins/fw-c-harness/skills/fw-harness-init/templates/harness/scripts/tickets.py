"""票檔：一票一檔 harness/tickets/FW-NNNN.json。"""
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
        raise ValueError(f"票號格式錯誤：{ticket_id!r}，應為 FW-NNNN")
    return int(match.group(1))


def now_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def load_ticket(repo, ticket_id):
    path = ticket_path(repo, ticket_id)
    if not path.exists():
        raise FileNotFoundError(f"找不到票 {ticket_id}：{path}")
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
        return [f"{filename or '<票>'}：票檔內容必須是 JSON 物件"]
    label = Path(filename).name if filename else (ticket.get("id") or "<票>")
    errors = []

    def err(message):
        errors.append(f"{label}：{message}")

    ticket_id = ticket.get("id")
    if not isinstance(ticket_id, str) or not TICKET_ID_RE.match(ticket_id):
        err("id 必須是 FW-NNNN 格式")
    elif filename is not None and Path(filename).stem != ticket_id:
        err(f"id {ticket_id} 與檔名 {Path(filename).name} 不一致。修法：改檔名，或執行 ticket.py renumber")

    for key in ("title", "area", "created_at", "user_visible_behavior", "notes"):
        if not isinstance(ticket.get(key), str):
            err(f"{key} 必須是字串")

    status = ticket.get("status")
    if status not in STATUSES:
        err(f"status 必須是 {'/'.join(STATUSES)} 之一")
    if not _is_count(ticket.get("priority")):
        err("priority 必須是非負整數")
    if not isinstance(ticket.get("requires_hil"), bool):
        err("requires_hil 必須是 true 或 false")
    if not _is_person(ticket.get("created_by")):
        err("created_by 必須含 name 與 email")
    assignee = ticket.get("assignee")
    if assignee is not None and not _is_person(assignee):
        err("assignee 必須是 null 或含 name 與 email")
    if status in ASSIGNED_STATUSES and assignee is None:
        err(f"status 為 {status} 時必須有 assignee")

    for key in ("verification_steps", "dod_pending"):
        if not _is_str_list(ticket.get(key)):
            err(f"{key} 必須是字串陣列")

    reason = ticket.get("blocked_reason")
    if reason is not None and not isinstance(reason, str):
        err("blocked_reason 必須是 null 或字串")
    if status == "blocked" and not (isinstance(reason, str) and reason.strip()):
        err("blocked 的票必須填 blocked_reason。修法：ticket.py block <票號> --reason \"原因\"")

    evidence = ticket.get("evidence")
    if not isinstance(evidence, list):
        err("evidence 必須是陣列")
    else:
        for index, item in enumerate(evidence):
            where = f"evidence[{index}]"
            if not isinstance(item, dict) or item.get("kind") not in EVIDENCE_KINDS:
                err(f"{where}.kind 必須是 check/hil/review 之一（commit 類 evidence 由 git log 動態計算，不寫入票檔）")
                continue
            if not _is_person(item.get("by")) or not isinstance(item.get("at"), str):
                err(f"{where} 必須含 by 與 at")
            for field in EVIDENCE_FIELDS[item["kind"]]:
                if field == "open_critical":
                    if not _is_count(item.get(field)):
                        err(f"{where}.open_critical 必須是非負整數")
                elif field == "passed":
                    if not isinstance(item.get(field), bool):
                        err(f"{where}.passed 必須是 true 或 false")
                elif not (isinstance(item.get(field), str) and item[field]):
                    err(f"{where}.{field} 必須是非空字串")

    history = ticket.get("history")
    if not isinstance(history, list):
        err("history 必須是陣列")
    else:
        for index, item in enumerate(history):
            if (not isinstance(item, dict) or not _is_person(item.get("by"))
                    or not isinstance(item.get("at"), str) or item.get("to") not in STATUSES
                    or (item.get("from") is not None and item.get("from") not in STATUSES)):
                err(f"history[{index}] 必須含 by、at、from（null 或狀態）、to（狀態）")
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
        "history": [{"by": dict(by), "at": now, "from": None, "to": "backlog", "note": "開票"}],
        "blocked_reason": None,
        "notes": "",
    }


def make_evidence(kind, by, now, **fields):
    if kind not in EVIDENCE_KINDS:
        raise ValueError(f"evidence kind 必須是 check/hil/review 之一，收到 {kind!r}")
    missing = [field for field in EVIDENCE_FIELDS[kind] if fields.get(field) in (None, "")]
    if missing:
        raise ValueError(f"{kind} evidence 缺少 {'、'.join(missing)}")
    return {"kind": kind, "by": dict(by), "at": now, **fields}
