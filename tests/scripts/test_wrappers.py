import shutil
import subprocess
import sys

import pytest

from helpers import SCRIPTS, TEMPLATES, fake_config, git, make_fixture_repo, write_config


@pytest.fixture
def installed(tmp_path):
    repo = make_fixture_repo(tmp_path / "fw")
    shutil.copytree(SCRIPTS, repo / "harness" / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(TEMPLATES / ".githooks", repo / ".githooks")
    for name in ("Makefile", "init.sh", "init.ps1"):
        shutil.copy(TEMPLATES / name, repo / name)
    write_config(repo, fake_config())
    git(repo, "config", "core.hooksPath", ".githooks")
    return repo


def run(repo, argv):
    return subprocess.run(argv, cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace")


@pytest.mark.skipif(shutil.which("sh") is None, reason="needs a POSIX sh on PATH")
def test_init_sh(installed):
    result = run(installed, ["sh", "init.sh"])
    assert result.returncode == 0, result.stdout + result.stderr
    assert "check 7/7 passed" in result.stdout


@pytest.mark.skipif(shutil.which("pwsh") is None and shutil.which("powershell") is None,
                    reason="needs PowerShell")
def test_init_ps1(installed):
    shell = shutil.which("pwsh") or shutil.which("powershell")
    result = run(installed, [shell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "init.ps1"])
    assert result.returncode == 0, result.stdout + result.stderr
    assert "check 7/7 passed" in result.stdout


@pytest.mark.skipif(shutil.which("make") is None, reason="needs make")
def test_make_check(installed):
    result = run(installed, ["make", "check", f"PYTHON={sys.executable}"])
    assert result.returncode == 0, result.stdout + result.stderr
    assert "check 7/7 passed" in result.stdout
