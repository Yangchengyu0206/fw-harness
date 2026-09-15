"""Architecture gate (spec section 6.3): module coverage, approved include dependencies, and the grandfather ratchet."""
import json
import posixpath
import re
import sys
from collections import defaultdict
from pathlib import Path

from console import use_utf8_stdio
from gitutil import git, repo_root
from jsonio import read_json
from ratchet import baseline_ref, baseline_text, new_entries

ARCH_PATH = "harness/architecture.json"
KINDS = ("owned", "vendor", "generated", "test")
READ_ONLY_KINDS = ("vendor", "generated")
SOURCE_SUFFIXES = (".c", ".h")
INCLUDE_RE = re.compile(r'^[ \t]*#[ \t]*include[ \t]*[<"]([^">\n]+)[">]', re.MULTILINE)
EDGE_RE = re.compile(r"^(\S+) -> (\S+)$")


class ArchitectureError(ValueError):
    pass


def validate_architecture(arch):
    if not isinstance(arch, dict):
        return ["architecture must be a JSON object"]
    errors = []
    if arch.get("version") != 1:
        errors.append("version must be 1")
    include_dirs = arch.get("include_dirs")
    if not (isinstance(include_dirs, list) and all(isinstance(d, str) and d for d in include_dirs)):
        errors.append("include_dirs must be an array of repo-relative folders")
    modules = arch.get("modules")
    if not isinstance(modules, dict):
        return errors + ["modules must be an object keyed by repo-relative folder"]
    for path, module in modules.items():
        if (not path or path.startswith("/") or "\\" in path
                or path.endswith("/") or path != posixpath.normpath(path)):
            errors.append(f"modules key {path!r} must be a normalized repo-relative folder "
                          "with forward slashes and no trailing slash")
        if not isinstance(module, dict) or module.get("kind") not in KINDS:
            errors.append(f"modules[{path!r}].kind must be one of {', '.join(KINDS)}")
            continue
        deps = module.get("allowed_deps")
        if not (isinstance(deps, list) and all(isinstance(dep, str) for dep in deps)):
            errors.append(f"modules[{path!r}].allowed_deps must be an array of module folders")
            continue
        for dep in deps:
            if dep not in modules:
                errors.append(f"modules[{path!r}].allowed_deps names {dep!r}, which is not a module")
    grandfathered = arch.get("grandfathered")
    if not isinstance(grandfathered, list):
        errors.append('grandfathered must be an array of "<module> -> <module>" strings')
    else:
        for entry in grandfathered:
            match = EDGE_RE.match(entry) if isinstance(entry, str) else None
            if not match or match.group(1) not in modules or match.group(2) not in modules:
                errors.append(f'grandfathered entry {entry!r} must look like "<module> -> <module>"')
    return errors


def load_architecture(repo):
    path = Path(repo) / ARCH_PATH
    if not path.is_file():
        raise ArchitectureError(f"{ARCH_PATH} not found. Fix: run fw-harness-init to create it")
    try:
        arch = read_json(path)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ArchitectureError(f"{ARCH_PATH} is not valid JSON ({exc}). Fix: repair it or restore it from git") from exc
    errors = validate_architecture(arch)
    if errors:
        raise ArchitectureError(f"{ARCH_PATH} is invalid:\n- " + "\n- ".join(errors))
    return arch


def module_of(path, modules):
    matches = [module for module in modules if path == module or path.startswith(module + "/")]
    return max(matches, key=len) if matches else None


def read_only_prefixes(arch):
    return [path for path, module in arch["modules"].items() if module["kind"] in READ_ONLY_KINDS]


def source_files(repo):
    listing = git(repo, "-c", "core.quotepath=off", "ls-files", "--cached", "--others", "--exclude-standard")
    return sorted(name for name in listing.splitlines()
                  if name.endswith(SOURCE_SUFFIXES) and (Path(repo) / name).is_file())


def _resolve(repo, including_file, target, include_dirs):
    for base in [posixpath.dirname(including_file), *include_dirs]:
        candidate = posixpath.normpath(posixpath.join(base, target))
        if not candidate.startswith("..") and (Path(repo) / candidate).is_file():
            return candidate
    return None


def dependencies(repo, arch, files):
    modules = arch["modules"]
    found = defaultdict(list)
    for name in files:
        source = module_of(name, modules)
        if source is None or modules[source]["kind"] != "owned":
            continue
        text = (Path(repo) / name).read_text(encoding="utf-8", errors="replace")
        for match in INCLUDE_RE.finditer(text):
            resolved = _resolve(repo, name, match.group(1), arch["include_dirs"])
            target = module_of(resolved, modules) if resolved else None
            if target is None or target == source:
                continue
            line = text.count("\n", 0, match.start()) + 1
            found[(source, target)].append(f"{name}:{line}")
    return found


def check_architecture(repo):
    arch = load_architecture(repo)
    modules = arch["modules"]
    errors, warnings = [], []

    files = source_files(repo)
    uncovered = sorted({posixpath.dirname(name) or "." for name in files if module_of(name, modules) is None})
    for folder in uncovered:
        errors.append(f"{folder}: C sources are not covered by any module in {ARCH_PATH}. "
                      "Fix: run fw-architecture-sync")
    for path in sorted(modules):
        if not (Path(repo) / path).is_dir():
            warnings.append(f"{path}: listed in {ARCH_PATH} but the folder no longer exists. Fix: remove it from modules")
        elif not (Path(repo) / path / "ARCHITECTURE.md").is_file():
            errors.append(f"{path}: missing ARCHITECTURE.md. Fix: run fw-architecture-sync")

    grandfathered = set(arch["grandfathered"])
    violations = set()
    for (source, target), where in sorted(dependencies(repo, arch, files).items()):
        if target in modules[source]["allowed_deps"]:
            continue
        edge = f"{source} -> {target}"
        violations.add(edge)
        if edge not in grandfathered:
            shown = ", ".join(where[:3]) + (", ..." if len(where) > 3 else "")
            errors.append(f"{edge}: dependency not approved ({shown}). "
                          f"Fix: remove the include, or have a human approve it in {ARCH_PATH}")
    for edge in sorted(grandfathered - violations):
        warnings.append(f"{edge}: grandfathered but no longer violated. Fix: remove it from the grandfather list")

    ref, warning = baseline_ref(repo)
    if warning:
        warnings.append(warning)
    base = baseline_text(repo, ref, ARCH_PATH)
    base_entries = None
    if base is not None:
        try:
            base_entries = json.loads(base).get("grandfathered", [])
        except (json.JSONDecodeError, AttributeError):
            base_entries = None
    added = new_entries(grandfathered, base_entries)
    if added:
        errors.append(f"{ARCH_PATH} grandfather list gained entries not on {ref}: {', '.join(added)}. "
                      "The list may only shrink. Fix: remove the new dependency instead of grandfathering it")
    return errors, warnings


def main(argv=None):
    use_utf8_stdio()
    repo = repo_root(Path.cwd())
    try:
        errors, warnings = check_architecture(repo)
    except ArchitectureError as exc:
        print(f"arch_check failed: {exc}", file=sys.stderr)
        return 1
    for warning in warnings:
        print(f"arch_check: {warning}")
    for error in errors:
        print(f"arch_check failed: {error}", file=sys.stderr)
    if errors:
        return 1
    print("arch_check: passed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
