# 計畫 1：身分、票與狀態腳本 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Language note (2026-09-15):** the project is open source and English-only (spec section 1, "Language and license"). This plan was written in Chinese before that decision. When executing, translate every comment, docstring, CLI/error message, and test string in the code blocks below into English, and update test assertions to match the English messages. No Chinese characters may remain in code or tests. Tasks 1 to 3 are already implemented this way; use `tickets.py` and `test_tickets.py` in the repo as the reference for message wording (for example the `"<label>: <message>"` prefix).

**Goal:** 實作 spec 第 5 節的狀態層：git 身分與 slug、一票一檔的票 schema、票號分配與 renumber、狀態機與 DoD 檢查、`ticket.py` CLI、`ticket_check`、`feature_list.json` 索引。

**Architecture:** 全部是 Python 標準庫腳本，放在 `fw-harness-init` skill 的範本目錄裡，之後由 init 複製到 FW repo 的 `harness/scripts/`。每個模組只負責一件事（IO、git、身分、票、票號、狀態機、檢查、索引），`ticket.py` 只是組合它們的 CLI。測試用 pytest，在暫存目錄建立真實 git repo（含 bare origin 和兩個身分的 clone）。

**Tech Stack:** Python 3 標準庫、git CLI、pytest（只在開發 plugin 時需要）

**Spec:** `docs/superpowers/specs/2026-09-15-fw-c-harness-plugin-design.md`

**整體拆分（本計畫是 1/4）：**
1. 身分、票與狀態腳本（本計畫）
2. 驗證閘門：`check.py`、`init` 驗證、`arch_check`、棘輪、size 預算、git hooks、`sample-fw` fixture
3. `fw-harness-init` / `fw-harness-upgrade` / `fw-architecture-sync`：範本、ARCHITECTURE.md 產生、既有檔案處理
4. 其餘 9 個 skills 內文、兩份 marketplace manifest、README、人工檢查清單

## Global Constraints

- 所有 skill 內文與使用者訊息使用繁體中文。
- 讀寫一律 UTF-8；Windows 下不依賴 `cp950`。
- 所有腳本：失敗時非 0 結束，訊息寫明「哪個檢查、哪個檔案、怎麼修」。
- 寫入票檔採「讀取 → 修改 → 寫入暫存檔 → rename」。
- 離線時（`git fetch` 失敗）：票號分配改用本地資料並明確警告，不靜默略過。
- 身分來源：`git config user.name` 與 `user.email`，不另外設帳號系統；skill 不能自行指定別人的身分。
- slug：取 email 的 local-part；若含 `+`，取 `+` 之後的部分；轉小寫，非 `[a-z0-9-]` 的字元換成 `-`；可以用 `harness/people.json` 覆寫。
- 票號格式 `FW-NNNN`，新票號為 `max(本地 tickets, origin/main tickets) + 1`。
- commit 類 evidence 不寫入票檔，由 git log 動態算出；票檔只存 `check`、`hil`、`review`。
- `feature_list.json` 由腳本產生並 gitignored。
- 計畫決定（spec 未指定）：腳本只用標準庫，支援 Python 3.9 以上；Windows 上以 `py -3` 執行。
- 票檔含布林欄位 `requires_hil`（預設 true）；`requires_hil` 為 true 時轉 `done` 需要 `kind: hil` evidence。
- `kind: check` evidence 含布林欄位 `passed`；只有 `passed: true` 的 check 能讓票轉 `verifying`。
- `ticket.py move <票號> done` 在 DoD 檢查通過後，還要求 stdin 是 TTY 並輸入票號確認（agent 的 shell 通常不是 TTY，因此無法自行標記 done）。

## 檔案結構

以下 `SCRIPTS` 代表 `plugins/fw-c-harness/skills/fw-harness-init/templates/harness/scripts`。

| 檔案 | 職責 |
|---|---|
| `SCRIPTS/jsonio.py` | UTF-8 JSON 讀取、原子寫入 |
| `SCRIPTS/gitutil.py` | 呼叫 git（UTF-8、錯誤訊息） |
| `SCRIPTS/identity.py` | 取得目前身分、計算 slug |
| `SCRIPTS/tickets.py` | 票的路徑、讀寫、schema 驗證、建立新票、建立 evidence |
| `SCRIPTS/allocate.py` | 票號分配、`renumber` |
| `SCRIPTS/transitions.py` | 狀態機與 DoD 條件 |
| `SCRIPTS/ticket_check.py` | `check` 第 4 步用的全域票檢查（可獨立執行） |
| `SCRIPTS/index.py` | 產生 `feature_list.json` |
| `SCRIPTS/ticket.py` | CLI：new / claim / move / block / unblock / evidence / dod / collisions / renumber / show |
| `pytest.ini` | pytest 設定 |
| `.gitignore` | 忽略 `__pycache__`、`.pytest_cache` |
| `tests/conftest.py` | 把 `SCRIPTS` 加進 `sys.path`；`repo`、`team` fixture |
| `tests/helpers.py` | 測試用 `git()`、`make_repo()`、`commit_all()` |
| `tests/scripts/test_*.py` | 各模組單元測試與兩人協作整合測試 |

所有測試指令都在 `C:\Users\YANG\Desktop\fw-harness` 執行。

---

### Task 1：專案骨架、`jsonio`、`gitutil`

**Files:**
- Create: `pytest.ini`
- Create: `.gitignore`
- Create: `tests/helpers.py`
- Create: `tests/conftest.py`
- Create: `SCRIPTS/jsonio.py`
- Create: `SCRIPTS/gitutil.py`
- Test: `tests/scripts/test_jsonio.py`
- Test: `tests/scripts/test_gitutil.py`

**Interfaces:**
- Produces:
  - `jsonio.read_json(path) -> Any`
  - `jsonio.write_json_atomic(path, data) -> None`（縮排 2、`ensure_ascii=False`、LF、結尾換行、自動建立父目錄）
  - `gitutil.GitError(RuntimeError)`
  - `gitutil.git(repo, *args, check=True) -> str`（回傳去除頭尾空白的 stdout）
  - `gitutil.git_ok(repo, *args) -> bool`
  - `gitutil.repo_root(start) -> pathlib.Path`
  - 測試：`helpers.git(cwd, *args) -> str`、`helpers.make_repo(path, name, email) -> Path`、`helpers.commit_all(repo, message) -> str`（回傳 commit hash）
  - fixture `repo`（單人 repo，身分 Alice Chen / alice@example.com）、fixture `team`（回傳 `(origin_path, {"alice": Path, "bob": Path})`）

- [ ] **Step 1：建立 pytest 設定與測試輔助**

`pytest.ini`：

```ini
[pytest]
testpaths = tests
addopts = -q
```

`.gitignore`：

```gitignore
__pycache__/
.pytest_cache/
```

`tests/helpers.py`：

```python
import subprocess
from pathlib import Path


def git(cwd, *args):
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True,
        text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} 失敗：{result.stderr}")
    return result.stdout.strip()


def set_identity(path, name, email):
    git(path, "config", "user.name", name)
    git(path, "config", "user.email", email)
    git(path, "config", "commit.gpgsign", "false")
    git(path, "config", "core.autocrlf", "false")
    # 蓋掉使用者全域的 pull 設定，讓分叉時的 pull 一律產生 merge commit
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
```

`tests/conftest.py`：

```python
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins" / "fw-c-harness" / "skills" / "fw-harness-init" / "templates" / "harness" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from helpers import git, make_repo, set_identity  # noqa: E402


@pytest.fixture
def repo(tmp_path):
    return make_repo(tmp_path / "fw", "Alice Chen", "alice@example.com")


@pytest.fixture
def team(tmp_path):
    seed = make_repo(tmp_path / "seed", "Seed", "seed@example.com")
    origin = tmp_path / "origin.git"
    git(tmp_path, "clone", "--bare", str(seed), str(origin))
    clones = {}
    for slug, name in [("alice", "Alice Chen"), ("bob", "Bob Lin")]:
        path = tmp_path / slug
        git(tmp_path, "clone", str(origin), str(path))
        set_identity(path, name, f"{slug}@example.com")
        clones[slug] = path
    return origin, clones
```

- [ ] **Step 2：寫 `jsonio` 的失敗測試**

`tests/scripts/test_jsonio.py`：

```python
import pytest

from jsonio import read_json, write_json_atomic


def test_roundtrip_keeps_chinese_as_utf8(tmp_path):
    path = tmp_path / "sub" / "t.json"
    write_json_atomic(path, {"title": "UART 驅動"})
    raw = path.read_bytes()
    assert "UART 驅動".encode("utf-8") in raw
    assert b"\r\n" not in raw
    assert raw.endswith(b"\n")
    assert read_json(path) == {"title": "UART 驅動"}


def test_failed_write_keeps_original_and_leaves_no_temp(tmp_path):
    path = tmp_path / "t.json"
    write_json_atomic(path, {"a": 1})
    with pytest.raises(TypeError):
        write_json_atomic(path, {"a": {1, 2}})
    assert read_json(path) == {"a": 1}
    assert [p.name for p in tmp_path.iterdir()] == ["t.json"]
```

- [ ] **Step 3：執行並確認失敗**

Run: `py -3 -m pytest tests/scripts/test_jsonio.py`
Expected: FAIL，`ModuleNotFoundError: No module named 'jsonio'`

- [ ] **Step 4：實作 `jsonio`**

`SCRIPTS/jsonio.py`：

```python
"""UTF-8 JSON 讀寫。寫入採暫存檔 + rename，避免寫到一半損毀。"""
import json
import os
import tempfile
from pathlib import Path


def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json_atomic(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
```

- [ ] **Step 5：執行並確認通過**

Run: `py -3 -m pytest tests/scripts/test_jsonio.py`
Expected: `2 passed`

- [ ] **Step 6：寫 `gitutil` 的失敗測試**

`tests/scripts/test_gitutil.py`：

```python
import pytest

from gitutil import GitError, git, git_ok, repo_root


def test_git_returns_stripped_stdout(repo):
    assert git(repo, "log", "-1", "--format=%s") == "harness: init"


def test_git_raises_with_command_and_stderr(repo):
    with pytest.raises(GitError) as exc:
        git(repo, "rev-parse", "no-such-ref")
    assert "git rev-parse no-such-ref" in str(exc.value)


def test_git_check_false_does_not_raise(repo):
    assert git(repo, "config", "no.such-key", check=False) == ""


def test_git_ok(repo):
    assert git_ok(repo, "rev-parse", "HEAD")
    assert not git_ok(repo, "rev-parse", "no-such-ref")


def test_repo_root_from_subdir(repo):
    assert repo_root(repo / "harness" / "tickets").resolve() == repo.resolve()
```

- [ ] **Step 7：執行並確認失敗**

Run: `py -3 -m pytest tests/scripts/test_gitutil.py`
Expected: FAIL，`ModuleNotFoundError: No module named 'gitutil'`

- [ ] **Step 8：實作 `gitutil`**

`SCRIPTS/gitutil.py`：

```python
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
```

- [ ] **Step 9：執行全部測試並確認通過**

Run: `py -3 -m pytest`
Expected: `7 passed`

- [ ] **Step 10：Commit**

```bash
git add pytest.ini .gitignore tests plugins
git commit -m "feat(scripts): 新增 jsonio、gitutil 與測試骨架"
```

### Task 2：`identity`（身分與 slug）

**Files:**
- Create: `SCRIPTS/identity.py`
- Test: `tests/scripts/test_identity.py`

