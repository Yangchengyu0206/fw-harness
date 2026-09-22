"""The MCP listing is what tells the agent which servers exist, so it reads both config shapes and never raises."""
import json
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[2] / "plugins" / "cdev" / "skills" / "cdev-init" / "templates" / "tools"
sys.path.insert(0, str(TOOLS))

import mcp_list  # noqa: E402

VSCODE = {"servers": {"datasheets": {"command": "npx", "args": ["-y", "datasheet-mcp"]},
                      "git-branches": {"url": "http://localhost:4000/mcp"}}}
CLAUDE = {"mcpServers": {"ap-notes": {"command": "uvx", "args": ["ap-notes-mcp"]}}}


def write(root, name, data):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def test_the_vscode_shape_is_read(tmp_path):
    write(tmp_path, ".vscode/mcp.json", VSCODE)
    (source, servers), = [entry for entry in mcp_list.collect(tmp_path) if ".vscode" in entry[0]]
    assert servers == [("datasheets", "npx -y datasheet-mcp"), ("git-branches", "http://localhost:4000/mcp")]


def test_the_claude_shape_is_read(tmp_path):
    write(tmp_path, ".mcp.json", CLAUDE)
    found = dict(mcp_list.collect(tmp_path))
    assert found[str(tmp_path / ".mcp.json")] == [("ap-notes", "uvx ap-notes-mcp")]


def test_a_repository_with_no_config_says_so(tmp_path, capsys):
    assert mcp_list.main(["--root", str(tmp_path)]) == 0
    assert "no MCP server is configured" in capsys.readouterr().out


def test_broken_json_is_skipped_rather_than_raised(tmp_path):
    (tmp_path / ".vscode").mkdir()
    (tmp_path / ".vscode" / "mcp.json").write_text("{ this is not json", encoding="utf-8")
    assert mcp_list.servers_in(tmp_path / ".vscode" / "mcp.json") == []


def test_the_listing_names_each_server_and_how_it_starts(tmp_path, capsys):
    write(tmp_path, ".vscode/mcp.json", VSCODE)
    assert mcp_list.main(["--root", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "datasheets: npx -y datasheet-mcp" in out and "Configure Tools" in out


def test_json_output_is_machine_readable(tmp_path, capsys):
    write(tmp_path, ".vscode/mcp.json", VSCODE)
    assert mcp_list.main(["--root", str(tmp_path), "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    names = [server["name"] for entry in data for server in entry["servers"]]
    assert "datasheets" in names and "git-branches" in names
