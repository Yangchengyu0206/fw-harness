"""State machine and Definition of Done (spec section 5.4)."""
import copy

from gitutil import git_ok
from tickets import load_all

FORWARD = {"backlog": "next", "next": "active", "active": "verifying", "verifying": "done"}


class TransitionError(ValueError):
    pass


def _email(person):
    return ((person or {}).get("email") or "").lower()


def latest_evidence(ticket, kind):
    items = [item for item in ticket.get("evidence", []) if item.get("kind") == kind]
    return items[-1] if items else None


def done_problems(ticket):
    problems = []
    if ticket.get("dod_pending"):
        problems.append(f"dod_pending is not empty: {', '.join(ticket['dod_pending'])}")
    if ticket.get("requires_hil", True) and latest_evidence(ticket, "hil") is None:
        problems.append("requires_hil is true but there is no kind: hil evidence. Fix: use fw-hil-verify")
    review = latest_evidence(ticket, "review")
    if review is None:
        problems.append("there is no kind: review evidence. Fix: ask someone other than the assignee to run fw-c-review")
    else:
        if _email(review.get("by")) == _email(ticket.get("assignee")):
            problems.append("the latest review was done by the assignee; a review must come from someone else")
        if review.get("open_critical", 0) != 0:
            problems.append(f"the latest review still has {review['open_critical']} open critical findings")
    return problems


def _ensure_no_other_active(repo, ticket_id, person):
    others = [other["id"] for _, other in load_all(repo)
              if other.get("id") != ticket_id and other.get("status") == "active"
              and _email(other.get("assignee")) == _email(person)]
    if others:
        raise TransitionError(
            f"{ticket_id}: {person['name']} already has active ticket {', '.join(others)}. "
            "One active ticket per person: move that one to verifying or blocked first"
        )


def _record(ticket, by, now, to, note):
    ticket["history"].append({"by": dict(by), "at": now, "from": ticket["status"], "to": to, "note": note})
    ticket["status"] = to


def transition(repo, ticket, to, by, now, note=""):
    new = copy.deepcopy(ticket)
    ticket_id, status = new["id"], new["status"]
    if to == "blocked":
        raise TransitionError(f"{ticket_id}: use block to enter blocked, with a blocked_reason")
    if status == "blocked":
        raise TransitionError(f"{ticket_id}: use unblock to return a blocked ticket to its previous state")
    if FORWARD.get(status) != to:
        raise TransitionError(
            f"{ticket_id}: {status} -> {to} is not allowed. Allowed next state: {FORWARD.get(status) or 'none'}"
        )
    if to == "active":
        _ensure_no_other_active(repo, ticket_id, by)
        new["assignee"] = dict(by)
    elif to == "verifying":
        on_history = [item for item in new["evidence"]
                      if item.get("kind") == "check"
                      and git_ok(repo, "merge-base", "--is-ancestor", item["commit"], "HEAD")]
        if not on_history:
            raise TransitionError(
                f"{ticket_id}: active -> verifying needs at least one kind: check evidence "
                "whose commit is HEAD or an ancestor of HEAD. "
                f"Fix: once check passes, run ticket.py evidence {ticket_id} check --commit <hash> --summary <text> --passed"
            )
        if not any(item.get("passed") is True for item in on_history):
            raise TransitionError(
                f"{ticket_id}: no check evidence on HEAD's history has passed: true. "
                "Fix: get check passing, then record it again"
            )
    elif to == "done":
        problems = done_problems(new)
        if problems:
            raise TransitionError(f"{ticket_id}: verifying -> done conditions not met:\n- " + "\n- ".join(problems))
    _record(new, by, now, to, note)
    return new


def block(ticket, by, now, reason):
    new = copy.deepcopy(ticket)
    if not reason or not reason.strip():
        raise TransitionError(f"{new['id']}: entering blocked requires a blocked_reason")
    if new["status"] in ("blocked", "done"):
        raise TransitionError(f"{new['id']}: a {new['status']} ticket cannot enter blocked")
    new["blocked_reason"] = reason.strip()
    _record(new, by, now, "blocked", reason.strip())
    return new


def unblock(repo, ticket, by, now, note=""):
    new = copy.deepcopy(ticket)
    if new["status"] != "blocked":
        raise TransitionError(f"{new['id']}: only a blocked ticket can be unblocked; it is {new['status']}")
    previous = next((item["from"] for item in reversed(new["history"])
                     if item.get("to") == "blocked" and item.get("from") not in (None, "blocked")), None)
    if previous is None:
        raise TransitionError(f"{new['id']}: history has no state before blocked; inspect the ticket file by hand")
    if previous == "active":
        _ensure_no_other_active(repo, new["id"], new["assignee"])
    new["blocked_reason"] = None
    _record(new, by, now, previous, note or "unblocked")
    return new
