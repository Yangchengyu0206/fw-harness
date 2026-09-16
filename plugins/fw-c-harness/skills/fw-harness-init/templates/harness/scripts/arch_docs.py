"""Render the generated block in ARCHITECTURE.md from harness/architecture.json (spec section 6.2)."""
import posixpath

BEGIN = "<!-- fw-harness:architecture:begin -->"
END = "<!-- fw-harness:architecture:end -->"
NOTICE = "<!-- Generated from harness/architecture.json. Run fw-architecture-sync after changing it. -->"
READ_ONLY = ("Read-only. Upgrade this folder from its upstream source instead of editing it here, "
             "and record the version in the section above.")


def _grandfathered_from(path, arch):
    prefix = path + " -> "
    return [entry[len(prefix):] for entry in sorted(arch["grandfathered"]) if entry.startswith(prefix)]


def render_block(path, arch):
    module = arch["modules"][path]
    lines = [BEGIN, NOTICE, "", f"- Kind: {module['kind']}"]
    if module["kind"] in ("vendor", "generated"):
        lines.append(f"- {READ_ONLY}")
    lines.append("- Approved dependencies: " + (", ".join(module["allowed_deps"]) or "none"))
    owed = _grandfathered_from(path, arch)
    if owed:
        lines.append("- Grandfathered dependencies (remove them, do not add more): " + ", ".join(owed))
    lines += ["", END]
    return "\n".join(lines)


def render_root(arch):
    lines = [BEGIN, NOTICE, "",
             "| Module | Kind | Approved dependencies |",
             "|---|---|---|"]
    for path in sorted(arch["modules"]):
        module = arch["modules"][path]
        lines.append(f"| {path} | {module['kind']} | {', '.join(module['allowed_deps']) or 'none'} |")
    if arch["grandfathered"]:
        lines += ["", "Grandfathered dependencies (the list may only shrink):"]
        lines += [f"- {entry}" for entry in sorted(arch["grandfathered"])]
    lines += ["", END]
    return "\n".join(lines)


def block_of(text):
    start = text.find(BEGIN)
    end = text.find(END)
    if start < 0 or end < start:
        return None
    return text[start:end + len(END)]


def apply_block(text, block):
    current = block_of(text)
    if current is not None:
        return text.replace(current, block)
    body = text.rstrip("\n")
    return (body + "\n\n" if body else "") + block + "\n"


def summary_for(path, files):
    sources = sum(1 for name in files if name.endswith(".c"))
    headers = sorted(name for name in files if name.endswith(".h"))
    shown = ", ".join(posixpath.basename(name) for name in headers[:3]) if headers else "none"
    return f"Holds {sources} .c and {len(headers)} .h files. Public headers: {shown}."


def new_document(path, summary, block):
    return "\n".join([
        f"# {path}",
        "",
        "## Responsibility",
        "",
        f"{summary} Written by fw-harness from the file listing, so replace this line with the "
        "one sentence a new colleague needs.",
        "",
        "## Entry points",
        "",
        "List the functions other modules are meant to call, and where the module is initialised.",
        "",
        "## ISR and memory notes",
        "",
        "List interrupt handlers, state shared with the main loop, buffers, and who owns them.",
        "",
        "## Approved dependencies",
        "",
        block,
        "",
    ])


def new_root_document(block):
    return "\n".join([
        "# Repository architecture",
        "",
        "## How to read this map",
        "",
        "Each module below has its own ARCHITECTURE.md next to the code. Read that one before "
        "changing a file. A module may include headers only from its approved dependencies; "
        "`check` enforces the table.",
        "",
        "## Modules",
        "",
        block,
        "",
        "## Adding a module",
        "",
        "Create the folder, run fw-architecture-sync, then have a human approve the new "
        "dependencies in harness/architecture.json.",
        "",
    ])
