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
