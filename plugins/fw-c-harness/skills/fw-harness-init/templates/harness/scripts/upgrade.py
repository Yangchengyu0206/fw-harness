"""fw-harness-upgrade: refresh managed harness files and propose team-owned changes (spec section 3.1)."""
import argparse
import json
import sys
from pathlib import Path

import install
import manifest
import review_docs
from console import use_utf8_stdio
from gitutil import repo_root
from jsonio import read_json, write_json_atomic, write_text_atomic
from tickets import now_iso


class UpgradeError(RuntimeError):
    pass


def load_record(repo):
    path = Path(repo) / manifest.VERSION_PATH
    if not path.is_file():
        raise UpgradeError(f"{manifest.VERSION_PATH} not found, so this repository has no harness yet. "
                           "Fix: run fw-harness-init first")
    try:
        record = read_json(path)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise UpgradeError(f"{manifest.VERSION_PATH} is not valid JSON ({exc}). "
                           "Fix: restore it from git") from exc
    if not isinstance(record.get("managed"), dict) or not isinstance(record.get("team_owned"), dict):
        raise UpgradeError(f"{manifest.VERSION_PATH} is missing the managed and team_owned tables. "
                           "Fix: restore it from git, or run fw-harness-init again")
    return record


def plan(repo, templates, record):
    repo, templates = Path(repo), Path(templates)
    report = {"created": [], "updated": [], "proposed": [], "unchanged": []}

    for path in manifest.managed_files(templates):
        source = (templates / path).read_bytes()
        target = repo / path
        if not target.is_file():
            report["created"].append((path, source))
        elif target.read_bytes() == source:
            report["unchanged"].append(path)
        elif record["managed"].get(path) == manifest.digest(target.read_bytes()):
            report["updated"].append((path, source))
        else:
            report["proposed"].append((path, source))

    for path in manifest.TEAM_OWNED:
        source = (templates / path).read_bytes()
        target = repo / path
        if not target.is_file():
            report["created"].append((path, source))
        elif record["team_owned"].get(path) == manifest.digest(source):
            report["unchanged"].append(path)
        elif target.read_bytes() == source:
            report["unchanged"].append(path)
        else:
            report["proposed"].append((path, source))
    return report


def upgrade(repo, templates, now=None, dry_run=False):
    repo, templates = Path(repo), Path(templates)
    if not (templates / "VERSION").is_file():
        raise UpgradeError(f"templates folder {templates} not found or incomplete. "
                           "Fix: pass --templates <plugin>/skills/fw-harness-init/templates")
    record = load_record(repo)
    work = plan(repo, templates, record)

    if not dry_run:
        for path, data in work["created"] + work["updated"]:
            install.write_bytes(repo / path, data)
            if path in manifest.EXECUTABLE:
                (repo / path).chmod(0o755)
        for path, data in work["proposed"]:
            install.write_bytes(repo / (path + manifest.PROPOSED_SUFFIX), data)

        instructions = review_docs.render_instructions(review_docs.load_checklist(repo),
                                                       review_docs.load_policy(repo))
        generated = repo / manifest.GENERATED[0]
        if not generated.is_file() or generated.read_text(encoding="utf-8") != instructions:
            write_text_atomic(generated, instructions)

    version = manifest.read_version(templates)
    result = {kind: sorted(entries) if kind == "unchanged" else sorted(path for path, _ in entries)
              for kind, entries in work.items()}
    result["from_version"] = record.get("version", "unknown")
    result["to_version"] = version
    if not dry_run:
        write_json_atomic(repo / manifest.VERSION_PATH,
                          install.version_record(repo, templates, version,
                                                 record.get("marketplace", install.DEFAULT_MARKETPLACE),
                                                 now or now_iso()))
    return result


def main(argv=None, cwd=None, now=None):
    use_utf8_stdio()
    parser = argparse.ArgumentParser(prog="upgrade", description="Update the harness in this repository")
    parser.add_argument("--templates", default=None, help="the plugin's templates folder")
    parser.add_argument("--dry-run", action="store_true", help="report the work without writing anything")
    args = parser.parse_args(argv)

    templates = Path(args.templates) if args.templates else install.default_templates()
    if templates is None:
        print("upgrade failed: could not find the templates folder. "
              "Fix: pass --templates <plugin>/skills/fw-harness-init/templates", file=sys.stderr)
        return 1
    repo = repo_root(cwd or Path.cwd())
    try:
        report = upgrade(repo, templates, now=now, dry_run=args.dry_run)
    except (UpgradeError, review_docs.ReviewDocsError) as exc:
        print(f"upgrade failed: {exc}", file=sys.stderr)
        return 1

    print(f"upgrade: {report['from_version']} to {report['to_version']}"
          + (" (dry run, nothing written)" if args.dry_run else ""))
    for kind in ("created", "updated", "proposed", "unchanged"):
        names = report[kind]
        print(f"upgrade: {kind} {len(names)} files" + (f": {', '.join(names[:5])}" if names[:5] else ""))
    for path in report["proposed"]:
        print(f"upgrade: {path} differs from the new template, so the new version is at "
              f"{path}{manifest.PROPOSED_SUFFIX}. Fix: review the difference item by item and merge what you want")
    if report["updated"] or report["created"]:
        print("upgrade: run check before committing, so a script change is verified here")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