**Interfaces:**
- Consumes: `gitutil.git`、`jsonio.read_json`
- Produces:
  - `identity.IdentityError(RuntimeError)`
  - `identity.slugify_email(email: str) -> str`
  - `identity.current_identity(repo) -> {"name": str, "email": str}`
  - `identity.slug_for(repo, email: str) -> str`（先查 `harness/people.json`，找不到才用 `slugify_email`）
  - `harness/people.json` 格式：`{"<email，小寫>": {"slug": "alice", "display_name": "Alice Chen"}}`，key 比對不分大小寫

- [ ] **Step 1：寫失敗測試**

`tests/scripts/test_identity.py`：

```python
import pytest

from identity import IdentityError, current_identity, slug_for, slugify_email
from jsonio import write_json_atomic


@pytest.mark.parametrize("email, slug", [
    ("alice@example.com", "alice"),
    ("Alice.Chen@example.com", "alice-chen"),
    ("team+bob_lin@example.com", "bob-lin"),
    ("x-y9@example.com", "x-y9"),
])
def test_slugify_email(email, slug):
    assert slugify_email(email) == slug


def test_current_identity_reads_git_config(repo):
    assert current_identity(repo) == {"name": "Alice Chen", "email": "alice@example.com"}


def test_current_identity_fails_with_fix_hint(repo, tmp_path, monkeypatch):
    from helpers import git
    git(repo, "config", "--unset", "user.email")
    empty = tmp_path / "empty-gitconfig"
    empty.write_text("", encoding="utf-8")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(empty))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    with pytest.raises(IdentityError) as exc:
        current_identity(repo)
    assert "git config user.email" in str(exc.value)


def test_slug_for_uses_people_json_case_insensitive(repo):
    write_json_atomic(repo / "harness" / "people.json",
                      {"alice@example.com": {"slug": "achen", "display_name": "Alice"}})
    assert slug_for(repo, "ALICE@example.com") == "achen"
    assert slug_for(repo, "bob@example.com") == "bob"


def test_slug_for_without_people_json(repo):
    assert slug_for(repo, "team+Bob@example.com") == "bob"
```

- [ ] **Step 2：執行並確認失敗**

Run: `py -3 -m pytest tests/scripts/test_identity.py`
Expected: FAIL，`ModuleNotFoundError: No module named 'identity'`

- [ ] **Step 3：實作**

`SCRIPTS/identity.py`：

```python
"""身分：來源只有 git config user.name / user.email。"""
import re
from pathlib import Path

from gitutil import git
from jsonio import read_json


class IdentityError(RuntimeError):
    pass


def slugify_email(email):
    local = email.split("@", 1)[0]
    if "+" in local:
        local = local.split("+", 1)[1]
    return re.sub(r"[^a-z0-9-]", "-", local.lower())


def current_identity(repo):
    name = git(repo, "config", "user.name", check=False)
    email = git(repo, "config", "user.email", check=False)
    missing = [key for key, value in (("user.name", name), ("user.email", email)) if not value]
    if missing:
        raise IdentityError(
            f"身分檢查失敗：git config {'、'.join(missing)} 未設定。"
            '修法：git config user.name "你的名字"；git config user.email you@company.com'
        )
    return {"name": name, "email": email}


def slug_for(repo, email):
    people_path = Path(repo) / "harness" / "people.json"
    if people_path.exists():
        people = {key.lower(): value for key, value in read_json(people_path).items()}
        entry = people.get(email.lower())
        if entry and entry.get("slug"):
            return entry["slug"]
    return slugify_email(email)
```

- [ ] **Step 4：執行並確認通過**

Run: `py -3 -m pytest tests/scripts/test_identity.py`
Expected: `8 passed`

- [ ] **Step 5：Commit**

```bash
git add plugins tests
git commit -m "feat(scripts): 新增 identity 身分與 slug 計算"
```

### Task 3：`tickets`（票檔讀寫、schema、建立票與 evidence）

**Files:**
- Create: `SCRIPTS/tickets.py`
- Test: `tests/scripts/test_tickets.py`

**Interfaces:**
- Consumes: `jsonio.read_json`、`jsonio.write_json_atomic`
- Produces:
  - 常數：`TICKET_ID_RE`、`STATUSES = ("backlog", "next", "active", "verifying", "done", "blocked")`、`EVIDENCE_KINDS = ("check", "hil", "review")`、`EVIDENCE_FIELDS = {"check": ("commit", "summary", "passed"), "hil": ("ref",), "review": ("ref", "open_critical")}`
  - `tickets_dir(repo) -> Path`、`ticket_path(repo, ticket_id) -> Path`
  - `format_id(number: int) -> str`（`7 -> "FW-0007"`）、`parse_id(ticket_id: str) -> int`（格式錯誤丟 `ValueError`）
  - `now_iso() -> str`（本地時區、到秒，例如 `2026-09-15T10:02:00+08:00`）
  - `load_ticket(repo, ticket_id) -> dict`（找不到丟 `FileNotFoundError`）
  - `load_all(repo) -> list[tuple[Path, dict]]`（依檔名排序，只讀 `FW-*.json`）
  - `save_ticket(repo, ticket) -> None`（寫到 `ticket_path(repo, ticket["id"])`）
  - `validate_ticket(ticket, filename=None) -> list[str]`（每條錯誤以 `"<檔名或票號>："` 開頭；空 list 表示合法）
  - `new_ticket(ticket_id, title, area, by, now, priority=3, user_visible_behavior="", verification_steps=(), dod_pending=(), requires_hil=True) -> dict`（`status="backlog"`、`assignee=None`，history 一筆 `from=None → backlog`）
  - `make_evidence(kind, by, now, **fields) -> dict`（缺欄位丟 `ValueError`）

- [ ] **Step 1：寫失敗測試**

`tests/scripts/test_tickets.py`：

```python
import re

import pytest

from tickets import (
    format_id, load_all, load_ticket, make_evidence, new_ticket, now_iso,
    parse_id, save_ticket, ticket_path, validate_ticket,
)

ALICE = {"name": "Alice Chen", "email": "alice@example.com"}
NOW = "2026-09-15T10:02:00+08:00"


def sample(ticket_id="FW-0042", **overrides):
    ticket = new_ticket(ticket_id, "UART 驅動支援 DMA 接收", "drivers/uart", ALICE, NOW,
                        priority=2, user_visible_behavior="連續接收 4KB 不掉 byte",
                        verification_steps=["host 測試", "上板：loopback 4KB"],
                        dod_pending=["上板 loopback 驗證"])
    ticket.update(overrides)
    return ticket


def test_id_helpers():
    assert format_id(7) == "FW-0007"
    assert format_id(12345) == "FW-12345"
    assert parse_id("FW-0042") == 42
    with pytest.raises(ValueError):
        parse_id("FW-42")


def test_now_iso_has_offset_and_seconds():
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d[+-]\d\d:\d\d", now_iso())


def test_new_ticket_is_valid_backlog():
    ticket = sample()
    assert validate_ticket(ticket, "FW-0042.json") == []
    assert ticket["status"] == "backlog"
    assert ticket["assignee"] is None
    assert ticket["evidence"] == []
    assert ticket["history"] == [{"by": ALICE, "at": NOW, "from": None, "to": "backlog", "note": "開票"}]


def test_filename_must_match_id():
    errors = validate_ticket(sample(), "FW-0043.json")
    assert any("與檔名" in e for e in errors)


@pytest.mark.parametrize("overrides, fragment", [
    ({"id": "FW-42"}, "id 必須是 FW-NNNN"),
    ({"status": "doing"}, "status 必須是"),
    ({"priority": "high"}, "priority"),
    ({"requires_hil": "yes"}, "requires_hil"),
    ({"status": "blocked"}, "blocked_reason"),
    ({"status": "active"}, "必須有 assignee"),
    ({"dod_pending": "上板"}, "dod_pending"),
    ({"evidence": [{"kind": "commit", "by": ALICE, "at": NOW}]}, "由 git log 動態計算"),
    ({"evidence": [{"kind": "review", "by": ALICE, "at": NOW, "ref": "r.md"}]}, "open_critical"),
    ({"evidence": [{"kind": "check", "by": ALICE, "at": NOW, "commit": "abc1234", "summary": "s", "passed": "yes"}]}, "passed"),
    ({"history": [{"by": ALICE, "at": NOW, "to": "nowhere"}]}, "history[0]"),
])
def test_validation_errors(overrides, fragment):
    errors = validate_ticket(sample(**overrides))
    assert any(fragment in e for e in errors), errors


def test_errors_are_prefixed_with_label():
    errors = validate_ticket(sample(status="doing"), "FW-0042.json")
    assert errors and all(e.startswith("FW-0042.json：") for e in errors)


def test_save_load_roundtrip_and_load_all_sorted(repo):
    save_ticket(repo, sample("FW-0002"))
    save_ticket(repo, sample("FW-0001"))
    assert ticket_path(repo, "FW-0001").exists()
    assert load_ticket(repo, "FW-0002")["id"] == "FW-0002"
    assert [t["id"] for _, t in load_all(repo)] == ["FW-0001", "FW-0002"]


def test_load_ticket_missing(repo):
    with pytest.raises(FileNotFoundError):
        load_ticket(repo, "FW-0099")


def test_make_evidence():
    ev = make_evidence("review", ALICE, NOW, ref="harness/reviews/x.md", open_critical=0)
    assert ev == {"kind": "review", "by": ALICE, "at": NOW, "ref": "harness/reviews/x.md", "open_critical": 0}
    failed = make_evidence("check", ALICE, NOW, commit="abc1234", summary="check 5/7", passed=False)
    assert failed["passed"] is False
    with pytest.raises(ValueError):
        make_evidence("check", ALICE, NOW, commit="abc1234", summary="check 7/7 通過")
    with pytest.raises(ValueError):
        make_evidence("check", ALICE, NOW, commit="abc")
    with pytest.raises(ValueError):
        make_evidence("commit", ALICE, NOW)
```

- [ ] **Step 2：執行並確認失敗**

Run: `py -3 -m pytest tests/scripts/test_tickets.py`
Expected: FAIL，`ModuleNotFoundError: No module named 'tickets'`

- [ ] **Step 3：實作**

`SCRIPTS/tickets.py`：

