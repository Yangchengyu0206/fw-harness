"""fw-harness-init: write the harness into a firmware repository (spec sections 4 and 8)."""
import argparse
import json
import os
import sys
from pathlib import Path

import manifest
import review_docs
from console import use_utf8_stdio
from gitutil import git, repo_root
from jsonio import read_json, write_json_atomic, write_text_atomic
from tickets import now_iso

DEFAULT_MARKETPLACE = "Yangchengyu0206/fw-harness"
MARKETPLACE_NAME = "fw-harness"
PLUGIN_NAME = "fw-c-harness"
# Claude Code, GitHub Copilot in VS Code, and Copilot CLI all read plugin recommendations from this file.
CLAUDE_SETTINGS = ".claude/settings.json"


class InstallError(RuntimeError):
    pass


def write_bytes(target, data):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)


def place(repo, source, path, report):
    target = Path(repo) / path
    data = Path(source).read_bytes()
    if target.is_file():
        if target.read_bytes() == data:
            report["unchanged"].append(path)
        else:
            write_bytes(target.with_name(target.name + manifest.PROPOSED_SUFFIX), data)
            report["proposed"].append(path)
        return
    write_bytes(target, data)
    if path in manifest.EXECUTABLE:
        os.chmod(target, 0o755)
    report["created"].append(path)


def claude_settings(existing, marketplace):
    settings = dict(existing or {})
    known = dict(settings.get("extraKnownMarketplaces") or {})
    known[MARKETPLACE_NAME] = {"source": {"source": "github", "repo": marketplace}}
    settings["extraKnownMarketplaces"] = known
    enabled = dict(settings.get("enabledPlugins") or {})
    enabled[f"{PLUGIN_NAME}@{MARKETPLACE_NAME}"] = True
    settings["enabledPlugins"] = enabled
    return settings


def _merge_settings(repo, path, merge, marketplace, report):
    target = Path(repo) / path
    existed = target.is_file()
    existing = read_json(target) if existed else {}
    merged = merge(existing, marketplace)
    if existed and merged == existing:
        report["unchanged"].append(path)
        return
    write_json_atomic(target, merged)
    report["merged" if existed else "created"].append(path)


def version_record(repo, templates, version, marketplace, now):
    managed = {}
    for path in manifest.managed_files(templates) + list(manifest.GENERATED):
        target = Path(repo) / path
        if target.is_file():
            managed[path] = manifest.digest(target.read_bytes())
    team_owned = {path: manifest.digest((Path(templates) / path).read_bytes())
                  for path in manifest.TEAM_OWNED}
    return {"version": version, "installed_at": now, "marketplace": marketplace,
            "managed": managed, "team_owned": team_owned}


def install(repo, templates, marketplace=DEFAULT_MARKETPLACE, now=None):
    repo, templates = Path(repo), Path(templates)
    if not (templates / "VERSION").is_file():
        raise InstallError(f"templates folder {templates} not found or incomplete. "
                           "Fix: pass --templates <plugin>/skills/fw-harness-init/templates")
    report = {"created": [], "merged": [], "proposed": [], "unchanged": []}

    for path in manifest.managed_files(templates) + list(manifest.TEAM_OWNED):
        place(repo, templates / path, path, report)
    for folder in manifest.DIRS:
        keep = repo / folder / ".gitkeep"
        if not keep.is_file():
            write_bytes(keep, b"")
            report["created"].append(f"{folder}/.gitkeep")

    instructions = review_docs.render_instructions(review_docs.load_checklist(repo),
                                                   review_docs.load_policy(repo))
    generated = repo / manifest.GENERATED[0]
    if not generated.is_file() or generated.read_text(encoding="utf-8") != instructions:
        write_text_atomic(generated, instructions)
        report["created"].append(manifest.GENERATED[0])
    else:
        report["unchanged"].append(manifest.GENERATED[0])

    _merge_settings(repo, CLAUDE_SETTINGS, claude_settings, marketplace, report)

    git(repo, "config", "core.hooksPath", ".githooks")
    for path in manifest.EXECUTABLE:
        if (repo / path).is_file():
            git(repo, "update-index", "--add", "--chmod=+x", path)

    version = manifest.read_version(templates)
    write_json_atomic(repo / manifest.VERSION_PATH,
                      version_record(repo, templates, version, marketplace, now or now_iso()))
    report["version"] = version
    return report


def default_templates():
    candidate = Path(__file__).resolve().parents[2]
    return candidate if (candidate / "VERSION").is_file() else None


def main(argv=None, cwd=None, now=None):
    use_utf8_stdio()
    parser = argparse.ArgumentParser(prog="install",
                                     description="Write the fw-c-harness into this repository")
    parser.add_argument("--templates", default=None, help="the plugin's templates folder")
    parser.add_argument("--marketplace", default=DEFAULT_MARKETPLACE,
                        help="owner/repo of the plugin marketplace")
    args = parser.parse_args(argv)

    templates = Path(args.templates) if args.templates else default_templates()
    if templates is None:
        print("install failed: could not find the templates folder. "
              "Fix: pass --templates <plugin>/skills/fw-harness-init/templates", file=sys.stderr)
        return 1
    repo = repo_root(cwd or Path.cwd())
    try:
        report = install(repo, templates, marketplace=args.marketplace, now=now)
    except (InstallError, review_docs.ReviewDocsError, json.JSONDecodeError) as exc:
        print(f"install failed: {exc}", file=sys.stderr)
        return 1

    print(f"install: harness {report['version']} written to {repo}")
    for kind in ("created", "merged", "proposed", "unchanged"):
        names = report[kind]
        print(f"install: {kind} {len(names)} files" + (f": {', '.join(names[:5])}" if names[:5] else ""))
    for path in report["proposed"]:
        print(f"install: {path} already exists, so the new version is at {path}{manifest.PROPOSED_SUFFIX}. "
              "Fix: compare them and merge by hand")
    print("install: next run arch_sync scan, confirm the modules with a human, then arch_sync docs")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
