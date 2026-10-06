import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[2] / "plugins" / "cdev" / "skills" / "cdev-init" / "templates" / "tools"
sys.path.insert(0, str(TOOLS))

import doc_check  # noqa: E402

ROOT_DOC = "# Architecture\n\n## Map\n\n| Folder | Role |\n|---|---|\n| [src](src/ARCHITECTURE.md) | code |\n"
FOLDER_DOC = "# src\n\n## Files\n\n- `main.c`: entry\n- `hal_*.c`: drivers\n\n## Flows\n\nboot\n"


def write(root, name, text=""):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def repo(tmp_path, folder_doc=FOLDER_DOC, root_doc=ROOT_DOC, files=("main.c", "hal_uart.c", "hal_spi.c")):
    write(tmp_path, "ARCHITECTURE.md", root_doc)
    write(tmp_path, "src/ARCHITECTURE.md", folder_doc)
    for name in files:
        write(tmp_path, f"src/{name}")
    return tmp_path


def test_documents_that_match_report_nothing(tmp_path, capsys):
    assert doc_check.main(["--root", str(repo(tmp_path))]) == 0
    assert "match" in capsys.readouterr().out


def test_an_unlisted_file_is_reported(tmp_path):
    root = repo(tmp_path, files=("main.c", "hal_uart.c", "retry.c"))
    assert doc_check.check(root)[0] == ["src/ARCHITECTURE.md: src/retry.c is not listed"]


def test_a_listed_file_that_is_gone_is_reported(tmp_path):
    root = repo(tmp_path, files=("hal_uart.c",))
    assert doc_check.check(root)[0] == ["src/ARCHITECTURE.md: lists main.c, which is not in src/"]


def test_subfolder_files_belong_to_the_subfolder_document(tmp_path):
    root = repo(tmp_path)
    write(root, "src/sub/deep.c")
    assert doc_check.check(root)[0] == []


def test_a_document_without_a_files_section_is_reported(tmp_path):
    root = repo(tmp_path, folder_doc="# src\n\n## Responsibility\n\ncode\n")
    assert doc_check.check(root)[0] == ["src/ARCHITECTURE.md: has no ## Files section"]


def test_the_root_map_must_link_every_folder_document(tmp_path):
    root = repo(tmp_path, root_doc="# Architecture\n\n## Map\n\n| [lib](lib/ARCHITECTURE.md) | x |\n")
    assert doc_check.check(root)[0] == [
        "ARCHITECTURE.md: the map links lib/ARCHITECTURE.md, which does not exist",
        "ARCHITECTURE.md: the map does not link src/ARCHITECTURE.md",
    ]


def test_drift_exits_one_and_names_the_fix(tmp_path, capsys):
    root = repo(tmp_path, files=("main.c", "hal_uart.c", "retry.c"))
    assert doc_check.main(["--root", str(root)]) == 1
    assert "cdev-architecture-sync" in capsys.readouterr().out


def test_dot_folders_are_skipped_outside_git(tmp_path):
    root = repo(tmp_path)
    write(root, ".vscode/ARCHITECTURE.md", "# stray\n")
    assert doc_check.check(root)[0] == []


def test_default_root_is_the_repository_root():
    assert doc_check.DEFAULT_ROOT == TOOLS.parent


def test_ignored_build_output_is_skipped_in_git(tmp_path):
    import subprocess
    root = repo(tmp_path)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    write(root, ".gitignore", "*.o\n")
    write(root, "src/main.o")
    assert doc_check.check(root)[0] == []
    write(root, "src/new.c")
    assert doc_check.check(root)[0] == ["src/ARCHITECTURE.md: src/new.c is not listed"]


STUB_DOC = "# src\n\n## Files\n\nNot documented yet. Run cdev-architecture-sync for this folder.\n"


def test_a_folder_not_documented_yet_is_waiting_rather_than_drift(tmp_path):
    root = repo(tmp_path, folder_doc=STUB_DOC, files=("main.c", "extra.c"))
    assert doc_check.check(root) == ([], ["src"])


def test_the_waiting_folders_are_named_in_the_output(tmp_path, capsys):
    root = repo(tmp_path, folder_doc=STUB_DOC)
    assert doc_check.main(["--root", str(root)]) == 0
    out = capsys.readouterr().out
    assert "not documented yet: src" in out and "cdev-architecture-sync" in out


def test_map_links_with_spaces_or_dot_slash_count(tmp_path):
    root = tmp_path
    write(root, "my dir/ARCHITECTURE.md", "# my dir\n\n## Files\n\n- `a.c`: a\n")
    write(root, "my dir/a.c")
    write(root, "lib/ARCHITECTURE.md", "# lib\n\n## Files\n\n- `b.c`: b\n")
    write(root, "lib/b.c")
    write(root, "ARCHITECTURE.md", "## Map\n\n| [my dir](<my dir/ARCHITECTURE.md>) |\n| [lib](./lib/ARCHITECTURE.md) |\n")
    assert doc_check.check(root) == ([], [])
    write(root, "ARCHITECTURE.md", "## Map\n\n| [my dir](my%20dir/ARCHITECTURE.md) |\n| [lib](lib/ARCHITECTURE.md) |\n")
    assert doc_check.check(root) == ([], [])


