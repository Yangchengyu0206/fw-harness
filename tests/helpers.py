import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "plugins" / "fw-c-harness" / "skills" / "fw-harness-init" / "templates"
SCRIPTS = TEMPLATES / "harness" / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
PY = "{python}"


def git(cwd, *args):
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True,
        text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {result.stderr}")
    return result.stdout.strip()


def set_identity(path, name, email):
    git(path, "config", "user.name", name)
    git(path, "config", "user.email", email)
    git(path, "config", "commit.gpgsign", "false")
    git(path, "config", "core.autocrlf", "false")
    # Pin pull behaviour so a diverged pull always creates a merge commit
    git(path, "config", "pull.rebase", "false")
    git(path, "config", "pull.ff", "true")


def commit_all(repo, message):
    git(repo, "add", "-A")
    git(repo, "commit", "-m", message)
    return git(repo, "rev-parse", "HEAD")


def make_repo(path, name, email):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-b", "main")
    set_identity(path, name, email)
    tickets = path / "harness" / "tickets"
    tickets.mkdir(parents=True)
    (tickets / ".gitkeep").write_text("", encoding="utf-8")
    commit_all(path, "harness: init")
    return path


def add_origin(repo, tmp_path):
    origin = Path(tmp_path) / "origin.git"
    git(tmp_path, "clone", "--bare", str(repo), str(origin))
    git(repo, "remote", "add", "origin", str(origin))
    git(repo, "fetch", "origin")
    return origin


def make_fixture_repo(path, name="Alice Chen", email="alice@example.com"):
    repo = make_repo(path, name, email)
    shutil.copytree(FIXTURES / "sample-fw", repo, dirs_exist_ok=True)
    commit_all(repo, "harness: add sample firmware")
    return repo


def fake_config(**check_overrides):
    ok = [PY, "-c", "pass"]
    size = [PY, "-c", "print('   text    data     bss     dec     hex filename'); "
                      "print('   1000     100     200    1300     514 fw.elf')"]
    check = {
        "format": {"command": ok, "extensions": [".c", ".h"]},
        "cppcheck": {"command": ok, "paths": ["src"]},
        "build": {"commands": [ok]},
        "test": {"commands": [ok]},
        "size": {"command": size, "flash_budget": 4096, "ram_budget": 1024},
    }
    check.update(check_overrides)
    return {"language": "en", "required_tools": [], "check": check}


def write_config(repo, config):
    path = Path(repo) / "harness" / "config.json"
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    commit_all(repo, "harness: config")
