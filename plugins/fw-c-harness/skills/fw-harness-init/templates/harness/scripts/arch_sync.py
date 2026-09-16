"""fw-architecture-sync helper: draft harness/architecture.json and refresh ARCHITECTURE.md (spec section 6.1)."""
import argparse
import sys
from pathlib import Path

import arch_docs
from arch_check import ARCH_PATH, ArchitectureError, load_architecture, module_of, source_files
from arch_scan import draft_architecture
from console import use_utf8_stdio
from gitutil import repo_root
from harness_config import ConfigError, load_config
from jsonio import read_json, write_json_atomic, write_text_atomic

PROPOSED_SUFFIX = ".harness-proposed"
DOC_NAME = "ARCHITECTURE.md"


def is_skeleton(path):
    path = Path(path)
    if not path.is_file():
        return True
    try:
        return not read_json(path).get("modules")
    except (ValueError, UnicodeDecodeError):
        return False


def scan(repo, force=False):
    config = load_config(repo)
    arch, report = draft_architecture(repo, config)
    if not arch["modules"]:
        raise ArchitectureError("found no C sources to scan. "
                                "Fix: run this from a repository that has .c or .h files committed or untracked")
    target = Path(repo) / ARCH_PATH
    written = ARCH_PATH
    if not (force or is_skeleton(target)):
        target = target.with_name(target.name + PROPOSED_SUFFIX)
        written = ARCH_PATH + PROPOSED_SUFFIX
    write_json_atomic(target, arch)
    return written, arch, report


def _sync(doc, block, build_new):
    text = doc.read_text(encoding="utf-8") if doc.is_file() else None
    updated = arch_docs.apply_block(text, block) if text is not None else build_new(block)
    if updated == text:
        return False
    write_text_atomic(doc, updated)
    return True


def docs(repo):
    repo = Path(repo)
    arch = load_architecture(repo)
    grouped = {path: [] for path in arch["modules"]}
    for name in source_files(repo):
        module = module_of(name, grouped)
        if module is not None:
            grouped[module].append(name)

    written = []
    for path in sorted(arch["modules"]):
        folder = repo / path
        if not folder.is_dir():
            continue
        block = arch_docs.render_block(path, arch)
        summary = arch_docs.summary_for(path, grouped[path])
        if _sync(folder / DOC_NAME, block, lambda b, p=path, s=summary: arch_docs.new_document(p, s, b)):
            written.append(f"{path}/{DOC_NAME}")
    if _sync(repo / DOC_NAME, arch_docs.render_root(arch), arch_docs.new_root_document):
        written.append(DOC_NAME)
    return written


def main(argv=None, cwd=None):
    use_utf8_stdio()
    parser = argparse.ArgumentParser(prog="arch_sync",
                                     description="Draft architecture.json and refresh ARCHITECTURE.md")
    sub = parser.add_subparsers(dest="command", required=True)
    scan_parser = sub.add_parser("scan", help="write a draft architecture.json from the tree")
    scan_parser.add_argument("--force", action="store_true", help="overwrite an approved architecture.json")
    sub.add_parser("docs", help="create or refresh every ARCHITECTURE.md")
    args = parser.parse_args(argv)

    repo = repo_root(cwd or Path.cwd())
    try:
        if args.command == "scan":
            written, arch, report = scan(repo, force=args.force)
            print(f"arch_sync: wrote {written} with {len(arch['modules'])} modules")
            for source, target in report["reverse"]:
                print(f"arch_sync: grandfathered reverse dependency {source} -> {target}. "
                      "Fix it or have a human confirm it stays")
            for name in report["root_sources"]:
                print(f"arch_sync: {name} sits at the repository root and belongs to no module. "
                      "Fix: move it into a folder")
            if written.endswith(PROPOSED_SUFFIX):
                print(f"arch_sync: {ARCH_PATH} already holds approved rules, so the draft went to {written}. "
                      "Fix: compare them and copy over the parts a human approves")
        else:
            for name in docs(repo):
                print(f"arch_sync: wrote {name}")
            print("arch_sync: documents match harness/architecture.json")
    except (ArchitectureError, ConfigError) as exc:
        print(f"arch_sync failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