```python
"""票檔：一票一檔 harness/tickets/FW-NNNN.json。"""
import re
from datetime import datetime
from pathlib import Path

from jsonio import read_json, write_json_atomic

TICKET_ID_RE = re.compile(r"^FW-(\d{4,})$")
STATUSES = ("backlog", "next", "active", "verifying", "done", "blocked")
EVIDENCE_KINDS = ("check", "hil", "review")
EVIDENCE_FIELDS = {"check": ("commit", "summary", "passed"), "hil": ("ref",), "review": ("ref", "open_critical")}
ASSIGNED_STATUSES = ("active", "verifying", "done")


def tickets_dir(repo):
    return Path(repo) / "harness" / "tickets"


def ticket_path(repo, ticket_id):
    return tickets_dir(repo) / f"{ticket_id}.json"


def format_id(number):
    return f"FW-{number:04d}"


def parse_id(ticket_id):
    match = TICKET_ID_RE.match(ticket_id)
    if not match:
        raise ValueError(f"票號格式錯誤：{ticket_id!r}，應為 FW-NNNN")
    return int(match.group(1))


def now_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def load_ticket(repo, ticket_id):
    path = ticket_path(repo, ticket_id)
    if not path.exists():
        raise FileNotFoundError(f"找不到票 {ticket_id}：{path}")
    return read_json(path)


def load_all(repo):
    directory = tickets_dir(repo)
    if not directory.exists():
        return []
    return [(path, read_json(path)) for path in sorted(directory.glob("FW-*.json"))]


def save_ticket(repo, ticket):
    write_json_atomic(ticket_path(repo, ticket["id"]), ticket)


def _is_person(value):
    return (isinstance(value, dict) and isinstance(value.get("name"), str)
            and isinstance(value.get("email"), str) and bool(value["email"]))


def _is_str_list(value):
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _is_count(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def validate_ticket(ticket, filename=None):
    if not isinstance(ticket, dict):
        return [f"{filename or '<票>'}：票檔內容必須是 JSON 物件"]
    label = Path(filename).name if filename else (ticket.get("id") or "<票>")
    errors = []

    def err(message):
        errors.append(f"{label}：{message}")

    ticket_id = ticket.get("id")
    if not isinstance(ticket_id, str) or not TICKET_ID_RE.match(ticket_id):
        err("id 必須是 FW-NNNN 格式")
    elif filename is not None and Path(filename).stem != ticket_id:
        err(f"id {ticket_id} 與檔名 {Path(filename).name} 不一致。修法：改檔名，或執行 ticket.py renumber")

    for key in ("title", "area", "created_at", "user_visible_behavior", "notes"):
        if not isinstance(ticket.get(key), str):
            err(f"{key} 必須是字串")

    status = ticket.get("status")
    if status not in STATUSES:
        err(f"status 必須是 {'/'.join(STATUSES)} 之一")
    if not _is_count(ticket.get("priority")):
        err("priority 必須是非負整數")
    if not isinstance(ticket.get("requires_hil"), bool):
        err("requires_hil 必須是 true 或 false")
    if not _is_person(ticket.get("created_by")):
        err("created_by 必須含 name 與 email")
    assignee = ticket.get("assignee")
    if assignee is not None and not _is_person(assignee):
        err("assignee 必須是 null 或含 name 與 email")
    if status in ASSIGNED_STATUSES and assignee is None:
        err(f"status 為 {status} 時必須有 assignee")

    for key in ("verification_steps", "dod_pending"):
        if not _is_str_list(ticket.get(key)):
            err(f"{key} 必須是字串陣列")

    reason = ticket.get("blocked_reason")
    if reason is not None and not isinstance(reason, str):
        err("blocked_reason 必須是 null 或字串")
    if status == "blocked" and not (isinstance(reason, str) and reason.strip()):
        err("blocked 的票必須填 blocked_reason。修法：ticket.py block <票號> --reason \"原因\"")

    evidence = ticket.get("evidence")
    if not isinstance(evidence, list):
        err("evidence 必須是陣列")
    else:
        for index, item in enumerate(evidence):
            where = f"evidence[{index}]"
            if not isinstance(item, dict) or item.get("kind") not in EVIDENCE_KINDS:
                err(f"{where}.kind 必須是 check/hil/review 之一（commit 類 evidence 由 git log 動態計算，不寫入票檔）")
                continue
            if not _is_person(item.get("by")) or not isinstance(item.get("at"), str):
                err(f"{where} 必須含 by 與 at")
            for field in EVIDENCE_FIELDS[item["kind"]]:
                if field == "open_critical":
                    if not _is_count(item.get(field)):
                        err(f"{where}.open_critical 必須是非負整數")
                elif field == "passed":
                    if not isinstance(item.get(field), bool):
                        err(f"{where}.passed 必須是 true 或 false")
                elif not (isinstance(item.get(field), str) and item[field]):
                    err(f"{where}.{field} 必須是非空字串")

    history = ticket.get("history")
    if not isinstance(history, list):
        err("history 必須是陣列")
    else:
        for index, item in enumerate(history):
            if (not isinstance(item, dict) or not _is_person(item.get("by"))
                    or not isinstance(item.get("at"), str) or item.get("to") not in STATUSES
                    or (item.get("from") is not None and item.get("from") not in STATUSES)):
                err(f"history[{index}] 必須含 by、at、from（null 或狀態）、to（狀態）")
    return errors


def new_ticket(ticket_id, title, area, by, now, priority=3, user_visible_behavior="",
               verification_steps=(), dod_pending=(), requires_hil=True):
    return {
        "id": ticket_id,
        "title": title,
        "area": area,
        "status": "backlog",
        "priority": priority,
        "requires_hil": requires_hil,
        "created_by": dict(by),
        "created_at": now,
        "assignee": None,
        "user_visible_behavior": user_visible_behavior,
        "verification_steps": list(verification_steps),
        "dod_pending": list(dod_pending),
        "evidence": [],
        "history": [{"by": dict(by), "at": now, "from": None, "to": "backlog", "note": "開票"}],
        "blocked_reason": None,
        "notes": "",
    }


def make_evidence(kind, by, now, **fields):
    if kind not in EVIDENCE_KINDS:
        raise ValueError(f"evidence kind 必須是 check/hil/review 之一，收到 {kind!r}")
    missing = [field for field in EVIDENCE_FIELDS[kind] if fields.get(field) in (None, "")]
    if missing:
        raise ValueError(f"{kind} evidence 缺少 {'、'.join(missing)}")
    return {"kind": kind, "by": dict(by), "at": now, **fields}
```

- [ ] **Step 4：執行並確認通過**

Run: `py -3 -m pytest tests/scripts/test_tickets.py`
Expected: `19 passed`

- [ ] **Step 5：Commit**

```bash
git add plugins tests
git commit -m "feat(scripts): 新增 tickets 票檔 schema 與讀寫"
```

### Task 4：`allocate`（票號分配與 renumber）

**Files:**
- Create: `SCRIPTS/allocate.py`
- Test: `tests/scripts/test_allocate.py`

**Interfaces:**
- Consumes: `gitutil.git`、`gitutil.git_ok`；`tickets.TICKET_ID_RE`、`format_id`、`parse_id`、`load_ticket`、`save_ticket`、`ticket_path`、`tickets_dir`、`new_ticket`（測試用）
- Produces:
  - `allocate.OFFLINE_WARNING: str`
  - `allocate.RenumberError(RuntimeError)`
  - `allocate.local_ids(repo) -> set[int]`
  - `allocate.remote_ids(repo, warn=<印到 stderr>) -> set[int] | None`（先 `git fetch origin main`，失敗就呼叫 `warn(OFFLINE_WARNING)` 並回傳 `None`）
  - `allocate.next_ticket_id(repo, warn=...) -> str`
  - `allocate.renumber(repo, ticket_id, by, now, warn=...) -> str`（回傳新票號；刪除舊檔、寫入新檔、history 加一筆 note；不動 git index）
  - `allocate.commits_mentioning(repo, ticket_id) -> list[str]`（`origin/main..HEAD` 中訊息含票號的 commit，每行 `"<短 hash> <subject>"`）
  - `allocate.find_collisions(repo, warn=...) -> list[str]`（合併前預檢：本地與 `origin/main` 同號但不是同一張票的票號，依號碼排序；離線時呼叫 `warn(OFFLINE_WARNING)` 並回傳 `[]`）
- 「後進者」判定：本地票與 `origin/main` 上同號票的 `created_by.email` 或 `created_at` 不同，就代表是兩張不同的票，本地這張改號。

- [ ] **Step 1：寫失敗測試**

`tests/scripts/test_allocate.py`：

```python
import pytest

from allocate import (
    OFFLINE_WARNING, RenumberError, commits_mentioning, find_collisions, next_ticket_id, renumber,
)
from helpers import commit_all, git
from tickets import load_ticket, new_ticket, save_ticket, ticket_path

ALICE = {"name": "Alice Chen", "email": "alice@example.com"}
BOB = {"name": "Bob Lin", "email": "bob@example.com"}


def open_ticket(repo, who, now, title="t"):
    ticket_id = next_ticket_id(repo, warn=lambda m: None)
    save_ticket(repo, new_ticket(ticket_id, title, "drivers/uart", who, now))
    commit_all(repo, f"{ticket_id} 開票")
    return ticket_id


def test_offline_uses_local_and_warns(repo):
    warnings = []
    assert next_ticket_id(repo, warn=warnings.append) == "FW-0001"
    assert warnings == [OFFLINE_WARNING]


def test_local_max_plus_one(repo):
    save_ticket(repo, new_ticket("FW-0003", "t", "a", ALICE, "2026-09-15T10:00:00+08:00"))
    assert next_ticket_id(repo, warn=lambda m: None) == "FW-0004"


def test_remote_max_plus_one(team):
    _, clones = team
    bob = clones["bob"]
    save_ticket(bob, new_ticket("FW-0005", "t", "a", BOB, "2026-09-15T10:00:00+08:00"))
    commit_all(bob, "FW-0005 開票")
    git(bob, "push", "origin", "main")
    warnings = []
    assert next_ticket_id(clones["alice"], warn=warnings.append) == "FW-0006"
    assert warnings == []


def collide(team):
    _, clones = team
    alice, bob = clones["alice"], clones["bob"]
    assert open_ticket(alice, ALICE, "2026-09-15T10:00:00+08:00", "alice 的票") == "FW-0001"
    assert open_ticket(bob, BOB, "2026-09-15T10:00:05+08:00", "bob 的票") == "FW-0001"
    git(bob, "push", "origin", "main")
    return alice, bob


def test_renumber_later_ticket_and_merge_cleanly(team):
    alice, _ = collide(team)
    new_id = renumber(alice, "FW-0001", ALICE, "2026-09-15T10:05:00+08:00", warn=lambda m: None)
    assert new_id == "FW-0002"
    assert not ticket_path(alice, "FW-0001").exists()
    moved = load_ticket(alice, "FW-0002")
    assert moved["id"] == "FW-0002" and moved["title"] == "alice 的票"
    assert moved["history"][-1]["note"] == "renumber：FW-0001 → FW-0002"
    assert commits_mentioning(alice, "FW-0001")[0].endswith("FW-0001 開票")
    commit_all(alice, "harness: renumber FW-0001 → FW-0002")
    git(alice, "merge", "--no-edit", "origin/main")
    assert load_ticket(alice, "FW-0001")["title"] == "bob 的票"
    assert load_ticket(alice, "FW-0002")["title"] == "alice 的票"


def test_find_collisions_before_and_after_renumber(team):
    alice, _ = collide(team)
    assert find_collisions(alice, warn=lambda m: None) == ["FW-0001"]
    renumber(alice, "FW-0001", ALICE, "2026-09-15T10:05:00+08:00", warn=lambda m: None)
    commit_all(alice, "harness: renumber FW-0001 → FW-0002")
    git(alice, "merge", "--no-edit", "origin/main")
    assert find_collisions(alice, warn=lambda m: None) == []


def test_find_collisions_offline_warns(repo):
    open_ticket(repo, ALICE, "2026-09-15T10:00:00+08:00")
    warnings = []
    assert find_collisions(repo, warn=warnings.append) == []
    assert warnings == [OFFLINE_WARNING]


def test_renumber_refuses_when_not_on_main(team):
    _, clones = team
    open_ticket(clones["alice"], ALICE, "2026-09-15T10:00:00+08:00")
    with pytest.raises(RenumberError, match="不在 origin/main"):
        renumber(clones["alice"], "FW-0001", ALICE, "now", warn=lambda m: None)


def test_renumber_refuses_same_ticket(team):
    _, clones = team
    open_ticket(clones["bob"], BOB, "2026-09-15T10:00:00+08:00")
    git(clones["bob"], "push", "origin", "main")
    git(clones["alice"], "pull", "--no-edit", "origin", "main")
    with pytest.raises(RenumberError, match="同一張票"):
        renumber(clones["alice"], "FW-0001", ALICE, "now", warn=lambda m: None)


def test_renumber_refuses_offline(repo):
    open_ticket(repo, ALICE, "2026-09-15T10:00:00+08:00")
    with pytest.raises(RenumberError, match="origin/main"):
        renumber(repo, "FW-0001", ALICE, "now", warn=lambda m: None)
```

