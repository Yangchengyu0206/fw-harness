"""呼叫 git CLI。輸出一律以 UTF-8 解碼。"""
import subprocess
from pathlib import Path


class GitError(RuntimeError):
    pass


def _run(repo, args):
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True,
        text=True, encoding="utf-8", errors="replace",
    )


def git(repo, *args, check=True):
    result = _run(repo, args)
    if check and result.returncode != 0:
        raise GitError(
            f"git {' '.join(args)} 失敗（exit {result.returncode}）：{result.stderr.strip()}"
        )
    return result.stdout.strip()


def git_ok(repo, *args):
    return _run(repo, args).returncode == 0


def repo_root(start):
    return Path(git(start, "rev-parse", "--show-toplevel"))
