"""List the MCP servers this repository and this machine configure, so the agent can see what it may reach for."""
import argparse
import json
import os
import platform
import sys
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_FILES = (".vscode/mcp.json", ".mcp.json")


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
    return [folder / "mcp.json" for folder in folders] + [home / ".copilot" / "mcp.json"]


def servers_in(path):
    """(name, how it starts) for every server in one config file."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return []
    block = data.get("servers") or data.get("mcpServers") or {}
    found = []
    for name, spec in block.items() if isinstance(block, dict) else []:
        if not isinstance(spec, dict):
            continue
        if spec.get("url"):
            how = spec["url"]
        else:
            how = " ".join([str(spec.get("command", ""))] + [str(a) for a in spec.get("args", [])]).strip()
        found.append((name, how or "unknown"))
    return sorted(found)


def collect(root):
    """[(source, [(name, how), ...]), ...] for the workspace first, then this machine."""
    root = Path(root)
    result = []
    for name in WORKSPACE_FILES:
        path = root / name
        if path.is_file():
            result.append((str(path), servers_in(path)))
    for path in user_files():
        if path.is_file():
            result.append((str(path), servers_in(path)))
    return result


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
        print(json.dumps([{"source": source, "servers": [{"name": n, "starts": h} for n, h in servers]}
                          for source, servers in found], ensure_ascii=False, indent=2))
        return 0

    total = sum(len(servers) for _, servers in found)
    if not total:
        print("mcp_list: no MCP server is configured for this repository or this machine.")
        print("  A server is added in .vscode/mcp.json, or in the user mcp.json through the command palette.")
        return 0
    print(f"mcp_list: {total} MCP server(s) configured. Their tools reach chat in agent mode when enabled.")
    for source, servers in found:
        print(f"\n{source}")
        for name, how in servers:
            print(f"- {name}: {how}")
    print("\nThe tools each server offers are listed in the chat Configure Tools picker.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
