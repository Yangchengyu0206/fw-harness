"""List the MCP servers this repository and this machine configure, so the agent can see what it may reach for."""
import argparse
import json
import os
import platform
import sys
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_FILES = (".vscode/mcp.json", ".mcp.json", ".vscode/settings.json")


def user_files():
    home = Path.home()
    if platform.system() == "Windows":
        appdata = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))
        folders = [appdata / "Code" / "User", appdata / "Code - Insiders" / "User"]
    elif platform.system() == "Darwin":
        base = home / "Library" / "Application Support"
        folders = [base / "Code" / "User", base / "Code - Insiders" / "User"]
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
        folders = [base / "Code" / "User", base / "Code - Insiders" / "User"]
    files = []
    for folder in folders:
        files += [folder / "mcp.json", folder / "settings.json"]
    return files + [home / ".copilot" / "mcp.json", home / ".claude.json"]


def strip_jsonc(text):
    """JSON with comments and trailing commas, as VS Code writes it, turned into plain JSON."""
    out, i, in_string = [], 0, False
    while i < len(text):
        char = text[i]
        if in_string:
            out.append(char)
            if char == "\\" and i + 1 < len(text):
                out.append(text[i + 1])
                i += 1
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
            out.append(char)
        elif text.startswith("//", i):
            end = text.find("\n", i)
            i = len(text) if end < 0 else end
            continue
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            i = len(text) if end < 0 else end + 2
            continue
        elif char in "}]":
            while out and out[-1] in " \t\r\n":
                out.pop()
            if out and out[-1] == ",":
                out.pop()
            out.append(char)
        else:
            out.append(char)
        i += 1
    return "".join(out)


def read_config(path):
    """(data, None), or (None, why it could not be read)."""
    try:
        text = Path(path).read_text(encoding="utf-8-sig")
    except OSError as exc:
        return None, str(exc)
    try:
        return json.loads(strip_jsonc(text)), None
    except json.JSONDecodeError as exc:
        return None, f"not valid JSON ({exc})"


def server_blocks(data, path, root):
    """Every block of servers one config file holds, whichever tool's shape it is in."""
    if not isinstance(data, dict):
        return []
    blocks = [data.get("servers"), data.get("mcpServers")]
    mcp = data.get("mcp")
    if Path(path).name == "settings.json" and isinstance(mcp, dict):
        blocks.append(mcp.get("servers"))
    projects = data.get("projects")
    if Path(path).name == ".claude.json" and isinstance(projects, dict) and root is not None:
        here = Path(root).resolve()
        for key, project in projects.items():
            if isinstance(project, dict) and Path(key).resolve() == here:
                blocks.append(project.get("mcpServers"))
    return [block for block in blocks if isinstance(block, dict)]


def servers_from(data, path, root=None):
    found = {}
    for block in server_blocks(data, path, root):
        for name, spec in block.items():
            if not isinstance(spec, dict):
                continue
            if spec.get("url"):
                how = spec["url"]
            else:
                how = " ".join([str(spec.get("command", ""))] + [str(a) for a in spec.get("args", [])]).strip()
            found[name] = how or "unknown"
    return sorted(found.items())


def servers_in(path, root=None):
    """(name, how it starts) for every server in one config file; [] when it cannot be read."""
    data, _ = read_config(path)
    return servers_from(data, path, root) if data is not None else []


def collect(root):
    """[(source, servers or None, error or None), ...] for the workspace first, then this machine.

    A file that holds no servers is left out; a file that cannot be read is kept, so the reader
    is not told there are no servers when the truth is that the file is broken.
    """
    root = Path(root)
    result = []
    for path in [root / name for name in WORKSPACE_FILES] + user_files():
        if not path.is_file():
            continue
        data, error = read_config(path)
        if error:
            if path.name != "settings.json":
                result.append((str(path), None, error))
            continue
        servers = servers_from(data, path, root)
        if servers or path.name in ("mcp.json", ".mcp.json"):
            result.append((str(path), servers, None))
    return result


def names(root):
    """The configured server names, without duplicates, for a one-line summary."""
    seen = []
    for _, servers, _ in collect(root):
        for name, _ in servers or []:
            if name not in seen:
                seen.append(name)
    return seen


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(prog="mcp_list.py", description=__doc__)
    parser.add_argument("--root", default=str(DEFAULT_ROOT))
    parser.add_argument("--json", action="store_true", help="print the same thing as JSON")
    args = parser.parse_args(argv)

    found = collect(args.root)
    if args.json:
        print(json.dumps([{"source": source, "error": error,
                           "servers": None if servers is None else [{"name": n, "starts": h} for n, h in servers]}
                          for source, servers, error in found], ensure_ascii=False, indent=2))
        return 0

    total = sum(len(servers or []) for _, servers, _ in found)
    broken = [(source, error) for source, servers, error in found if servers is None]
    if not total:
        print("mcp_list: no MCP server is configured for this repository or this machine.")
        print("  A server is added in .vscode/mcp.json, or in the user mcp.json through the command palette.")
    else:
        print(f"mcp_list: {total} MCP server(s) configured. Their tools reach chat in agent mode when enabled.")
        for source, servers, _ in found:
            if servers:
                print(f"\n{source}")
                for name, how in servers:
                    print(f"- {name}: {how}")
        print("\nThe tools each server offers are listed in the chat Configure Tools picker.")
    for source, error in broken:
        print(f"\n{source} could not be read: {error}. Servers it configures are not counted above.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
