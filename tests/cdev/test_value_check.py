"""value_check finds hardware values added without a source, which is how a guessed register gets caught."""
import subprocess
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[2] / "plugins" / "cdev" / "skills" / "cdev-init" / "templates" / "tools"
sys.path.insert(0, str(TOOLS))

import value_check  # noqa: E402

BASE = "#define HX_TP_I2C_ADDR 0x48u /* datasheet p.12 */\n"


def git(root, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=root, check=True,
                   capture_output=True)


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q")
    (tmp_path / "hx.h").write_text(BASE, encoding="utf-8")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "base")
    return tmp_path


def add(repo, text, name="hx.h"):
    path = repo / name
    path.write_text((path.read_text(encoding="utf-8") if path.exists() else "") + text, encoding="utf-8")


def test_a_guessed_register_is_reported(repo):
    add(repo, "#define HX_REG_REPORT_RATE    0x26u\n")
    assert value_check.unsourced(repo) == [("hx.h", 2, "HX_REG_REPORT_RATE", "0x26")]


@pytest.mark.parametrize("line", [
    "#define HX_REG_REPORT_RATE 0x26u /* UNVERIFIED: need the HX83102-J02 datasheet */\n",
    "/* HX83102-J02 datasheet, Table 7-3 */\n#define HX_REG_REPORT_RATE 0x26u\n",
    "#define HX_REG_REPORT_RATE 0x26u // AP note AN-102 p.4\n",
])
def test_a_value_that_names_its_source_or_says_unverified_passes(repo, line):
    add(repo, line)
    assert value_check.unsourced(repo) == []


def test_enum_members_count_but_statements_do_not(repo):
    add(repo, "enum { RATE_120 = 0x03, };\n", "rate.c")
    add(repo, "static void f(void) { mask = 0xFF; }\n", "rate.c")
    assert [name for _, _, name, _ in value_check.unsourced(repo)] == []
    add(repo, "enum rate {\n    RATE_60 = 0x02,\n};\n", "rate2.c")
    assert [name for _, _, name, _ in value_check.unsourced(repo)] == ["RATE_60"]


def test_committed_values_are_not_reported_again(repo):
    add(repo, "#define OLD 0x10\n")
    git(repo, "commit", "-qam", "old")
    assert value_check.unsourced(repo) == []


def test_exit_code_and_fix(repo, capsys):
    add(repo, "#define HX_REG_X 0x78u\n")
    assert value_check.main(["--root", str(repo)]) == 1
    out = capsys.readouterr().out
    assert "HX_REG_X = 0x78" in out and "UNVERIFIED" in out


def test_no_git_reports_nothing_rather_than_failing(tmp_path, monkeypatch):
    def missing(*args, **kwargs):
        raise FileNotFoundError("git")
    monkeypatch.setattr(value_check.subprocess, "run", missing)
    assert value_check.unsourced(tmp_path) == []


def test_values_added_inside_a_submodule_are_checked_too(repo, tmp_path):
    alg = tmp_path / "alg_origin"
    alg.mkdir()
    git(alg, "init", "-q")
    (alg / "alg.h").write_text("#define GAIN_REG 0x10 /* datasheet p.3 */\n", encoding="utf-8")
    git(alg, "add", "-A")
    git(alg, "commit", "-qm", "alg")
    git(repo, "-c", "protocol.file.allow=always", "submodule", "add", "-q", str(alg), "ALG")
    (repo / "ALG" / "alg.h").write_text("#define GAIN_REG 0x10 /* datasheet p.3 */\n#define NEW_REG 0x44\n",
                                        encoding="utf-8")
    assert value_check.unsourced(repo) == [("ALG/alg.h", 2, "NEW_REG", "0x44")]