def test_a_file_name_with_brackets_is_not_a_glob(tmp_path):
    root = repo(tmp_path, folder_doc="# src\n\n## Files\n\n- `foo[1].c`: one\n", files=("foo[1].c",))
    assert doc_check.check(root) == ([], [])


def test_a_byte_order_mark_and_trailing_spaces_are_tolerated(tmp_path):
    root = repo(tmp_path, folder_doc="# src\n\n## Files \n\n- `main.c`: entry\n", files=("main.c",))
    (root / "ARCHITECTURE.md").write_text(ROOT_DOC, encoding="utf-8-sig")
    assert doc_check.check(root) == ([], [])


def test_without_git_on_path_it_walks_the_tree(tmp_path, monkeypatch):
    root = repo(tmp_path)
    (root / ".git").mkdir()

    def missing(*args, **kwargs):
        raise FileNotFoundError("git")
    monkeypatch.setattr(doc_check.subprocess, "run", missing)
    assert doc_check.check(root) == ([], [])


def test_every_note_has_a_line_and_every_line_a_note(tmp_path):
    root = repo(tmp_path)
    write(root, "NOTES.md", "# Notes\n\n## Topics\n\n- [crg](docs/notes/crg.md): before running the review graph\n")
    write(root, "docs/notes/crg.md", "# crg\n")
    assert doc_check.check(root) == ([], [])
    write(root, "docs/notes/orphan.md", "# orphan\n")
    (root / "docs" / "notes" / "crg.md").unlink()
    problems, _ = doc_check.check(root)
    assert "NOTES.md: links docs/notes/crg.md, which does not exist" in problems
    assert "NOTES.md: docs/notes/orphan.md has no line" in problems


def test_notes_without_an_index_are_reported(tmp_path):
    root = repo(tmp_path)
    write(root, "docs/notes/crg.md", "# crg\n")
    problems, _ = doc_check.check(root)
    assert any("NOTES.md is missing" in problem for problem in problems)


def test_a_repository_without_notes_needs_no_index(tmp_path):
    assert doc_check.check(repo(tmp_path)) == ([], [])


def test_every_submodule_is_on_the_map_but_needs_no_document_of_ours(tmp_path):
    root = repo(tmp_path)
    write(root, ".gitmodules", '[submodule "ALG"]\n\tpath = ALG\n\turl = ../ALG.git\n[submodule "MPFW"]\n\tpath = fw/MPFW\n\turl = ../MPFW.git\n')
    problems, _ = doc_check.check(root)
    assert "ARCHITECTURE.md: the map does not mention the submodule ALG" in problems
    assert "ARCHITECTURE.md: the map does not mention the submodule fw/MPFW" in problems
    write(root, "ARCHITECTURE.md", ROOT_DOC + "| `ALG` | submodule: algorithm, edited here |\n| `fw/MPFW` | submodule: main firmware, read-only |\n")
    assert doc_check.check(root) == ([], [])


def git(cwd, *args):
    import subprocess
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "protocol.file.allow=always", *args],
                   cwd=cwd, check=True, capture_output=True)


def with_submodule(tmp_path):
    """A real superproject with ALG checked out as a submodule, the way a project repository looks."""
    alg = tmp_path / "alg_origin"
    write(alg, "src/filter.c")
    write(alg, "src/filter.h")
    git(alg, "init", "-q")
    git(alg, "add", "-A")
    git(alg, "commit", "-qm", "alg")
    root = repo(tmp_path / "proj")
    git(root, "init", "-q")
    git(root, "submodule", "add", "-q", str(alg), "ALG")
    return root


def test_a_submodule_worked_in_here_is_documented_inside_it_like_any_folder(tmp_path):
    root = with_submodule(tmp_path)
    write(root, "ALG/src/ARCHITECTURE.md", "# ALG/src\n\n## Files\n\n- `filter.c`: filter\n")
    write(root, "ARCHITECTURE.md", ROOT_DOC + "| [ALG/src](ALG/src/ARCHITECTURE.md) | submodule ALG, edited here |\n")
    problems, _ = doc_check.check(root)
    assert problems == ["ALG/src/ARCHITECTURE.md: ALG/src/filter.h is not listed"]


def test_a_submodule_only_used_here_needs_only_its_row(tmp_path):
    root = with_submodule(tmp_path)
    write(root, "ARCHITECTURE.md", ROOT_DOC + "| `ALG` | submodule, read-only here |\n")
    assert doc_check.check(root) == ([], [])
