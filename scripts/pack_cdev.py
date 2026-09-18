"""Build a zip of the cdev plugin for a machine that cannot reach the marketplace."""
import argparse
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "cdev"
EXTRA = ("LICENSE", "THIRD_PARTY_NOTICES.md")
INSTALLER = ROOT / "scripts" / "install_local.py"
SKIP_PARTS = {"__pycache__", ".pytest_cache"}
SKIP_SUFFIXES = {".pyc"}


def version():
    return json.loads((PLUGIN / "plugin.json").read_text(encoding="utf-8"))["version"]


def wanted(path):
    return (path.is_file()
            and not SKIP_PARTS & set(path.parts)
            and path.suffix not in SKIP_SUFFIXES)


def entries():
    """(archive path, source path) for everything the package holds."""
    found = [(path.relative_to(PLUGIN).as_posix(), path)
             for path in sorted(PLUGIN.rglob("*")) if wanted(path)]
    found += [(name, ROOT / name) for name in EXTRA if (ROOT / name).is_file()]
    found.append((INSTALLER.name, INSTALLER))
    return found


def build(out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"cdev-{version()}.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, source in entries():
            archive.write(source, f"cdev/{name}")
    return target


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(prog="pack_cdev.py", description=__doc__)
    parser.add_argument("--out", default=str(ROOT / "dist"), help="where the zip is written")
    args = parser.parse_args(argv)
    target = build(args.out)
    with zipfile.ZipFile(target) as archive:
        count = len(archive.namelist())
    print(f"{target} ({count} files, {target.stat().st_size // 1024} KB)")
    print("The person who receives it unzips it, then runs: py -3 cdev/install_local.py")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
