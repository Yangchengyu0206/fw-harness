"""The only implementation of `check` (spec section 4.2). Makefile and the init wrappers call it and add no flags."""
import argparse
import sys
from datetime import datetime
from pathlib import Path

from arch_check import ArchitectureError
from console import use_utf8_stdio
from gitutil import GitError, git, repo_root
from harness_config import ConfigError, load_config
from identity import IdentityError, current_identity
from steps import STEPS, StepResult
from tickets import load_ticket, make_evidence, now_iso, save_ticket, validate_ticket

LOG_DIR = ".verify_logs"


def run_check(repo, config, log):
    results = []
    for name, step in STEPS:
        try:
            result = step(repo, config)
        except (ArchitectureError, GitError, OSError, ValueError) as exc:
            result = StepResult(name, False, f"{type(exc).__name__}: {exc}")
        results.append(result)
        log(f"== {name}: {'passed' if result.passed else 'FAILED'}: {result.summary}")
        if result.output:
            log(result.output)
        if not result.passed:
            break
    return results


def summarize(results):
    passed = sum(1 for result in results if result.passed)
    if passed == len(STEPS):
        return f"check {passed}/{len(STEPS)} passed", True
    return f"check failed at {results[-1].name} ({passed}/{len(STEPS)} passed)", False


def _record(repo, ticket_id, results, now):
    summary, passed = summarize(results)
    ticket = load_ticket(repo, ticket_id)
    commit = git(repo, "rev-parse", "HEAD")[:10]
    ticket["evidence"].append(make_evidence("check", current_identity(repo), now,
                                            commit=commit, summary=summary, passed=passed))
    errors = validate_ticket(ticket, f"{ticket_id}.json")
    if errors:
        raise ValueError("; ".join(errors))
    save_ticket(repo, ticket)


def main(argv=None, cwd=None, now=None):
    use_utf8_stdio()
    parser = argparse.ArgumentParser(prog="check.py",
                                     description="Run the harness gates in order and stop at the first failure.")
    parser.add_argument("--record", metavar="FW-NNNN",
                        help="record the result as check evidence on this ticket (needs a clean working tree)")
    args = parser.parse_args(argv)
    try:
        repo = repo_root(cwd or Path.cwd())
        config = load_config(repo)
        if args.record:
            load_ticket(repo, args.record)
            current_identity(repo)
            if git(repo, "status", "--porcelain"):
                raise ValueError("--record needs a clean working tree so the evidence matches HEAD. "
                                 "Fix: commit or stash your changes first")
    except (ConfigError, GitError, IdentityError, FileNotFoundError, ValueError) as exc:
        print(f"check.py failed: {exc}", file=sys.stderr)
        return 1

    lines = []

    def log(line):
        print(line)
        lines.append(line)

    results = run_check(repo, config, log)
    summary, passed = summarize(results)
    log(summary)
    log_dir = repo / LOG_DIR
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"check-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
    log_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if args.record:
        try:
            _record(repo, args.record, results, now or now_iso())
        except (GitError, IdentityError, FileNotFoundError, ValueError) as exc:
            print(f"check.py --record failed: {exc}", file=sys.stderr)
            return 1
        print(f"Recorded check evidence on {args.record}: {summary}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
