"""commit-msg hook check (spec section 4.3): reference existing tickets, or use an exempt prefix."""
import re
import sys
from pathlib import Path

from console import use_utf8_stdio
from gitutil import repo_root
from index import TICKET_REF_RE
from tickets import ticket_path

EXEMPT_PREFIX_RE = re.compile(r"^(harness|chore)(\([^)]*\))?!?:")
GIT_GENERATED_PREFIXES = ("Merge ", "Revert ", "fixup! ", "squash! ", "amend! ")


def check_message(repo, text):
    lines = [line for line in text.splitlines() if not line.startswith("#")]
    message = "\n".join(lines).strip()
    if not message:
        return []
    subject = message.splitlines()[0]
    if subject.startswith(GIT_GENERATED_PREFIXES) or EXEMPT_PREFIX_RE.match(subject):
        return []
    ids = sorted(set(TICKET_REF_RE.findall(message)))
    if not ids:
        return ["commit message must reference a ticket (FW-NNNN) or start with harness: or chore:"]
    missing = [ticket_id for ticket_id in ids if not ticket_path(repo, ticket_id).is_file()]
    if missing:
        return [f"commit message references tickets that do not exist: {', '.join(missing)}. "
                "Fix: open the ticket with ticket.py new first"]
    return []


def main(argv=None, cwd=None):
    use_utf8_stdio()
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: commit_msg_check.py <commit message file>", file=sys.stderr)
        return 2
    repo = repo_root(cwd or Path.cwd())
    errors = check_message(repo, Path(args[0]).read_text(encoding="utf-8", errors="replace"))
    for error in errors:
        print(f"commit-msg: {error}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