- [ ] **Step 2：執行並確認失敗**

Run: `py -3 -m pytest tests/scripts/test_allocate.py`
Expected: FAIL，`ModuleNotFoundError: No module named 'allocate'`

- [ ] **Step 3：實作**

`SCRIPTS/allocate.py`：

```python
"""票號分配與 renumber。票號只有在開票 commit 合入 main 之後才算佔住。"""
import json
import sys
from pathlib import Path

from gitutil import git, git_ok
from tickets import TICKET_ID_RE, format_id, load_ticket, parse_id, save_ticket, ticket_path, tickets_dir

OFFLINE_WARNING = "警告：無法 git fetch origin main（離線或沒有 origin），票號只依本地計算，合併時可能撞號。"


class RenumberError(RuntimeError):
    pass


def _warn_stderr(message):
    print(message, file=sys.stderr)


def local_ids(repo):
    directory = tickets_dir(repo)
    if not directory.exists():
        return set()
    return {parse_id(path.stem) for path in directory.glob("FW-*.json") if TICKET_ID_RE.match(path.stem)}


def remote_ids(repo, warn=_warn_stderr):
    if not git_ok(repo, "fetch", "origin", "main"):
        warn(OFFLINE_WARNING)
        return None
    listing = git(repo, "ls-tree", "--name-only", "origin/main", "harness/tickets/")
    ids = set()
    for line in listing.splitlines():
        path = Path(line)
        if path.suffix == ".json" and TICKET_ID_RE.match(path.stem):
            ids.add(parse_id(path.stem))
    return ids


def next_ticket_id(repo, warn=_warn_stderr):
    remote = remote_ids(repo, warn) or set()
    return format_id(max(local_ids(repo) | remote | {0}) + 1)


def _same_ticket(a, b):
    return (a.get("created_at") == b.get("created_at")
            and (a.get("created_by") or {}).get("email") == (b.get("created_by") or {}).get("email"))


def renumber(repo, ticket_id, by, now, warn=_warn_stderr):
    remote = remote_ids(repo, warn)
    if remote is None:
        raise RenumberError("renumber 需要 origin/main 才能判斷誰是後進者。修法：確認網路與 origin 設定後重試")
    if parse_id(ticket_id) not in remote:
        raise RenumberError(f"{ticket_id} 不在 origin/main 上，沒有撞號，不需要 renumber")
    local = load_ticket(repo, ticket_id)
    on_main = json.loads(git(repo, "show", f"origin/main:harness/tickets/{ticket_id}.json"))
    if _same_ticket(local, on_main):
        raise RenumberError(f"本地的 {ticket_id} 與 origin/main 上是同一張票（created_by 與 created_at 相同），不需要 renumber")
    new_id = format_id(max(local_ids(repo) | remote) + 1)
    local["id"] = new_id
    local["history"].append({
        "by": dict(by), "at": now, "from": local["status"], "to": local["status"],
        "note": f"renumber：{ticket_id} → {new_id}",
    })
    save_ticket(repo, local)
    ticket_path(repo, ticket_id).unlink()
    return new_id


def commits_mentioning(repo, ticket_id):
    output = git(repo, "log", "origin/main..HEAD", "--fixed-strings", f"--grep={ticket_id}", "--format=%h %s")
    return [line for line in output.splitlines() if line]


def find_collisions(repo, warn=_warn_stderr):
    remote = remote_ids(repo, warn)
    if remote is None:
        return []
    found = []
    for number in sorted(local_ids(repo) & remote):
        ticket_id = format_id(number)
        on_main = json.loads(git(repo, "show", f"origin/main:harness/tickets/{ticket_id}.json"))
        if not _same_ticket(load_ticket(repo, ticket_id), on_main):
            found.append(ticket_id)
    return found
```

- [ ] **Step 4：執行並確認通過**

Run: `py -3 -m pytest tests/scripts/test_allocate.py`
Expected: `9 passed`

- [ ] **Step 5：Commit**

```bash
git add plugins tests
git commit -m "feat(scripts): 新增票號分配與 renumber"
```

### Task 5：`transitions`（狀態機與 DoD）

**Files:**
- Create: `SCRIPTS/transitions.py`
- Test: `tests/scripts/test_transitions.py`

**Interfaces:**
- Consumes: `gitutil.git_ok`；`tickets.load_all`、`new_ticket`、`save_ticket`、`make_evidence`（測試用）
- Produces:
  - `transitions.FORWARD = {"backlog": "next", "next": "active", "active": "verifying", "verifying": "done"}`
  - `transitions.TransitionError(ValueError)`
  - `latest_evidence(ticket, kind) -> dict | None`
  - `done_problems(ticket) -> list[str]`（空 list 表示可以轉 `done`）
  - `transition(repo, ticket, to, by, now, note="") -> dict`（回傳新 dict，不修改輸入；只允許 `FORWARD` 內的轉換）
  - `block(ticket, by, now, reason) -> dict`
  - `unblock(repo, ticket, by, now, note="") -> dict`（回到進入 blocked 前的狀態）
- 計畫決定：`done` 的票不能進入 `blocked`；spec 沒畫的回退（例如 `active → next`）這版不支援。

- [ ] **Step 1：寫失敗測試**

`tests/scripts/test_transitions.py`：

```python
import pytest

from helpers import commit_all, git
from tickets import make_evidence, new_ticket, save_ticket
from transitions import (
    TransitionError, block, done_problems, transition, unblock,
)

ALICE = {"name": "Alice Chen", "email": "alice@example.com"}
BOB = {"name": "Bob Lin", "email": "bob@example.com"}
NOW = "2026-09-15T10:00:00+08:00"


def ticket_at(repo, ticket_id, status, assignee=ALICE, **overrides):
    ticket = new_ticket(ticket_id, "t", "drivers/uart", ALICE, NOW)
    ticket["status"] = status
    if status in ("active", "verifying", "done"):
        ticket["assignee"] = dict(assignee)
    ticket.update(overrides)
    save_ticket(repo, ticket)
    return ticket


def test_forward_path_sets_assignee_and_history(repo):
    ticket = ticket_at(repo, "FW-0001", "backlog")
    ticket = transition(repo, ticket, "next", ALICE, NOW)
    ticket = transition(repo, ticket, "active", BOB, NOW, note="我來")
    assert ticket["status"] == "active"
    assert ticket["assignee"] == BOB
    assert ticket["history"][-1] == {"by": BOB, "at": NOW, "from": "next", "to": "active", "note": "我來"}


def test_illegal_skip_rejected(repo):
    ticket = ticket_at(repo, "FW-0001", "backlog")
    with pytest.raises(TransitionError, match="不允許 backlog → active"):
        transition(repo, ticket, "active", ALICE, NOW)


def test_transition_does_not_mutate_input(repo):
    ticket = ticket_at(repo, "FW-0001", "backlog")
    transition(repo, ticket, "next", ALICE, NOW)
    assert ticket["status"] == "backlog" and len(ticket["history"]) == 1


def test_blocked_only_via_block_and_unblock(repo):
    ticket = ticket_at(repo, "FW-0001", "next")
    with pytest.raises(TransitionError, match="block"):
        transition(repo, ticket, "blocked", ALICE, NOW)


def test_one_active_per_person(repo):
    ticket_at(repo, "FW-0001", "active", assignee=ALICE)
    second = ticket_at(repo, "FW-0002", "next")
    with pytest.raises(TransitionError, match="已經有 active 的票 FW-0001"):
        transition(repo, second, "active", ALICE, NOW)
    assert transition(repo, second, "active", BOB, NOW)["assignee"] == BOB


def test_verifying_requires_check_on_head_ancestry(repo):
    ticket = ticket_at(repo, "FW-0001", "active")
    with pytest.raises(TransitionError, match="kind: check"):
        transition(repo, ticket, "verifying", ALICE, NOW)

    git(repo, "checkout", "-b", "side")
    (repo / "side.txt").write_text("x", encoding="utf-8")
    side_commit = commit_all(repo, "chore: side")
    git(repo, "checkout", "main")
    ticket["evidence"] = [make_evidence("check", ALICE, NOW, commit=side_commit, summary="check 7/7 通過", passed=True)]
    with pytest.raises(TransitionError, match="kind: check"):
        transition(repo, ticket, "verifying", ALICE, NOW)

    head = git(repo, "rev-parse", "--short", "HEAD")
    ticket["evidence"].append(make_evidence("check", ALICE, NOW, commit=head, summary="check 5/7", passed=False))
    with pytest.raises(TransitionError, match="passed: true"):
        transition(repo, ticket, "verifying", ALICE, NOW)

    ticket["evidence"].append(make_evidence("check", ALICE, NOW, commit=head, summary="check 7/7 通過", passed=True))
    assert transition(repo, ticket, "verifying", ALICE, NOW)["status"] == "verifying"


def test_done_problems_lists_every_gap(repo):
    ticket = ticket_at(repo, "FW-0001", "verifying", dod_pending=["上板 loopback 驗證"])
    problems = done_problems(ticket)
    assert len(problems) == 3
    assert "dod_pending" in problems[0]
    assert "kind: hil" in problems[1]
    assert "kind: review" in problems[2]


def test_self_review_and_open_critical_rejected(repo):
    ticket = ticket_at(repo, "FW-0001", "verifying")
    ticket["evidence"] = [make_evidence("review", ALICE, NOW, ref="r1.md", open_critical=0)]
    assert any("assignee 本人" in p for p in done_problems(ticket))
    ticket["evidence"].append(make_evidence("review", BOB, NOW, ref="r2.md", open_critical=2))
    assert any("2 個 open critical" in p for p in done_problems(ticket))


def test_latest_review_wins_and_hil_optional(repo):
    ticket = ticket_at(repo, "FW-0001", "verifying", requires_hil=False)
    ticket["evidence"] = [
        make_evidence("review", BOB, NOW, ref="r1.md", open_critical=1),
        make_evidence("review", BOB, NOW, ref="r2.md", open_critical=0),
    ]
    assert done_problems(ticket) == []
    ticket["requires_hil"] = True
    assert done_problems(ticket) == [
        "requires_hil 為 true，但沒有 kind: hil 的 evidence。修法：使用 fw-hil-verify"
    ]


def test_done_happy_path(repo):
    ticket = ticket_at(repo, "FW-0001", "verifying")
    ticket["evidence"] = [
        make_evidence("hil", ALICE, NOW, ref="harness/evidence/FW-0001/loopback.log"),
        make_evidence("review", BOB, NOW, ref="harness/reviews/FW-0001_bob_2026-09-16.md", open_critical=0),
    ]
    assert transition(repo, ticket, "done", ALICE, NOW)["status"] == "done"


def test_block_and_unblock_returns_to_previous(repo):
    ticket = ticket_at(repo, "FW-0001", "verifying")
    with pytest.raises(TransitionError, match="blocked_reason"):
        block(ticket, ALICE, NOW, "  ")
    blocked = block(ticket, ALICE, NOW, "等硬體板")
    assert blocked["status"] == "blocked" and blocked["blocked_reason"] == "等硬體板"
    restored = unblock(repo, blocked, ALICE, NOW)
    assert restored["status"] == "verifying" and restored["blocked_reason"] is None
    done = ticket_at(repo, "FW-0002", "done")
    with pytest.raises(TransitionError):
        block(done, ALICE, NOW, "x")


def test_unblock_to_active_respects_one_active(repo):
    first = block(ticket_at(repo, "FW-0001", "active"), ALICE, NOW, "等規格")
    save_ticket(repo, first)
    second = transition(repo, ticket_at(repo, "FW-0002", "next"), "active", ALICE, NOW)
    save_ticket(repo, second)
    with pytest.raises(TransitionError, match="已經有 active 的票 FW-0002"):
        unblock(repo, first, ALICE, NOW)
```

