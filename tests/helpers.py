import subprocess
from pathlib import Path


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
