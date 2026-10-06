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
    (source, servers, error), = [entry for entry in mcp_list.collect(tmp_path) if ".vscode" in entry[0]]
    assert error is None and servers == [("datasheets", "npx -y datasheet-mcp"), ("git-branches", "http://localhost:4000/mcp")]


def test_the_claude_shape_is_read(tmp_path):
    write(tmp_path, ".mcp.json", CLAUDE)
    found = {source: servers for source, servers, _ in mcp_list.collect(tmp_path)}
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


def test_comments_and_trailing_commas_are_read_and_urls_survive(tmp_path):
    (tmp_path / ".vscode").mkdir()
    (tmp_path / ".vscode" / "mcp.json").write_text(
        '{\n  // the company servers\n  "servers": {\n    /* docs */\n'
        '    "himax-rag": {"type": "http", "url": "http://rag.local:8000/api/v1/mcp/",},\n  },\n}\n',
        encoding="utf-8")
    assert mcp_list.servers_in(tmp_path / ".vscode" / "mcp.json") == [
        ("himax-rag", "http://rag.local:8000/api/v1/mcp/")]


def test_servers_in_vscode_settings_are_read(tmp_path):
    write(tmp_path, ".vscode/settings.json", {"editor.tabSize": 4, "mcp": {"servers": {"gitlab": {"url": "http://g/mcp"}}}})
    assert "gitlab" in mcp_list.names(tmp_path)


def test_a_settings_file_without_servers_is_not_listed(tmp_path):
    write(tmp_path, ".vscode/settings.json", {"editor.tabSize": 4})
    assert not [entry for entry in mcp_list.collect(tmp_path) if entry[0].startswith(str(tmp_path))]


def test_claude_json_project_servers_count_for_this_root_only(tmp_path):
    other = tmp_path / "other"
    other.mkdir()
    data = {"mcpServers": {"everywhere": {"command": "x"}},
            "projects": {str(tmp_path): {"mcpServers": {"here": {"command": "y"}}},
                         str(other): {"mcpServers": {"elsewhere": {"command": "z"}}}}}
    path = tmp_path / ".claude.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert [name for name, _ in mcp_list.servers_in(path, root=tmp_path)] == ["everywhere", "here"]


def test_a_broken_file_is_reported_rather_than_counted_as_empty(tmp_path, capsys):
    (tmp_path / ".vscode").mkdir()
    (tmp_path / ".vscode" / "mcp.json").write_text("{ this is not json", encoding="utf-8")
    assert mcp_list.main(["--root", str(tmp_path)]) == 0
    assert "could not be read" in capsys.readouterr().out