- [ ] **Step 2：執行並確認失敗**

Run: `py -3 -m pytest tests/scripts/test_transitions.py`
Expected: FAIL，`ModuleNotFoundError: No module named 'transitions'`

- [ ] **Step 3：實作**

`SCRIPTS/transitions.py`：

```python
"""狀態機與 Definition of Done（spec 第 5.4 節）。"""
import copy

from gitutil import git_ok
from tickets import load_all

FORWARD = {"backlog": "next", "next": "active", "active": "verifying", "verifying": "done"}


class TransitionError(ValueError):
    pass


def _email(person):
    return ((person or {}).get("email") or "").lower()


def latest_evidence(ticket, kind):
    items = [item for item in ticket.get("evidence", []) if item.get("kind") == kind]
    return items[-1] if items else None


def done_problems(ticket):
    problems = []
    if ticket.get("dod_pending"):
        problems.append(f"dod_pending 尚未清空：{'、'.join(ticket['dod_pending'])}")
    if ticket.get("requires_hil", True) and latest_evidence(ticket, "hil") is None:
        problems.append("requires_hil 為 true，但沒有 kind: hil 的 evidence。修法：使用 fw-hil-verify")
    review = latest_evidence(ticket, "review")
    if review is None:
        problems.append("沒有 kind: review 的 evidence。修法：請 assignee 以外的同事執行 fw-c-review")
    else:
        if _email(review.get("by")) == _email(ticket.get("assignee")):
            problems.append("最新一筆 review 是 assignee 本人做的，不能自己 review 自己")
        if review.get("open_critical", 0) != 0:
            problems.append(f"最新一筆 review 還有 {review['open_critical']} 個 open critical")
    return problems


def _ensure_no_other_active(repo, ticket_id, person):
    others = [other["id"] for _, other in load_all(repo)
              if other.get("id") != ticket_id and other.get("status") == "active"
              and _email(other.get("assignee")) == _email(person)]
    if others:
        raise TransitionError(
            f"{ticket_id}：{person['name']} 已經有 active 的票 {'、'.join(others)}。"
            "每人一次一票，先把那張轉到 verifying 或 blocked"
        )


def _record(ticket, by, now, to, note):
    ticket["history"].append({"by": dict(by), "at": now, "from": ticket["status"], "to": to, "note": note})
    ticket["status"] = to


def transition(repo, ticket, to, by, now, note=""):
    new = copy.deepcopy(ticket)
    ticket_id, status = new["id"], new["status"]
    if to == "blocked":
        raise TransitionError(f"{ticket_id}：進入 blocked 請用 block，並填 blocked_reason")
    if status == "blocked":
        raise TransitionError(f"{ticket_id}：blocked 的票請用 unblock 回到原狀態")
    if FORWARD.get(status) != to:
        raise TransitionError(
            f"{ticket_id}：不允許 {status} → {to}。允許的下一步：{FORWARD.get(status) or '無'}"
        )
    if to == "active":
        _ensure_no_other_active(repo, ticket_id, by)
        new["assignee"] = dict(by)
    elif to == "verifying":
        checks = [item for item in new["evidence"] if item.get("kind") == "check"]
        if not any(git_ok(repo, "merge-base", "--is-ancestor", item["commit"], "HEAD") for item in checks):
            raise TransitionError(
                f"{ticket_id}：active → verifying 需要至少一筆 kind: check 的 evidence，"
                "且其 commit 是 HEAD 或 HEAD 的祖先。"
                f"修法：check 通過後執行 ticket.py evidence {ticket_id} check --commit <hash> --summary <摘要> --passed"
            )
        if not any(item.get("passed") is True
                   and git_ok(repo, "merge-base", "--is-ancestor", item["commit"], "HEAD") for item in checks):
            raise TransitionError(
                f"{ticket_id}：HEAD 歷史上的 check evidence 都沒有 passed: true。修法：修到 check 通過後重新記錄"
            )
    elif to == "done":
        problems = done_problems(new)
        if problems:
            raise TransitionError(f"{ticket_id}：verifying → done 條件未滿足：\n- " + "\n- ".join(problems))
    _record(new, by, now, to, note)
    return new


def block(ticket, by, now, reason):
    new = copy.deepcopy(ticket)
    if not reason or not reason.strip():
        raise TransitionError(f"{new['id']}：進入 blocked 必須填 blocked_reason")
    if new["status"] in ("blocked", "done"):
        raise TransitionError(f"{new['id']}：{new['status']} 的票不能進入 blocked")
    new["blocked_reason"] = reason.strip()
    _record(new, by, now, "blocked", reason.strip())
    return new


def unblock(repo, ticket, by, now, note=""):
    new = copy.deepcopy(ticket)
    if new["status"] != "blocked":
        raise TransitionError(f"{new['id']}：只有 blocked 的票可以 unblock，目前是 {new['status']}")
    previous = next((item["from"] for item in reversed(new["history"])
                     if item.get("to") == "blocked" and item.get("from") not in (None, "blocked")), None)
    if previous is None:
        raise TransitionError(f"{new['id']}：history 找不到進入 blocked 前的狀態，請手動檢查票檔")
    if previous == "active":
        _ensure_no_other_active(repo, new["id"], new["assignee"])
    new["blocked_reason"] = None
    _record(new, by, now, previous, note or "解除 blocked")
    return new
```

- [ ] **Step 4：執行並確認通過**

Run: `py -3 -m pytest tests/scripts/test_transitions.py`
Expected: `12 passed`

- [ ] **Step 5：Commit**

```bash
git add plugins tests
git commit -m "feat(scripts): 新增狀態機與 DoD 條件檢查"
```

### Task 6：`ticket_check`（全域票檢查）

**Files:**
- Create: `SCRIPTS/ticket_check.py`
- Test: `tests/scripts/test_ticket_check.py`

**Interfaces:**
- Consumes: `tickets.load_all`、`validate_ticket`；`transitions.done_problems`
- Produces:
  - `ticket_check.check_tickets(repo) -> list[str]`（空 list 表示通過）
  - `ticket_check.main(argv=None) -> int`（從目前目錄找 repo root；通過印 `ticket_check：通過（N 張票）` 回傳 0；失敗把每條錯誤印到 stderr 回傳 1）
  - 計畫 2 的 `check.py` 會 `import ticket_check` 並呼叫 `check_tickets`

- [ ] **Step 1：寫失敗測試**

`tests/scripts/test_ticket_check.py`：

```python
from jsonio import write_json_atomic
from ticket_check import check_tickets, main
from tickets import make_evidence, new_ticket, save_ticket, ticket_path

ALICE = {"name": "Alice Chen", "email": "alice@example.com"}
BOB = {"name": "Bob Lin", "email": "bob@example.com"}
NOW = "2026-09-15T10:00:00+08:00"


def put(repo, ticket_id, status="backlog", assignee=None, **overrides):
    ticket = new_ticket(ticket_id, "t", "drivers/uart", ALICE, NOW)
    ticket.update(status=status, assignee=assignee, **overrides)
    save_ticket(repo, ticket)
    return ticket


def test_empty_and_valid_pass(repo):
    assert check_tickets(repo) == []
    put(repo, "FW-0001")
    put(repo, "FW-0002", "active", ALICE)
    assert check_tickets(repo) == []


def test_schema_error_reported_with_filename(repo):
    put(repo, "FW-0001", status="doing")
    assert any(e.startswith("FW-0001.json：") and "status" in e for e in check_tickets(repo))


def test_broken_json_reported(repo):
    ticket_path(repo, "FW-0001").write_text("{ 壞掉", encoding="utf-8")
    errors = check_tickets(repo)
    assert len(errors) == 1 and "FW-0001.json" in errors[0] and "JSON" in errors[0]


def test_duplicate_id_reported(repo):
    ticket = put(repo, "FW-0001")
    write_json_atomic(ticket_path(repo, "FW-0002"), ticket)
    assert any("重複" in e and "FW-0001" in e for e in check_tickets(repo))


def test_two_active_for_same_assignee(repo):
    put(repo, "FW-0001", "active", ALICE)
    put(repo, "FW-0002", "active", {"name": "Alice", "email": "ALICE@example.com"})
    put(repo, "FW-0003", "active", BOB)
    errors = check_tickets(repo)
    assert len(errors) == 1 and "FW-0001、FW-0002" in errors[0]


def test_done_without_dod_reported(repo):
    put(repo, "FW-0001", "done", ALICE)
    ok = put(repo, "FW-0002", "done", ALICE, requires_hil=False,
             evidence=[make_evidence("review", BOB, NOW, ref="r.md", open_critical=0)])
    errors = check_tickets(repo)
    assert len(errors) == 1 and errors[0].startswith("FW-0001.json：") and "kind: review" in errors[0]
    assert ok["id"] == "FW-0002"


def test_main_exit_codes(repo, monkeypatch, capsys):
    monkeypatch.chdir(repo)
    put(repo, "FW-0001")
    assert main([]) == 0
    assert "通過（1 張票）" in capsys.readouterr().out
    put(repo, "FW-0002", status="blocked")
    assert main([]) == 1
    assert "blocked_reason" in capsys.readouterr().err
```

- [ ] **Step 2：執行並確認失敗**

Run: `py -3 -m pytest tests/scripts/test_ticket_check.py`
Expected: FAIL，`ModuleNotFoundError: No module named 'ticket_check'`

- [ ] **Step 3：實作**

`SCRIPTS/ticket_check.py`：

