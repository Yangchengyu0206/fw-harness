"""Ticket CLI: the only entry point for state writes. Identity always comes from git config and is never an argument."""
import argparse
import json
import sys
from pathlib import Path

from allocate import RenumberError, commits_mentioning, find_collisions, next_ticket_id, renumber
from console import use_utf8_stdio
from gitutil import GitError, git, repo_root
from identity import IdentityError, current_identity
from tickets import (
    EVIDENCE_FIELDS, EVIDENCE_KINDS, load_ticket, make_evidence, new_ticket, now_iso, save_ticket,
    validate_ticket,
)
from transitions import TransitionError, block, transition, unblock


def build_parser():
    parser = argparse.ArgumentParser(prog="ticket.py", description="Firmware ticket operations (identity comes from git config)")
    sub = parser.add_subparsers(dest="command", required=True)

    new = sub.add_parser("new", help="open a new ticket")
    new.add_argument("--title", required=True)
    new.add_argument("--area", required=True)
    new.add_argument("--priority", type=int, default=3)
    new.add_argument("--behavior", default="")
    new.add_argument("--step", action="append", default=[])
    new.add_argument("--dod", action="append", default=[])
    new.add_argument("--no-hil", dest="requires_hil", action="store_false",
                     help="this ticket needs no on-board verification (default: it does)")

    sub.add_parser("claim", help="claim a ticket and make it active").add_argument("ticket_id")

    move = sub.add_parser("move", help="move a ticket to its next state")
    move.add_argument("ticket_id")
    move.add_argument("status", choices=["next", "active", "verifying", "done"])
    move.add_argument("--note", default="")

    blk = sub.add_parser("block", help="mark a ticket blocked")
    blk.add_argument("ticket_id")
    blk.add_argument("--reason", required=True)

    unb = sub.add_parser("unblock", help="return a blocked ticket to its previous state")
    unb.add_argument("ticket_id")
    unb.add_argument("--note", default="")

    ev = sub.add_parser("evidence", help="add check / hil / review evidence")
    ev.add_argument("ticket_id")
    ev.add_argument("kind", choices=EVIDENCE_KINDS)
    ev.add_argument("--commit")
    ev.add_argument("--summary")
    outcome = ev.add_mutually_exclusive_group()
    outcome.add_argument("--passed", dest="passed", action="store_true")
    outcome.add_argument("--failed", dest="passed", action="store_false")
    ev.set_defaults(passed=None)
    ev.add_argument("--ref")
    ev.add_argument("--open-critical", dest="open_critical", type=int)

    dod = sub.add_parser("dod", help="add or complete dod_pending items")
    dod.add_argument("ticket_id")
    dod.add_argument("--add", action="append", default=[])
    dod.add_argument("--remove", action="append", default=[])

    sub.add_parser("collisions", help="before merging, check local ticket IDs against origin/main")
    sub.add_parser("renumber", help="move a clashing local ticket to the next free ID").add_argument("ticket_id")
    sub.add_parser("show", help="print a ticket").add_argument("ticket_id")
    return parser


def confirm_done_on_tty(ticket_id):
    if not sys.stdin.isatty():
        return False
    answer = input(f"Confirm {ticket_id} passed on-board verification and was reviewed by someone else. Type the ticket ID: ")
    return answer.strip() == ticket_id


def _save(repo, ticket):
    errors = validate_ticket(ticket, f"{ticket['id']}.json")
    if errors:
        raise ValueError("schema check before writing failed: " + "; ".join(errors))
    save_ticket(repo, ticket)


def cmd_new(repo, args, by, now):
    ticket_id = next_ticket_id(repo)
    ticket = new_ticket(ticket_id, args.title, args.area, by, now, priority=args.priority,
                        user_visible_behavior=args.behavior, verification_steps=args.step,
                        dod_pending=args.dod, requires_hil=args.requires_hil)
    _save(repo, ticket)
    print(f"Opened {ticket_id}: {args.title}")
    print("Note: the ID is claimed only once the commit creating this ticket is merged into main.")
    return 0


def cmd_claim(repo, args, by, now):
    ticket = load_ticket(repo, args.ticket_id)
    if ticket["status"] == "backlog":
        ticket = transition(repo, ticket, "next", by, now, note="claim")
    ticket = transition(repo, ticket, "active", by, now, note="claim")
    _save(repo, ticket)
    print(f"{ticket['id']} claimed by {by['name']}, now active")
    return 0


