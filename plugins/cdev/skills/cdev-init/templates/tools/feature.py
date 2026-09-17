"""Keep feature_list.json valid. The only script cdev writes into a repository."""
import argparse
import json
import os
import re
import sys
import tempfile
from datetime import date
from pathlib import Path

DEFAULT_FILE = Path(__file__).resolve().parents[1] / "feature_list.json"
STATUSES = ("backlog", "next", "active", "verifying", "done", "blocked")
ID_RE = re.compile(r"^F-\d{3,}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TEXT_FIELDS = ("id", "title", "area", "status", "behavior", "next_step", "notes", "updated")


class FeatureError(ValueError):
    pass


def empty():
    return {"version": 1, "features": []}


def validate(data):
    if not isinstance(data, dict):
        return ["the file must hold a JSON object"]
    errors = []
    if data.get("version") != 1:
        errors.append("version must be 1")
    features = data.get("features")
    if not isinstance(features, list):
        return errors + ["features must be an array"]
    seen = set()
    for index, item in enumerate(features):
        where = f"features[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{where} must be an object")
            continue
        for field in TEXT_FIELDS:
            if not isinstance(item.get(field), str):
                errors.append(f"{where}.{field} must be a string")
        fid = item.get("id")
        if isinstance(fid, str):
            if not ID_RE.match(fid):
                errors.append(f"{where}: id must look like F-001, got {fid!r}")
            elif fid in seen:
                errors.append(f"{where}: {fid} is used more than once")
            seen.add(fid)
        if isinstance(item.get("title"), str) and not item["title"].strip():
            errors.append(f"{where}.title must not be empty")
        if item.get("status") not in STATUSES:
            errors.append(f"{where}.status must be one of {', '.join(STATUSES)}")
        steps = item.get("verification")
        if not (isinstance(steps, list) and all(isinstance(step, str) for step in steps)):
            errors.append(f"{where}.verification must be an array of strings")
        if isinstance(item.get("updated"), str) and not DATE_RE.match(item["updated"]):
            errors.append(f"{where}.updated must be a date like 2026-09-17")
    return errors


def load(path):
    path = Path(path)
    if not path.is_file():
        raise FeatureError(f"{path.name} not found. Fix: run cdev-init, or create it with feature.py add")
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise FeatureError(f"{path.name} is not valid JSON ({exc}). Fix: repair it or restore it from git") from exc
    errors = validate(data)
    if errors:
        raise FeatureError(f"{path.name} is invalid:\n- " + "\n- ".join(errors))
    return data


def save(path, data):
    errors = validate(data)
    if errors:
        raise FeatureError("refusing to write an invalid feature list:\n- " + "\n- ".join(errors))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def next_id(data):
    numbers = [int(item["id"][2:]) for item in data["features"]]
    return f"F-{max(numbers, default=0) + 1:03d}"


def find(data, fid):
    for item in data["features"]:
        if item["id"] == fid:
            return item
    known = ", ".join(item["id"] for item in data["features"]) or "none"
    raise FeatureError(f"{fid} not found. Known ids: {known}")


def add(data, title, today, area="", behavior="", verification=(), status="backlog"):
    item = {"id": next_id(data), "title": title, "area": area, "status": status,
            "behavior": behavior, "verification": list(verification), "next_step": "",
            "notes": "", "updated": today}
    data["features"].append(item)
    return item


def update(data, fid, today, status=None, next_step=None, notes=None, behavior=None, verification=None):
    if all(value is None for value in (status, next_step, notes, behavior, verification)):
        raise FeatureError("give at least one of --status, --next, --notes, --behavior, --verify")
    item = find(data, fid)
    for field, value in (("status", status), ("next_step", next_step), ("notes", notes), ("behavior", behavior)):
        if value is not None:
            item[field] = value
    if verification:
        item["verification"].extend(verification)
    item["updated"] = today
    return item


def line(item):
    text = f"{item['id']}  {item['status']:<9}  {item['title']}"
    return text + (f"  (next: {item['next_step']})" if item["next_step"] else "")


def build_parser():
    parser = argparse.ArgumentParser(prog="feature.py", description="Keep feature_list.json valid")
    parser.add_argument("--file", default=str(DEFAULT_FILE), help="path to feature_list.json")
    sub = parser.add_subparsers(dest="command", required=True)

    add_parser = sub.add_parser("add", help="add a feature")
    add_parser.add_argument("--title", required=True)
    add_parser.add_argument("--area", default="")
    add_parser.add_argument("--behavior", default="")
    add_parser.add_argument("--verify", action="append", default=[])
    add_parser.add_argument("--status", choices=STATUSES, default="backlog")

    set_parser = sub.add_parser("set", help="update a feature")
    set_parser.add_argument("id")
    set_parser.add_argument("--status", choices=STATUSES)
    set_parser.add_argument("--next", dest="next_step")
    set_parser.add_argument("--notes")
    set_parser.add_argument("--behavior")
    set_parser.add_argument("--verify", action="append")

    show_parser = sub.add_parser("show", help="list features, or print one")
    show_parser.add_argument("id", nargs="?")
    show_parser.add_argument("--status", choices=STATUSES)

    sub.add_parser("check", help="validate the file")
    return parser


def main(argv=None, today=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    args = build_parser().parse_args(argv)
    today = today or date.today().isoformat()
    path = Path(args.file)
    try:
        if args.command == "add":
            data = load(path) if path.is_file() else empty()
            item = add(data, args.title, today, area=args.area, behavior=args.behavior,
                       verification=args.verify, status=args.status)
            save(path, data)
            print(f"added {item['id']}: {item['title']}")
        elif args.command == "set":
            data = load(path)
            item = update(data, args.id, today, status=args.status, next_step=args.next_step,
                          notes=args.notes, behavior=args.behavior, verification=args.verify)
            save(path, data)
            print(line(item))
        elif args.command == "show":
            data = load(path)
            if args.id:
                print(json.dumps(find(data, args.id), ensure_ascii=False, indent=2))
            else:
                shown = [item for item in data["features"] if args.status in (None, item["status"])]
                print("\n".join(line(item) for item in shown) if shown else "no features")
        else:
            data = load(path)
            print(f"{path.name}: {len(data['features'])} features, valid")
    except FeatureError as exc:
        print(f"feature.py failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
