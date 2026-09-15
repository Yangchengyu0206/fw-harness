"""Generate feature_list.json (gitignored): ticket summaries plus commit evidence derived from git log."""
import re
import sys
from collections import defaultdict
from pathlib import Path

from gitutil import git, repo_root
from jsonio import read_json, write_json_atomic
from tickets import EVIDENCE_KINDS, load_all, now_iso
from transitions import latest_evidence

INDEX_NAME = "feature_list.json"
# Not \b: letters such as CJK characters or µ are word characters, so \b misses IDs written right after them
TICKET_REF_RE = re.compile(r"(?<![A-Za-z0-9-])FW-\d{4,}(?!\d)")
# \x1f and \x1e count as whitespace for str.strip(), which would eat the separators of the
# last commit when its body is empty; \x01 and \x02 do not
_FIELD, _RECORD = "\x01", "\x02"


def commit_evidence(repo):
    output = git(repo, "log", "--format=%H%x01%an%x01%ae%x01%aI%x01%s%x01%b%x02")
    result = defaultdict(list)
    for record in output.split(_RECORD):
        record = record.strip("\n")
        if not record.strip():
            continue
        sha, name, email, at, subject, body = record.split(_FIELD, 5)
        for ticket_id in sorted(set(TICKET_REF_RE.findall(f"{subject}\n{body}"))):
            result[ticket_id].append({
                "kind": "commit", "commit": sha[:10],
                "by": {"name": name, "email": email}, "at": at, "subject": subject,
            })
    return result


def build_index(repo):
    commits = commit_evidence(repo)
    entries = []
    for _, ticket in load_all(repo):
        review = latest_evidence(ticket, "review")
        entries.append({
            "id": ticket["id"],
            "title": ticket["title"],
            "area": ticket["area"],
            "status": ticket["status"],
            "priority": ticket["priority"],
            "assignee": ticket["assignee"],
            "requires_hil": ticket["requires_hil"],
            "dod_pending": ticket["dod_pending"],
            "blocked_reason": ticket["blocked_reason"],
            "evidence_counts": {kind: sum(1 for e in ticket["evidence"] if e["kind"] == kind)
                                for kind in EVIDENCE_KINDS},
            "latest_review_open_critical": review["open_critical"] if review else None,
            "commits": commits.get(ticket["id"], []),
        })
    return {"generated_at": now_iso(), "tickets": entries}


def write_index(repo):
    path = Path(repo) / INDEX_NAME
    write_json_atomic(path, build_index(repo))
    return path


def main(argv=None):
    repo = repo_root(Path.cwd())
    path = write_index(repo)
    count = len(read_json(path)["tickets"])
    print(f"Generated {path.name} ({count} ticket{'' if count == 1 else 's'})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