def cmd_move(repo, args, by, now):
    ticket = transition(repo, load_ticket(repo, args.ticket_id), args.status, by, now, note=args.note)
    if args.status == "done" and not args.confirm(ticket["id"]):
        raise ValueError(
            "moving to done needs a human to type the ticket ID in an interactive terminal "
            "(an agent cannot mark a ticket done). "
            f"Fix: run ticket.py move {ticket['id']} done in your own terminal"
        )
    _save(repo, ticket)
    print(f"{ticket['id']} -> {ticket['status']}")
    return 0


def cmd_block(repo, args, by, now):
    ticket = block(load_ticket(repo, args.ticket_id), by, now, args.reason)
    _save(repo, ticket)
    print(f"{ticket['id']} -> blocked: {ticket['blocked_reason']}")
    return 0


def cmd_unblock(repo, args, by, now):
    ticket = unblock(repo, load_ticket(repo, args.ticket_id), by, now, note=args.note)
    _save(repo, ticket)
    print(f"{ticket['id']} -> {ticket['status']}")
    return 0


def cmd_evidence(repo, args, by, now):
    ticket = load_ticket(repo, args.ticket_id)
    if args.kind == "check" and args.passed is None:
        raise ValueError("check evidence needs --passed or --failed")
    given = {"commit": args.commit, "summary": args.summary, "passed": args.passed,
             "ref": args.ref, "open_critical": args.open_critical}
    fields = {key: given[key] for key in EVIDENCE_FIELDS[args.kind]}
    if args.kind == "check" and fields["commit"]:
        fields["commit"] = git(repo, "rev-parse", "--verify", f"{fields['commit']}^{{commit}}")[:10]
    ticket["evidence"].append(make_evidence(args.kind, by, now, **fields))
    _save(repo, ticket)
    print(f"{ticket['id']}: added {args.kind} evidence")
    return 0


def cmd_dod(repo, args, by, now):
    ticket = load_ticket(repo, args.ticket_id)
    missing = [item for item in args.remove if item not in ticket["dod_pending"]]
    if missing:
        current = ", ".join(ticket["dod_pending"]) or "none"
        raise ValueError(f"dod_pending has no item named {', '.join(missing)}. Current items: {current}")
    if not args.add and not args.remove:
        raise ValueError("give at least one --add or --remove")
    ticket["dod_pending"] = [item for item in ticket["dod_pending"] if item not in args.remove] + args.add
    parts = [f"add {item}" for item in args.add] + [f"done {item}" for item in args.remove]
    ticket["history"].append({"by": dict(by), "at": now, "from": ticket["status"],
                              "to": ticket["status"], "note": "dod: " + "; ".join(parts)})
    _save(repo, ticket)
    print(f"{ticket['id']} dod_pending: {', '.join(ticket['dod_pending']) or 'empty'}")
    return 0


def cmd_collisions(repo, args, by, now):
    found = find_collisions(repo)
    if not found:
        print("No ticket ID clashes with origin/main")
        return 0
    for ticket_id in found:
        print(f"Clash: local {ticket_id} is a different ticket from {ticket_id} on origin/main. "
              f"Fix: ticket.py renumber {ticket_id}")
    return 1


def cmd_renumber(repo, args, by, now):
    old_id = args.ticket_id
    new_id = renumber(repo, old_id, by, now)
    print(f"Renumbered local {old_id} to {new_id}. Run git add harness/tickets and commit.")
    commits = commits_mentioning(repo, old_id)
    if commits:
        print(f"These branch commits still mention {old_id}. If nobody else uses the branch, reword them to {new_id}:")
        for line in commits:
            print(f"  {line}")
    return 0


def cmd_show(repo, args, by, now):
    print(json.dumps(load_ticket(repo, args.ticket_id), ensure_ascii=False, indent=2))
    return 0


COMMANDS = {
    "new": cmd_new, "claim": cmd_claim, "move": cmd_move, "block": cmd_block, "unblock": cmd_unblock,
    "evidence": cmd_evidence, "dod": cmd_dod, "collisions": cmd_collisions, "renumber": cmd_renumber,
    "show": cmd_show,
}


def main(argv=None, cwd=None, now=None, confirm=None):
    use_utf8_stdio()
    args = build_parser().parse_args(argv)
    args.confirm = confirm or confirm_done_on_tty
    try:
        repo = repo_root(cwd or Path.cwd())
        by = current_identity(repo)
        return COMMANDS[args.command](repo, args, by, now or now_iso())
    except (IdentityError, GitError, TransitionError, RenumberError, FileNotFoundError, ValueError) as exc:
        print(f"ticket.py {args.command} failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
