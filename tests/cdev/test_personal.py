"""A personal harness keeps its markdown out of every commit, in the repository and in its submodules."""
import subprocess
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[2] / "plugins" / "cdev" / "skills" / "cdev-init" / "templates" / "tools"
sys.path.insert(0, str(TOOLS))

import doc_check  # noqa: E402
import personal  # noqa: E402


def git(cwd, *args):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "protocol.file.allow=always",
                           *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def write(root, name, text=""):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def project(tmp_path):
    alg = tmp_path / "alg_origin"
    write(alg, "src/filter.c")
    write(alg, "README.md", "# ALG\n")
    git(alg, "init", "-q")
    git(alg, "add", "-A")
    git(alg, "commit", "-qm", "alg")
    root = tmp_path / "proj"
    write(root, "src/main.c")
    git(root, "init", "-q")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "base")
    git(root, "submodule", "add", "-q", str(alg), "ALG")
    git(root, "commit", "-qm", "add ALG")
    return root


def untracked(repo):
    return git(repo, "status", "--porcelain", "--untracked-files=all")


def test_markdown_stays_out_of_the_repository_and_the_submodule(project):
    assert dict(personal.ensure(project)) == {".": "set", "ALG": "set"}
    write(project, "AGENTS.md", "# rules\n")
    write(project, "src/ARCHITECTURE.md", "# src\n")
    write(project, "ALG/src/ARCHITECTURE.md", "# ALG/src\n")
    write(project, "ALG/src/new.c")
    write(project, "tools/feature.py")
    write(project, "feature_list.json", "{}")
    assert ".md" not in untracked(project) and "tools/" not in untracked(project)
    assert "feature_list" not in untracked(project)
    assert untracked(project / "ALG").strip() == "?? src/new.c"


def test_running_it_again_changes_nothing(project):
    personal.ensure(project)
    exclude = personal.exclude_file(project)
    before = exclude.read_text(encoding="utf-8")
    assert dict(personal.ensure(project)) == {".": "already", "ALG": "already"}
    assert exclude.read_text(encoding="utf-8") == before


def test_tracked_markdown_stays_tracked(project):
    personal.ensure(project)
    write(project, "ALG/README.md", "# ALG, edited\n")
    assert untracked(project / "ALG").strip() == "M README.md"


def test_check_reports_without_changing(project, capsys):
    assert personal.main(["--root", str(project), "--check"]) == 1
    assert "Fix: py -3 tools/personal.py" in capsys.readouterr().out
    assert not personal.excluded(personal.exclude_file(project))


def test_doc_check_still_sees_the_excluded_documents(project):
    personal.ensure(project)
    write(project, "ARCHITECTURE.md", "## Map\n\n| [src](src/ARCHITECTURE.md) | code |\n"
                                      "| [ALG/src](ALG/src/ARCHITECTURE.md) | submodule ALG, edited a lot |\n")
    write(project, "src/ARCHITECTURE.md", "# src\n\n## Files\n\n- `main.c`: entry\n")
    write(project, "ALG/src/ARCHITECTURE.md", "# ALG/src\n\n## Files\n\n- `filter.c`: filter\n")
    assert doc_check.check(project) == ([], [])


def test_team_takes_out_only_what_personal_added(project):
    exclude = personal.exclude_file(project)
    exclude.parent.mkdir(parents=True, exist_ok=True)
    exclude.write_text("# mine\n*.log\n", encoding="utf-8")
    personal.ensure(project)
    write(project, "AGENTS.md", "# rules\n")
    assert "AGENTS.md" not in untracked(project)
    assert dict(personal.share(project)) == {".": "removed", "ALG": "removed"}
    assert exclude.read_text(encoding="utf-8") == "# mine\n*.log\n"
    assert "AGENTS.md" in untracked(project)
