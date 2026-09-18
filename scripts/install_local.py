"""Install this cdev package on a machine that cannot reach the marketplace.

Two ways to install, and this script helps with both:

  py -3 install_local.py --settings              print the VS Code setting for this folder
  py -3 install_local.py --repo <path>           copy the skills into a repository
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILLS = HERE / "skills"
TARGETS = {"copilot": ".github/skills", "claude": ".claude/skills"}
SKIP = {"__pycache__"}


def settings_snippet(folder):
    return json.dumps({"chat.pluginLocations": {folder.as_posix(): True}}, indent=2)


def skill_names():
    return sorted(path.parent.name for path in SKILLS.glob("*/SKILL.md"))


def copy_into(repo, tool):
    repo = Path(repo)
    if not repo.is_dir():
        raise SystemExit(f"{repo} is not a folder")
    target = repo / TARGETS[tool]
    target.mkdir(parents=True, exist_ok=True)
    copied = []
    for name in skill_names():
        destination = target / name
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(SKILLS / name, destination,
                        ignore=shutil.ignore_patterns(*SKIP))
        copied.append(name)
    for extra in ("LICENSE", "THIRD_PARTY_NOTICES.md"):
        if (HERE / extra).is_file():
            shutil.copy2(HERE / extra, target / extra)
    return target, copied


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(prog="install_local.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--settings", action="store_true",
                        help="print the VS Code setting that registers this folder as a plugin")
    parser.add_argument("--repo", help="copy the skills into this repository instead")
    parser.add_argument("--tool", choices=sorted(TARGETS), default="copilot",
                        help="which folder to copy into: copilot writes .github/skills, claude writes .claude/skills")
    args = parser.parse_args(argv)

    if not SKILLS.is_dir():
        raise SystemExit(f"no skills folder next to this script ({SKILLS})")

    if args.repo:
        target, copied = copy_into(args.repo, args.tool)
        print(f"copied {len(copied)} skills into {target}")
        print("  " + ", ".join(copied))
        print("Commit them so everyone who clones the repository has them.")
        return 0

    if args.settings or True:
        print("Add this to your VS Code user settings JSON (Preferences: Open User Settings (JSON)):")
        print(settings_snippet(HERE))
        print(f"\nThen restart VS Code. The {len(skill_names())} cdev skills load in every workspace.")
        print("To keep the skills inside one repository instead, run: py -3 install_local.py --repo <path>")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