```python
"""check 第 4 步：所有票檔的全域一致性檢查（spec 第 5.5 節）。"""
import json
import sys
from collections import defaultdict
from pathlib import Path

from gitutil import repo_root
from jsonio import read_json
from tickets import tickets_dir, validate_ticket
from transitions import done_problems


def _load(repo):
    loaded, errors = [], []
    directory = tickets_dir(repo)
    for path in sorted(directory.glob("FW-*.json")) if directory.exists() else []:
        try:
            loaded.append((path, read_json(path)))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            errors.append(f"{path.name}：不是合法的 UTF-8 JSON（{exc}）。修法：修正檔案內容或從 git 還原")
    return loaded, errors


def check_tickets(repo):
    loaded, errors = _load(repo)
    by_id = defaultdict(list)
    active_by_email = defaultdict(list)
    for path, ticket in loaded:
        problems = validate_ticket(ticket, path.name)
        errors.extend(problems)
        if not isinstance(ticket, dict):
            continue
        by_id[ticket.get("id")].append(path.name)
        if problems:
            continue
        if ticket["status"] == "active":
            active_by_email[ticket["assignee"]["email"].lower()].append(ticket["id"])
        if ticket["status"] == "done":
            errors.extend(f"{path.name}：done 條件未滿足：{p}" for p in done_problems(ticket))
    for ticket_id, names in by_id.items():
        if len(names) > 1:
            errors.append(f"票號 {ticket_id} 重複出現在 {'、'.join(names)}。修法：ticket.py renumber {ticket_id}")
    for email, ids in active_by_email.items():
        if len(ids) > 1:
            errors.append(f"{email} 同時有多張 active 的票：{'、'.join(ids)}。修法：只留一張 active，其餘轉 verifying 或 blocked")
    return errors


def main(argv=None):
    repo = repo_root(Path.cwd())
    errors = check_tickets(repo)
    if errors:
        for error in errors:
            print(f"ticket_check 失敗：{error}", file=sys.stderr)
        return 1
    count = len(list(tickets_dir(repo).glob("FW-*.json"))) if tickets_dir(repo).exists() else 0
    print(f"ticket_check：通過（{count} 張票）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 4：執行並確認通過**

Run: `py -3 -m pytest tests/scripts/test_ticket_check.py`
Expected: `7 passed`

- [ ] **Step 5：Commit**

```bash
git add plugins tests
git commit -m "feat(scripts): 新增 ticket_check 全域票檢查"
```

### Task 7：`index`（產生 `feature_list.json`）

**Files:**
- Create: `SCRIPTS/index.py`
- Test: `tests/scripts/test_index.py`

**Interfaces:**
- Consumes: `gitutil.git`、`repo_root`；`jsonio.write_json_atomic`；`tickets.load_all`、`now_iso`、`EVIDENCE_KINDS`；`transitions.latest_evidence`
- Produces:
  - `index.INDEX_NAME = "feature_list.json"`（放在 repo root，由計畫 3 的範本加進 `.gitignore`）
  - `index.TICKET_REF_RE`（`(?<![A-Za-z0-9-])FW-\d{4,}(?!\d)`；計畫 2 的 `commit-msg` hook 要用同一個）
  - `index.commit_evidence(repo) -> dict[str, list[dict]]`：票號 → `[{"kind": "commit", "commit": <前 10 碼>, "by": {"name", "email"}, "at": <author ISO 時間>, "subject": str}]`，依 git log 由新到舊；subject 與 body 都掃
  - `index.build_index(repo) -> {"generated_at": str, "tickets": [entry]}`，entry 欄位：`id`、`title`、`area`、`status`、`priority`、`assignee`、`requires_hil`、`dod_pending`、`blocked_reason`、`evidence_counts`（`check`/`hil`/`review` 各幾筆）、`latest_review_open_critical`（沒有 review 時為 `null`）、`commits`
  - `index.write_index(repo) -> Path`
  - `index.main(argv=None) -> int`（計畫 2 的 `post-commit`、`post-merge` hook 會呼叫）

- [ ] **Step 1：寫失敗測試**

`tests/scripts/test_index.py`：

```python
from helpers import commit_all, git
from index import INDEX_NAME, build_index, commit_evidence, main, write_index
from jsonio import read_json
from tickets import make_evidence, new_ticket, save_ticket

ALICE = {"name": "Alice Chen", "email": "alice@example.com"}
BOB = {"name": "Bob Lin", "email": "bob@example.com"}
NOW = "2026-09-15T10:00:00+08:00"


def seed(repo):
    first = new_ticket("FW-0001", "UART DMA", "drivers/uart", ALICE, NOW, priority=2)
    first.update(status="active", assignee=ALICE, dod_pending=["上板"])
    first["evidence"] = [
        make_evidence("check", ALICE, NOW, commit="abc1234", summary="check 7/7 通過", passed=True),
        make_evidence("review", BOB, NOW, ref="r.md", open_critical=1),
    ]
    save_ticket(repo, first)
    save_ticket(repo, new_ticket("FW-0002", "SPI", "drivers/spi", BOB, NOW))
    commit_all(repo, "FW-0001 開票")
    (repo / "a.txt").write_text("a", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "harness: 調整", "-m", "順便處理 FW-0002 與修正FW-0001，不含 XFW-0003")


def test_commit_evidence_scans_subject_and_body(repo):
    seed(repo)
    evidence = commit_evidence(repo)
    assert [c["subject"] for c in evidence["FW-0001"]] == ["harness: 調整", "FW-0001 開票"]
    assert [c["subject"] for c in evidence["FW-0002"]] == ["harness: 調整"]
    assert "FW-0003" not in evidence
    item = evidence["FW-0001"][1]
    assert item["kind"] == "commit" and len(item["commit"]) == 10
    assert item["by"] == ALICE and item["at"].startswith("20")


def test_build_index_summary(repo):
    seed(repo)
    tickets = {t["id"]: t for t in build_index(repo)["tickets"]}
    first = tickets["FW-0001"]
    assert first["status"] == "active" and first["assignee"] == ALICE
    assert first["requires_hil"] is True
    assert first["evidence_counts"] == {"check": 1, "hil": 0, "review": 1}
    assert first["latest_review_open_critical"] == 1
    assert len(first["commits"]) == 2
    assert tickets["FW-0002"]["latest_review_open_critical"] is None


def test_write_index_leaves_tracked_files_untouched(repo):
    seed(repo)
    path = write_index(repo)
    assert path == repo / INDEX_NAME
    assert read_json(path)["tickets"][0]["id"] == "FW-0001"
    assert git(repo, "status", "--porcelain") == f"?? {INDEX_NAME}"


def test_main_prints_count(repo, monkeypatch, capsys):
    seed(repo)
    monkeypatch.chdir(repo)
    assert main([]) == 0
    assert "2 張票" in capsys.readouterr().out
```

- [ ] **Step 2：執行並確認失敗**

Run: `py -3 -m pytest tests/scripts/test_index.py`
Expected: FAIL，`ModuleNotFoundError: No module named 'index'`

- [ ] **Step 3：實作**

`SCRIPTS/index.py`：

```python
"""產生 feature_list.json（gitignored）：票摘要 + 由 git log 動態算出的 commit evidence。"""
import re
import sys
from collections import defaultdict
from pathlib import Path

from gitutil import git, repo_root
from jsonio import read_json, write_json_atomic
from tickets import EVIDENCE_KINDS, load_all, now_iso
from transitions import latest_evidence

INDEX_NAME = "feature_list.json"
# 不用 \b：中文字屬於 \w，「修正FW-0001」會比對不到
TICKET_REF_RE = re.compile(r"(?<![A-Za-z0-9-])FW-\d{4,}(?!\d)")
_FIELD, _RECORD = "\x1f", "\x1e"


def commit_evidence(repo):
    output = git(repo, "log", "--format=%H%x1f%an%x1f%ae%x1f%aI%x1f%s%x1f%b%x1e")
    result = defaultdict(list)
    for record in output.split(_RECORD):
        record = record.strip("\n")
        if not record.strip():
            continue
        sha, name, email, at, subject, body = record.split(_FIELD, 5)
        for ticket_id in sorted(set(TICKET_REF_RE.findall(f"{subject}\n{body}"))):
            result[ticket_id].append({
                "kind": "commit", "commit": sha[:10],
                "by": {"name": name, "email": email}, "at": at, "subject": subject,
            })
    return result


def build_index(repo):
    commits = commit_evidence(repo)
    entries = []
    for _, ticket in load_all(repo):
        review = latest_evidence(ticket, "review")
        entries.append({
            "id": ticket["id"],
            "title": ticket["title"],
            "area": ticket["area"],
            "status": ticket["status"],
            "priority": ticket["priority"],
            "assignee": ticket["assignee"],
            "requires_hil": ticket["requires_hil"],
            "dod_pending": ticket["dod_pending"],
            "blocked_reason": ticket["blocked_reason"],
            "evidence_counts": {kind: sum(1 for e in ticket["evidence"] if e["kind"] == kind)
                                for kind in EVIDENCE_KINDS},
            "latest_review_open_critical": review["open_critical"] if review else None,
            "commits": commits.get(ticket["id"], []),
        })
    return {"generated_at": now_iso(), "tickets": entries}


def write_index(repo):
    path = Path(repo) / INDEX_NAME
    write_json_atomic(path, build_index(repo))
    return path


def main(argv=None):
    repo = repo_root(Path.cwd())
    path = write_index(repo)
    count = len(read_json(path)["tickets"])
    print(f"已產生 {path.name}（{count} 張票）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 4：執行並確認通過**

Run: `py -3 -m pytest tests/scripts/test_index.py`
Expected: `4 passed`

- [ ] **Step 5：Commit**

```bash
git add plugins tests
git commit -m "feat(scripts): 新增 feature_list.json 索引產生"
```

### Task 8：`ticket.py` CLI 與 UTF-8 主控台輸出

**Files:**
- Create: `SCRIPTS/console.py`
- Create: `SCRIPTS/ticket.py`
- Modify: `SCRIPTS/ticket_check.py`（`main` 開頭呼叫 `use_utf8_stdio()`）
- Modify: `SCRIPTS/index.py`（`main` 開頭呼叫 `use_utf8_stdio()`）
- Test: `tests/scripts/test_ticket_cli.py`

**Interfaces:**
- Consumes: `allocate.next_ticket_id`、`renumber`、`commits_mentioning`、`find_collisions`、`RenumberError`；`transitions.transition`、`block`、`unblock`、`TransitionError`；`identity.current_identity`、`IdentityError`；`gitutil.git`、`repo_root`、`GitError`；`tickets.load_ticket`、`save_ticket`、`new_ticket`、`make_evidence`、`validate_ticket`、`now_iso`、`EVIDENCE_FIELDS`
- Produces:
  - `console.use_utf8_stdio() -> None`（把 stdout/stderr 改成 UTF-8，避免 Windows 管線用 cp950 輸出時丟出 `UnicodeEncodeError`）
  - `ticket.confirm_done_on_tty(ticket_id) -> bool`（stdin 不是 TTY 就回傳 False；否則要求輸入票號）
  - `ticket.main(argv=None, cwd=None, now=None, confirm=None) -> int`（`confirm` 預設為 `confirm_done_on_tty`；測試注入）
  - 子命令（**沒有任何指定身分的參數**，身分一律來自 git config）：
    - `new --title T --area A [--priority N] [--behavior B] [--step S]... [--dod D]... [--no-hil]`
    - `claim FW-NNNN`（`backlog` 會先轉 `next` 再轉 `active`）
    - `move FW-NNNN {next,active,verifying,done} [--note N]`（`done`：DoD 檢查通過後才呼叫 `confirm`，未確認就失敗且不寫檔）
    - `block FW-NNNN --reason R`、`unblock FW-NNNN [--note N]`
    - `evidence FW-NNNN {check,hil,review} [--commit C] [--summary S] [--passed | --failed] [--ref R] [--open-critical N]`（check 的 commit 會解析成 10 碼 hash，不存在就失敗；check 必須給 `--passed` 或 `--failed`）
    - `dod FW-NNNN [--add D]... [--remove D]...`（每次變更在 history 記一筆 `from == to` 的 note）
    - `collisions`（有撞號時列出並回傳 1）、`renumber FW-NNNN`、`show FW-NNNN`
  - 失敗訊息格式：`ticket.py <子命令> 失敗：<原因與修法>`，回傳 1

- [ ] **Step 1：寫失敗測試**

`tests/scripts/test_ticket_cli.py`：

```python
import json

import pytest

from helpers import git
from ticket import main
from tickets import load_ticket, make_evidence, save_ticket

NOW = "2026-09-15T10:00:00+08:00"
BOB = {"name": "Bob Lin", "email": "bob@example.com"}


def run(repo, *argv):
    return main(list(argv), cwd=repo, now=NOW, confirm=lambda ticket_id: True)


def test_new_uses_git_identity_and_warns_offline(repo, capsys):
    assert run(repo, "new", "--title", "UART DMA", "--area", "drivers/uart",
               "--step", "上板：loopback", "--dod", "上板 loopback 驗證") == 0
    out = capsys.readouterr()
    assert "已開票 FW-0001" in out.out
    assert "離線" in out.err
    ticket = load_ticket(repo, "FW-0001")
    assert ticket["created_by"] == {"name": "Alice Chen", "email": "alice@example.com"}
    assert ticket["verification_steps"] == ["上板：loopback"]


def test_identity_cannot_be_passed_as_argument(repo):
    with pytest.raises(SystemExit):
        run(repo, "new", "--title", "t", "--area", "a", "--by", "bob@example.com")


def test_claim_from_backlog_goes_through_next(repo):
    run(repo, "new", "--title", "t", "--area", "a")
    assert run(repo, "claim", "FW-0001") == 0
    ticket = load_ticket(repo, "FW-0001")
    assert ticket["status"] == "active"
    assert [h["to"] for h in ticket["history"]] == ["backlog", "next", "active"]


def test_move_failure_message(repo, capsys):
    run(repo, "new", "--title", "t", "--area", "a")
    run(repo, "claim", "FW-0001")
    assert run(repo, "move", "FW-0001", "verifying") == 1
    err = capsys.readouterr().err
    assert "ticket.py move 失敗" in err and "kind: check" in err


def test_check_evidence_resolves_commit_then_verifying(repo, capsys):
    run(repo, "new", "--title", "t", "--area", "a")
    run(repo, "claim", "FW-0001")
    assert run(repo, "evidence", "FW-0001", "check", "--commit", "nope", "--summary", "s", "--passed") == 1
    assert run(repo, "evidence", "FW-0001", "check", "--commit", "HEAD", "--summary", "check 7/7 通過") == 1
    assert "--passed 或 --failed" in capsys.readouterr().err
    assert run(repo, "evidence", "FW-0001", "check", "--commit", "HEAD", "--summary", "check 7/7 通過", "--passed") == 0
    head = git(repo, "rev-parse", "HEAD")
    evidence = load_ticket(repo, "FW-0001")["evidence"][0]
    assert evidence["commit"] == head[:10] and evidence["passed"] is True
    assert run(repo, "move", "FW-0001", "verifying") == 0


def test_review_evidence_requires_open_critical(repo, capsys):
    run(repo, "new", "--title", "t", "--area", "a")
    assert run(repo, "evidence", "FW-0001", "review", "--ref", "r.md") == 1
    assert "open_critical" in capsys.readouterr().err
    assert run(repo, "evidence", "FW-0001", "review", "--ref", "r.md", "--open-critical", "0") == 0


def test_dod_add_remove(repo, capsys):
    run(repo, "new", "--title", "t", "--area", "a", "--dod", "上板")
    assert run(repo, "dod", "FW-0001", "--add", "review", "--remove", "上板") == 0
    ticket = load_ticket(repo, "FW-0001")
    assert ticket["dod_pending"] == ["review"]
    assert ticket["history"][-1]["note"] == "dod：新增 review；完成 上板"
    assert run(repo, "dod", "FW-0001", "--remove", "不存在") == 1


def test_block_unblock(repo):
    run(repo, "new", "--title", "t", "--area", "a")
    with pytest.raises(SystemExit):
        run(repo, "block", "FW-0001")
    assert run(repo, "block", "FW-0001", "--reason", "等硬體") == 0
    assert load_ticket(repo, "FW-0001")["status"] == "blocked"
    assert run(repo, "unblock", "FW-0001") == 0
    assert load_ticket(repo, "FW-0001")["status"] == "backlog"


def ready_for_done(repo):
    run(repo, "new", "--title", "t", "--area", "a", "--no-hil")
    run(repo, "claim", "FW-0001")
    run(repo, "evidence", "FW-0001", "check", "--commit", "HEAD", "--summary", "ok", "--passed")
    run(repo, "move", "FW-0001", "verifying")
    ticket = load_ticket(repo, "FW-0001")
    ticket["evidence"].append(make_evidence("review", BOB, NOW, ref="r.md", open_critical=0))
    save_ticket(repo, ticket)


def test_done_via_cli_after_review_by_other(repo):
    ready_for_done(repo)
    assert load_ticket(repo, "FW-0001")["requires_hil"] is False
    assert run(repo, "move", "FW-0001", "done") == 0
    assert load_ticket(repo, "FW-0001")["status"] == "done"


def test_done_refused_without_tty(repo, capsys):
    ready_for_done(repo)
    capsys.readouterr()
    # 不注入 confirm：pytest 的 stdin 不是 TTY，等同 agent 執行
    assert main(["move", "FW-0001", "done"], cwd=repo, now=NOW) == 1
    assert "互動式終端機" in capsys.readouterr().err
    assert load_ticket(repo, "FW-0001")["status"] == "verifying"


def test_collisions_offline_reports_none(repo, capsys):
    assert run(repo, "collisions") == 0
    out = capsys.readouterr()
    assert "沒有撞號" in out.out and "離線" in out.err


def test_show_prints_utf8_json(repo, capsys):
    run(repo, "new", "--title", "UART 驅動", "--area", "a")
    capsys.readouterr()
    assert run(repo, "show", "FW-0001") == 0
    assert json.loads(capsys.readouterr().out)["title"] == "UART 驅動"


def test_missing_identity(repo, tmp_path, monkeypatch, capsys):
    git(repo, "config", "--unset", "user.name")
    empty = tmp_path / "empty-gitconfig"
    empty.write_text("", encoding="utf-8")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(empty))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    assert run(repo, "new", "--title", "t", "--area", "a") == 1
    assert "git config user.name" in capsys.readouterr().err
```

- [ ] **Step 2：執行並確認失敗**

Run: `py -3 -m pytest tests/scripts/test_ticket_cli.py`
Expected: FAIL，`ModuleNotFoundError: No module named 'ticket'`

- [ ] **Step 3：實作 `console.py`**

`SCRIPTS/console.py`：

```python
"""主控台輸出一律 UTF-8，不依賴 Windows 的 cp950。"""
import sys


def use_utf8_stdio():
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")
```

- [ ] **Step 4：實作 `ticket.py`**

`SCRIPTS/ticket.py`：

```python
"""票的 CLI：所有狀態寫入的唯一入口。身分一律取自 git config，不接受參數指定。"""
import argparse
import json
import sys
from pathlib import Path

from allocate import RenumberError, commits_mentioning, find_collisions, next_ticket_id, renumber
from console import use_utf8_stdio
from gitutil import GitError, git, repo_root
from identity import IdentityError, current_identity
from tickets import (
    EVIDENCE_FIELDS, EVIDENCE_KINDS, load_ticket, make_evidence, new_ticket, now_iso, save_ticket,
    validate_ticket,
)
from transitions import TransitionError, block, transition, unblock


def build_parser():
    parser = argparse.ArgumentParser(prog="ticket.py", description="FW 票操作（身分取自 git config）")
    sub = parser.add_subparsers(dest="command", required=True)

    new = sub.add_parser("new", help="開新票")
    new.add_argument("--title", required=True)
    new.add_argument("--area", required=True)
    new.add_argument("--priority", type=int, default=3)
    new.add_argument("--behavior", default="")
    new.add_argument("--step", action="append", default=[])
    new.add_argument("--dod", action="append", default=[])
    new.add_argument("--no-hil", dest="requires_hil", action="store_false",
                     help="這張票不需要上板驗證（預設需要）")

    sub.add_parser("claim", help="認領並轉 active").add_argument("ticket_id")

    move = sub.add_parser("move", help="轉狀態")
    move.add_argument("ticket_id")
    move.add_argument("status", choices=["next", "active", "verifying", "done"])
    move.add_argument("--note", default="")

    blk = sub.add_parser("block", help="進入 blocked")
    blk.add_argument("ticket_id")
    blk.add_argument("--reason", required=True)

    unb = sub.add_parser("unblock", help="解除 blocked")
    unb.add_argument("ticket_id")
    unb.add_argument("--note", default="")

    ev = sub.add_parser("evidence", help="新增 check / hil / review evidence")
    ev.add_argument("ticket_id")
    ev.add_argument("kind", choices=EVIDENCE_KINDS)
    ev.add_argument("--commit")
    ev.add_argument("--summary")
    outcome = ev.add_mutually_exclusive_group()
    outcome.add_argument("--passed", dest="passed", action="store_true")
    outcome.add_argument("--failed", dest="passed", action="store_false")
    ev.set_defaults(passed=None)
    ev.add_argument("--ref")
    ev.add_argument("--open-critical", dest="open_critical", type=int)

    dod = sub.add_parser("dod", help="新增或完成 dod_pending 項目")
    dod.add_argument("ticket_id")
    dod.add_argument("--add", action="append", default=[])
    dod.add_argument("--remove", action="append", default=[])

    sub.add_parser("collisions", help="合併前檢查本地票號是否與 origin/main 撞號")
    sub.add_parser("renumber", help="撞號時把本地票改成下一個空號").add_argument("ticket_id")
    sub.add_parser("show", help="顯示票").add_argument("ticket_id")
    return parser


def confirm_done_on_tty(ticket_id):
    if not sys.stdin.isatty():
        return False
    answer = input(f"確認 {ticket_id} 已完成上板驗證並經他人 review？請輸入票號確認：")
    return answer.strip() == ticket_id


def _save(repo, ticket):
    errors = validate_ticket(ticket, f"{ticket['id']}.json")
    if errors:
        raise ValueError("寫入前 schema 檢查失敗：" + "；".join(errors))
    save_ticket(repo, ticket)


def cmd_new(repo, args, by, now):
    ticket_id = next_ticket_id(repo)
    ticket = new_ticket(ticket_id, args.title, args.area, by, now, priority=args.priority,
                        user_visible_behavior=args.behavior, verification_steps=args.step,
                        dod_pending=args.dod, requires_hil=args.requires_hil)
    _save(repo, ticket)
    print(f"已開票 {ticket_id}：{args.title}")
    print("提醒：票號要等開票 commit 合入 main 之後才算佔住。")
    return 0


def cmd_claim(repo, args, by, now):
    ticket = load_ticket(repo, args.ticket_id)
    if ticket["status"] == "backlog":
        ticket = transition(repo, ticket, "next", by, now, note="認領")
    ticket = transition(repo, ticket, "active", by, now, note="認領")
    _save(repo, ticket)
    print(f"{ticket['id']} 已由 {by['name']} 認領，狀態 active")
    return 0


def cmd_move(repo, args, by, now):
    ticket = transition(repo, load_ticket(repo, args.ticket_id), args.status, by, now, note=args.note)
    if args.status == "done" and not args.confirm(ticket["id"]):
        raise ValueError(
            "轉成 done 必須由人在互動式終端機輸入票號確認（agent 不可自行標記 done）。"
            f"修法：請在自己的終端機執行 ticket.py move {ticket['id']} done"
        )
    _save(repo, ticket)
    print(f"{ticket['id']} → {ticket['status']}")
    return 0


def cmd_block(repo, args, by, now):
    ticket = block(load_ticket(repo, args.ticket_id), by, now, args.reason)
    _save(repo, ticket)
    print(f"{ticket['id']} → blocked：{ticket['blocked_reason']}")
    return 0


def cmd_unblock(repo, args, by, now):
    ticket = unblock(repo, load_ticket(repo, args.ticket_id), by, now, note=args.note)
    _save(repo, ticket)
    print(f"{ticket['id']} → {ticket['status']}")
    return 0


def cmd_evidence(repo, args, by, now):
    ticket = load_ticket(repo, args.ticket_id)
    if args.kind == "check" and args.passed is None:
        raise ValueError("check evidence 必須指定 --passed 或 --failed")
    given = {"commit": args.commit, "summary": args.summary, "passed": args.passed,
             "ref": args.ref, "open_critical": args.open_critical}
    fields = {key: given[key] for key in EVIDENCE_FIELDS[args.kind]}
    if args.kind == "check" and fields["commit"]:
        fields["commit"] = git(repo, "rev-parse", "--verify", f"{fields['commit']}^{{commit}}")[:10]
    ticket["evidence"].append(make_evidence(args.kind, by, now, **fields))
    _save(repo, ticket)
    print(f"{ticket['id']} 已新增 {args.kind} evidence")
    return 0


def cmd_dod(repo, args, by, now):
    ticket = load_ticket(repo, args.ticket_id)
    missing = [item for item in args.remove if item not in ticket["dod_pending"]]
    if missing:
        raise ValueError(f"dod_pending 沒有這些項目：{'、'.join(missing)}。目前項目：{'、'.join(ticket['dod_pending']) or '無'}")
    if not args.add and not args.remove:
        raise ValueError("請至少指定一個 --add 或 --remove")
    ticket["dod_pending"] = [item for item in ticket["dod_pending"] if item not in args.remove] + args.add
    parts = [f"新增 {item}" for item in args.add] + [f"完成 {item}" for item in args.remove]
    ticket["history"].append({"by": dict(by), "at": now, "from": ticket["status"],
                              "to": ticket["status"], "note": "dod：" + "；".join(parts)})
    _save(repo, ticket)
    print(f"{ticket['id']} dod_pending：{'、'.join(ticket['dod_pending']) or '已清空'}")
    return 0


def cmd_renumber(repo, args, by, now):
    old_id = args.ticket_id
    new_id = renumber(repo, old_id, by, now)
    print(f"已將本地的 {old_id} 改為 {new_id}。請 git add harness/tickets 後 commit。")
    commits = commits_mentioning(repo, old_id)
    if commits:
        print(f"分支上以下 commit 的訊息仍引用 {old_id}，確認分支沒有其他人使用後，請改寫成 {new_id}：")
        for line in commits:
            print(f"  {line}")
    return 0


def cmd_show(repo, args, by, now):
    print(json.dumps(load_ticket(repo, args.ticket_id), ensure_ascii=False, indent=2))
    return 0


def cmd_collisions(repo, args, by, now):
    found = find_collisions(repo)
    if not found:
        print("沒有撞號")
        return 0
    for ticket_id in found:
        print(f"撞號：本地的 {ticket_id} 與 origin/main 上的不是同一張票。修法：ticket.py renumber {ticket_id}")
    return 1


COMMANDS = {
    "new": cmd_new, "claim": cmd_claim, "move": cmd_move, "block": cmd_block, "unblock": cmd_unblock,
    "evidence": cmd_evidence, "dod": cmd_dod, "collisions": cmd_collisions, "renumber": cmd_renumber,
    "show": cmd_show,
}


def main(argv=None, cwd=None, now=None, confirm=None):
    use_utf8_stdio()
    args = build_parser().parse_args(argv)
    args.confirm = confirm or confirm_done_on_tty
    try:
        repo = repo_root(cwd or Path.cwd())
        by = current_identity(repo)
        return COMMANDS[args.command](repo, args, by, now or now_iso())
    except (IdentityError, GitError, TransitionError, RenumberError, FileNotFoundError, ValueError) as exc:
        print(f"ticket.py {args.command} 失敗：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 5：`ticket_check.py` 與 `index.py` 也改用 UTF-8 輸出**

兩個檔案都加上 import：

```python
from console import use_utf8_stdio
```

並把兩個 `main` 的第一行改成：

```python
def main(argv=None):
    use_utf8_stdio()
    repo = repo_root(Path.cwd())
```

- [ ] **Step 6：執行並確認通過**

Run: `py -3 -m pytest`
Expected: 全部通過，`79 passed`

- [ ] **Step 7：Commit**

```bash
git add plugins tests
git commit -m "feat(scripts): 新增 ticket.py CLI 與 UTF-8 主控台輸出"
```

### Task 9：兩人協作整合測試

**Files:**
- Test: `tests/scripts/test_team_flow.py`

**Interfaces:**
- Consumes: `ticket.main`、`ticket_check.check_tickets`、`index.build_index`、`tickets.load_ticket`；fixture `team`；`helpers.git`、`commit_all`
- Produces: 無新程式碼。這個測試模擬 spec 第 9 節「兩個不同 git 身分並行：同時開票撞號、各自 active、互相 review」。如果它失敗，要回頭修前面任務的模組，不能改測試來遷就。

- [ ] **Step 1：寫整合測試**

`tests/scripts/test_team_flow.py`：

```python
from helpers import commit_all, git
from index import build_index
from ticket import main
from ticket_check import check_tickets
from tickets import load_ticket

NOW = "2026-09-15T10:00:00+08:00"


def run(repo, *argv):
    # 整合測試代表「人」在終端機操作，所以注入確認；TTY 拒絕的情境在 test_ticket_cli.py 測
    return main(list(argv), cwd=repo, now=NOW, confirm=lambda ticket_id: True)


def test_two_people_collide_claim_review_and_finish(team):
    _, clones = team
    alice, bob = clones["alice"], clones["bob"]

    # 1. 兩人在對方 push 之前各自開票，拿到同一個號碼
    assert run(alice, "new", "--title", "UART DMA", "--area", "drivers/uart",
               "--step", "上板：loopback 4KB", "--dod", "上板 loopback 驗證") == 0
    commit_all(alice, "FW-0001 開票：UART DMA")
    assert run(bob, "new", "--title", "SPI flash", "--area", "drivers/spi") == 0
    commit_all(bob, "FW-0001 開票：SPI flash")
    git(bob, "push", "origin", "main")

    # 2. alice 合併前預檢發現撞號；她是後進者，renumber 後可以乾淨合併
    assert run(alice, "collisions") == 1
    assert run(alice, "renumber", "FW-0001") == 0
    commit_all(alice, "harness: FW-0001 改號為 FW-0002")
    git(alice, "merge", "--no-edit", "origin/main")
    assert load_ticket(alice, "FW-0001")["title"] == "SPI flash"
    assert load_ticket(alice, "FW-0002")["title"] == "UART DMA"
    git(alice, "push", "origin", "main")
    git(bob, "pull", "--no-edit", "origin", "main")

    # 3. 各自認領；同一人不能同時有兩張 active
    assert run(alice, "claim", "FW-0002") == 0
    commit_all(alice, "FW-0002 認領")
    assert run(alice, "claim", "FW-0001") == 1
    assert run(bob, "claim", "FW-0001") == 0
    commit_all(bob, "FW-0001 認領")

    # 4. alice 寫完、check 通過 → verifying；自己 review 不能轉 done
    (alice / "uart.c").write_text("int uart_init(void) { return 0; }\n", encoding="utf-8")
    head = commit_all(alice, "FW-0002 實作 DMA 接收")
    assert run(alice, "evidence", "FW-0002", "check", "--commit", head, "--summary", "check 7/7 通過", "--passed") == 0
    assert run(alice, "move", "FW-0002", "verifying") == 0
    assert run(alice, "evidence", "FW-0002", "review", "--ref", "harness/reviews/self.md", "--open-critical", "0") == 0
    assert run(alice, "dod", "FW-0002", "--remove", "上板 loopback 驗證") == 0
    assert run(alice, "evidence", "FW-0002", "hil", "--ref", "harness/evidence/FW-0002/loopback.log") == 0
    assert run(alice, "move", "FW-0002", "done") == 1
    commit_all(alice, "FW-0002 check、hil evidence")
    git(alice, "pull", "--no-edit", "origin", "main")
    git(alice, "push", "origin", "main")

    # 5. bob review：先有 critical，修正後重審歸零，alice 才能轉 done
    git(bob, "pull", "--no-edit", "origin", "main")
    assert run(bob, "evidence", "FW-0002", "review", "--ref", "harness/reviews/FW-0002_bob_2026-09-16.md", "--open-critical", "1") == 0
    assert run(bob, "evidence", "FW-0002", "review", "--ref", "harness/reviews/FW-0002_bob_2026-09-17.md", "--open-critical", "0") == 0
    commit_all(bob, "FW-0002 review evidence")
    git(bob, "push", "origin", "main")
    git(alice, "pull", "--no-edit", "origin", "main")
    assert run(alice, "move", "FW-0002", "done") == 0
    commit_all(alice, "FW-0002 完成")

    # 6. 全域檢查通過，索引帶出兩人的 commit evidence
    assert check_tickets(alice) == []
    entry = {t["id"]: t for t in build_index(alice)["tickets"]}["FW-0002"]
    authors = {c["by"]["email"] for c in entry["commits"]}
    assert authors == {"alice@example.com", "bob@example.com"}
    assert entry["status"] == "done"
```

- [ ] **Step 2：執行**

Run: `py -3 -m pytest tests/scripts/test_team_flow.py -v`
Expected: `1 passed`。若失敗，用 superpowers:systematic-debugging 找出是哪個模組的行為和 spec 第 5 節不符，修模組並補對應的單元測試。

- [ ] **Step 3：跑完整測試**

Run: `py -3 -m pytest`
Expected: `80 passed`

- [ ] **Step 4：Commit**

```bash
git add tests
git commit -m "test(scripts): 新增兩人協作整合測試"
```

---

## 完成條件

- `py -3 -m pytest` 全部通過（80 個測試）。
- `SCRIPTS/` 只有標準庫 import。驗證指令：`py -3 -c "import ast,sys,pathlib; mods={n.names[0].name.split('.')[0] if isinstance(n,ast.Import) else (n.module or '').split('.')[0] for p in pathlib.Path(sys.argv[1]).glob('*.py') for n in ast.walk(ast.parse(p.read_text(encoding='utf-8'))) if isinstance(n,(ast.Import,ast.ImportFrom))}; local={p.stem for p in pathlib.Path(sys.argv[1]).glob('*.py')}; print(sorted(m for m in mods-local if m not in sys.stdlib_module_names))" plugins/fw-c-harness/skills/fw-harness-init/templates/harness/scripts`，預期輸出 `[]`。
- 沒有任何子命令能指定身分。

## 留給後續計畫

- 計畫 2：`check.py` 呼叫 `ticket_check.check_tickets`；`check.py --record <票號>` 以 `make_evidence("check", ..., passed=<結果>)` 寫入 check evidence；`commit-msg` hook 使用 `index.TICKET_REF_RE` 並確認票檔存在；`post-commit` 與 `post-merge` 呼叫 `index.main`，`post-merge` 偵測重複票號時提示 `ticket.py renumber`。
- 計畫 3：範本的 `.gitignore` 要加入 `feature_list.json`；`people.json` 範本。
- 計畫 4：`fw-ticket` skill 只透過 `ticket.py` 寫入，並拒絕替使用者轉 `done`；`fw-done` 需要的 progress 檔名 `<YYYY-MM-DD>_<slug>_<n>.md`（`n` 取當天同一人已有檔案數 + 1）與 handoff 路徑，由計畫 4 以 `identity.slug_for` 實作（spec 第 5.6 節）。
