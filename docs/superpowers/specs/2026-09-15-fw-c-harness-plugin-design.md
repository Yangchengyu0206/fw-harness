# fw-c-harness plugin 設計

- 日期：2026-09-15
- 作者：Yang cheng
- 狀態：草稿，待審

## 1. 目標

做一個 plugin，FW 團隊成員裝一次就同時拿到：

1. **Harness**：由 skill 產生到各自的 C 韌體 repo（入口檔、狀態檔、驗證閘門、git hooks、架構文件）。
2. **Skills**：開工、選票、寫碼、review、除錯、收尾等流程。

需求限制：

- 同事以 **Claude Code** 和 **GitHub Copilot** 為主，兩者都要能用。
- **多人協作同一份程式碼**：每一筆狀態變更都要帶上個人身分，並且不能因為多人並行而撞號或頻繁合併衝突。
- 預設工具鏈：GCC（arm-none-eabi）+ CMake、host gcc 跑 Unity 測試、cppcheck、clang-format。
- MISRA C:2012 **只當參考標準**：預設 advisory，可逐專案調整。

### 非目標

- 不支援 IAR/Keil、Zephyr、ESP-IDF 的內建設定（只在文件中提供替換指引）。
- 不自動燒錄正式板，不做 HIL 測試框架本身。
- 不整合 GitHub Issues，票存在 repo 內。
- 不附 MISRA 規則原文（有版權），只列規則編號和我們自己寫的一行摘要。

## 2. 發佈方式

一個 git repo 同時作為兩種工具的 marketplace：

```
fw-harness/
├─ .claude-plugin/marketplace.json     Claude Code：/plugin marketplace add <repo>
├─ .github/plugin/marketplace.json     Copilot：copilot plugin marketplace add <repo>
├─ plugins/fw-c-harness/
│  ├─ .claude-plugin/plugin.json
│  ├─ .github/plugin/plugin.json       列出同一批 skills
│  ├─ skills/                          見第 3 節
│  └─ README.md                        兩種工具的安裝與更新方式
├─ tests/                              plugin 自身的測試（見第 9 節）
└─ docs/superpowers/specs/
```

兩份 marketplace manifest 指向同一個 `plugins/fw-c-harness` 目錄，skills 只維護一份。

`fw-harness-init` 會在 FW repo 寫入 `extraKnownMarketplaces`（`.claude/settings.json` 與 `.github/copilot-settings.json`），同事 clone 之後就會被提示安裝這個 plugin。

**分工原則**：plugin 只放「跟著 plugin 版本更新的東西」（skills 和範本）。規則、狀態、閘門腳本、git hooks **全部落地到 FW repo 並進 git**，這樣沒裝 plugin 的人、手動 commit 的人和 CI 都走同一套規則。

## 3. Skills（12 個）

所有 skill 使用 `SKILL.md` 格式。frontmatter 的 `description` 同時寫英文和中文關鍵字，方便兩種工具觸發。內文使用繁體中文。

### 3.1 Harness 生命週期

| Skill | 作用 |
|---|---|
| `fw-harness-init` | 在 FW repo 產生整套 harness（第 4 節），包含依實際目錄產生的 ARCHITECTURE.md（第 6 節）。會先偵測既有檔案，不覆寫。 |
| `fw-harness-upgrade` | plugin 更新後，比對 repo 內的 `harness/.harness-version`：**受管檔**（scripts、hooks）直接更新；**團隊自有檔**（AGENTS.md、CLAUDE.md 的事故與規則段落）只顯示 diff 並逐項詢問。 |
| `fw-architecture-sync` | `arch_check` 失敗時使用：替新資料夾產生 ARCHITECTURE.md 草稿、更新觀察到的依賴。核准規則仍需人確認。 |

### 3.2 工作循環

| Skill | 作用 |
|---|---|
| `fw-session-start` | 開工六步：確認位置與 git 身分 → 跑 `init` → 讀自己的 handoff → 讀最近的 progress 與 `git log` → 列出可選的票（自己 active 的票優先）→ **與使用者確認選哪張票之後才能寫碼**。 |
| `fw-ticket` | 開票、認領、轉狀態、加 evidence。所有寫入都透過 `harness/scripts/ticket.py`，自動填入身分與時間，並執行狀態轉換檢查（第 5.4 節）。 |
| `fw-hil-verify` | 補 `verifying` 票的上板欠款：引導燒錄與串口擷取，把 log 存到 `harness/evidence/`，並寫入 `kind: hil` 的 evidence。燒錄由人執行，skill 只給指令與收證據。 |
| `fw-done` | 收尾五步：看 diff → 更新 `harness/handoff/<人>.md` → 新增一輪 `harness/progress/` → 更新票 → 產生繁中 commit 訊息（含票號）。**只顯示訊息，不執行 commit。** |

### 3.3 寫碼與 review

參考 awesome-copilot（MIT 授權）改寫，檔頭註明出處。

| Skill | 來源 | 作用 |
|---|---|---|
| `fw-c-implement` | `agents/expert-embedded-c-engineer.agent.md` | 讀票與相關 ARCHITECTURE.md → 先寫 Unity 測試並確認失敗 → 實作 → 跑 `check` → 寫入 evidence。references：`embedded-c-rules.md`（fixed-width 型別、const、`static`、macro、錯誤回傳碼）、`isr-concurrency.md`（volatile、臨界區、ISR 內禁止的事）、`memory-budget.md`（動態配置限制、stack、map 預算）、`module-template.md`（.h/.c 樣板）。 |
| `fw-c-review` | `instructions/code-review-generic.instructions.md`（分級與格式）、`skills/security-review/SKILL.md`（流程與自我驗證） | 範圍 → 分層違規 → C 正確性 → 並行/ISR → 資源 → FW 安全（未驗證長度、除錯口、寫死金鑰）→ 測試 → **自我驗證每條 finding** → 報告。報告格式見第 7 節。 |
| `fw-c-test-gap` | `skills/test-gap-audit/SKILL.md` | 只讀的測試缺口稽核，P0–P3。沿用原 skill 的證據標準（引用的行必須真的含有所指的內容；數字要附產生它的指令）。 |
| `fw-c-debug` | `agents/debug.agent.md` | 先重現再修。加上 HardFault 暫存器解讀、stack overflow、ISR 競態、`git bisect`。修好後必須補回歸測試。 |
| `fw-misra-deviation` | `expert-embedded-c-engineer` 的 deviation 段落 | 需要偏離 MISRA 規則時，產生 `docs/deviations/DEV-NNNN.md`（規則編號、理由、風險、範圍、核准人），核准人不能是作者本人。 |

## 4. 落地到 FW repo 的 harness

```
<fw-repo>/
├─ AGENTS.md                         共同入口（Copilot、Claude 等工具都讀）
├─ CLAUDE.md                         權威手冊
├─ ARCHITECTURE.md                   頂層地圖（第 6 節）
├─ <各程式碼資料夾>/ARCHITECTURE.md   依實際目錄產生
├─ .github/
│  ├─ copilot-instructions.md        一行：先讀 AGENTS.md
│  └─ instructions/c-fw-review.instructions.md   applyTo: "**/*.{c,h}"，供 GitHub 網頁上的 Copilot PR review 使用
├─ .claude/settings.json             extraKnownMarketplaces
├─ .githooks/                        commit-msg、post-commit、post-merge
├─ Makefile                          check 目標：薄包裝
├─ init.sh / init.ps1                薄包裝
├─ .clang-format
├─ docs/
│  ├─ references/*.llms.txt          MCU SDK / RTOS 筆記
│  └─ deviations/                    MISRA deviation 紀錄
└─ harness/
   ├─ .harness-version
   ├─ config.json                    工具鏈路徑、CMake preset、size 預算、cppcheck 參數
   ├─ architecture.json              核准的分層與依賴規則＋grandfather 清單
   ├─ review-policy.json             第 7 節
   ├─ people.json                    選填：email → slug / 顯示名稱
   ├─ cppcheck-suppressions.txt      棘輪：只能縮短
   ├─ tickets/FW-NNNN.json           一票一檔
   ├─ progress/<YYYY-MM-DD>_<slug>_<n>.md
   ├─ handoff/<slug>.md
   ├─ reviews/FW-NNNN_<slug>_<YYYY-MM-DD>.md
   ├─ evidence/                      HIL log 等大型證據
   └─ scripts/                       Python 3，閘門與狀態邏輯的唯一實作
```

### 4.1 入口：AGENTS.md → CLAUDE.md

**AGENTS.md**（簡短）：

- 能改哪些目錄。vendor 和工具產生的程式碼由 ARCHITECTURE.md 標示為不可改。
- 禁止事項：`git clean`、`git push`、`--no-verify`；修改 linker script、startup 檔、`harness/architecture.json` 的核准規則、`cppcheck-suppressions.txt`（只能刪不能加）；自行把票標成 `done`。
- Windows 注意事項：Python 啟動器（`py -3` 與 Store stub）、cp950 編碼（腳本一律用 UTF-8 讀寫）、Git Bash 與 PowerShell 的差異。
- 指向 CLAUDE.md。

**CLAUDE.md** 四塊：

1. **開工流程**：同 `fw-session-start` 六步。
2. **工作規則**：每人一次一票；合併前在合併後的樹上跑 `check`；新 C 檔必須加進 CMake，不能只放在磁碟上；不改編譯旗標。
3. **Definition of Done**：見第 5.4 節。
4. **設計決策的「為什麼」**：每個旗標、每個閘門附理由。範本附一個「事故」欄位格式（日期、發生什麼、長出哪條規則），初始留空由團隊累積。

### 4.2 驗證閘門

**唯一實作**是 `harness/scripts/check.py`，`Makefile`、`init.sh`、`init.ps1` 都只是呼叫它的薄包裝，而且**不得另加旗標**。

`init`（每個 session 開頭跑，只驗證、不安裝）：

1. Python 3 可用
2. `git config user.name/email` 已設定（沒設就失敗，因為身分是協作的基礎）
3. `core.hooksPath` 指向 `.githooks`
4. 工具存在並記錄版本：`arm-none-eabi-gcc`、`gcc`、`cmake`、`cppcheck`、`clang-format`
5. `harness/` 結構與 JSON schema 正確
6. 跑一次 `check`

log 寫到 `.verify_logs/<時間戳>.log`（gitignored）。

`check` 依序執行，任一步失敗就停：

1. `clang-format --dry-run --Werror`（只檢查變更過的檔案）
2. `cppcheck`，使用 `harness/cppcheck-suppressions.txt`
3. `arch_check`（第 6.3 節）
4. `ticket_check`（第 5.5 節）
5. 交叉編譯（`target` preset，`-Wall -Wextra -Werror`）
6. host 端 Unity 測試（`host-test` preset）
7. size 預算：讀 map 檔，flash/RAM 超過 `config.json` 設定的預算就失敗

**棘輪**：`cppcheck-suppressions.txt` 與 `architecture.json` 的 grandfather 清單只能縮短。前者由第 2 步、後者由第 3 步比對 `origin/main`，發現新增項目就失敗。

### 4.3 git hooks（取代 Claude 專屬的 PostToolUse hook）

使用 git hooks 的原因：人手動 commit、Copilot commit、Claude commit，行為都一樣。

| Hook | 作用 |
|---|---|
| `commit-msg` | 訊息必須含 `FW-NNNN`，或以 `harness:` / `chore:` 開頭；票號必須存在於 `harness/tickets/`。 |
| `post-commit` | 重新產生 `feature_list.json` 索引。**不修改任何被追蹤的檔案**，所以 commit 後工作樹保持乾淨。 |
| `post-merge` | 重新產生索引；如果合併後出現重複票號，就提示執行 `ticket.py renumber`。 |

**commit 類 evidence 不寫入票檔**，而是由 `git log --grep FW-NNNN` 在產生索引時動態算出。原本 harness 是由 hook 寫入 evidence，多人時會造成工作樹變髒和合併衝突，所以改成動態計算。票檔只存無法從 git 推導的 evidence（check、hil、review）。

## 5. 狀態與身分

### 5.1 身分

- 來源：`git config user.name` 與 `user.email`，不另外設帳號系統。
- slug（用於檔名）：取 email 的 local-part；若含 `+`，取 `+` 之後的部分；轉小寫，非 `[a-z0-9-]` 的字元換成 `-`。可以用 `harness/people.json` 覆寫。
- 所有寫入狀態的腳本都自動填入身分，skill 不能自行指定別人的身分。

### 5.2 票檔 `harness/tickets/FW-NNNN.json`

```json
{
  "id": "FW-0042",
  "title": "UART 驅動支援 DMA 接收",
  "area": "drivers/uart",
  "status": "active",
  "priority": 2,
  "created_by": {"name": "Yang cheng", "email": "..."},
  "created_at": "2026-09-15T10:02:00+08:00",
  "assignee": {"name": "Yang cheng", "email": "..."},
  "user_visible_behavior": "115200 baud 下連續接收 4KB 不掉 byte",
  "verification_steps": ["host 測試：ring buffer 溢位回報錯誤碼", "上板：loopback 4KB 比對 CRC"],
  "dod_pending": ["上板 loopback 驗證"],
  "evidence": [
    {"kind": "check", "by": {...}, "at": "...", "commit": "a1b2c3d", "summary": "check 7/7 通過"},
    {"kind": "review", "by": {...}, "at": "...", "ref": "harness/reviews/FW-0042_alice_2026-09-16.md", "open_critical": 0},
    {"kind": "hil", "by": {...}, "at": "...", "ref": "harness/evidence/FW-0042/loopback.log"}
  ],
  "history": [
    {"by": {...}, "at": "...", "from": "next", "to": "active", "note": ""}
  ],
  "blocked_reason": null,
  "notes": ""
}
```

索引 `feature_list.json` 由腳本產生並 **gitignored**，內容是所有票的摘要加上動態算出的 commit evidence，供 agent 快速瀏覽。

### 5.3 票號分配

- 新票號為 `max(本地 tickets, origin/main tickets) + 1`，腳本會先 `git fetch origin main`（離線時用本地最大號並警告）。
- 票號**只有在開票 commit 合入 main 之後才算佔住**。
- 撞號時，兩個分支都新增了 `harness/tickets/FW-0096.json`，合併時 git 會直接回報 add/add 衝突，不會悄悄覆蓋。`ticket.py renumber FW-0096` 會把後進者改成下一個空號，並提示修改分支上引用舊號的 commit 訊息。

### 5.4 狀態機與 Definition of Done

```
backlog → next → active → verifying → done
             ↘      ↘         ↘
               blocked（任何狀態都可進入，須填 blocked_reason；解除後回到原狀態）
```

| 轉換 | 條件（由 `ticket.py` 檢查） |
|---|---|
| → `active` | 執行者成為 assignee；該 assignee 沒有其他 `active` 的票 |
| `active` → `verifying` | 至少一筆 `kind: check`，且其 commit 是目前 HEAD 或 HEAD 的祖先 |
| `verifying` → `done` | `dod_pending` 已清空；有 `kind: hil`（若 `verification_steps` 含上板步驟）；有 `kind: review`，其 `by` ≠ assignee 且 `open_critical == 0` |

「寫完」與「完成」分開：程式碼寫完、check 通過，但上板或 review 還沒做，就停在 `verifying`，並把欠的事列進 `dod_pending`。

**agent 不能把票轉到 `done`**：AGENTS.md 明文禁止，`fw-ticket` skill 也會拒絕。機械上，`ticket_check` 能驗證的是「done 的票有沒有 hil 與非本人 review evidence」，但無法證明 evidence 是真人產生的。這個限制寫進 CLAUDE.md，最終把關靠 PR review。

### 5.5 `ticket_check`（在 `check` 中執行）

- 所有票檔符合 schema，票號不重複且與檔名一致
- 每個 assignee 最多一張 `active`
- `done` 的票滿足第 5.4 節的條件
- 每個 `blocked` 的票都有 `blocked_reason`

### 5.6 progress 與 handoff

- `harness/progress/<YYYY-MM-DD>_<slug>_<n>.md`：一個 session 一檔，檔頭有作者、票號、起訖 commit，內文附 `check` 摘要當證據。一人一檔，所以不會衝突。
- `harness/handoff/<slug>.md`：每人一份，每次覆寫。內容是目標、完成事項、blockers、建議下一步。
- 接手別人的票時，`fw-session-start` 會一併讀原 assignee 的 handoff。

## 6. ARCHITECTURE.md 自動產生與同步

### 6.1 產生（`fw-harness-init`、`fw-architecture-sync`）

1. **掃描**：底下有 `.c`/`.h` 的資料夾都是候選。排除 `build/`、`out/`、`Debug/`、`Release/`、`.git/` 與 `.gitignore` 內的項目。預設深度兩層；某個資料夾的 C 檔超過 `config.json` 的門檻（預設 30 個）且子資料夾職責分明時，再往下切。
2. **分類**：
   - **自有程式碼**：產生完整版
   - **vendor / 工具產生**：依名稱（`third_party`、`vendor`、`CMSIS`、`Drivers/STM32*` 等）或檔頭的 "generated" 字樣判斷；產生簡短版，寫明「不可修改、來源與版本、升級方式」
   - **測試**：寫明框架、命名慣例、執行方式
3. **依賴分析**：解析 `#include "..."`，以 CMake 的 include 路徑對應到資料夾，建立資料夾依賴圖，列出循環依賴與疑似反向依賴。
4. **草稿內容**：職責（從檔名、函式名、既有註解推測，標明為推測）、進入點、**觀察到的依賴**、**核准的依賴（空白，待人確認）**、ISR 與記憶體注意事項。
5. **確認**：init 最後列出推測的分層順序，請使用者逐項確認或調整，確認後寫入 `harness/architecture.json`。目前已存在的違規依賴放進 grandfather 清單。

### 6.2 真相來源

`harness/architecture.json` 是核准規則的唯一來源；ARCHITECTURE.md 內的「核准依賴」表格由它產生，並以標記區塊包起來，腳本只改寫標記區塊內的內容。其他段落是人寫的說明，腳本不動。

### 6.3 `arch_check`

| 狀況 | 結果 |
|---|---|
| 含 C 檔的資料夾沒有 ARCHITECTURE.md，也沒有列在 `architecture.json` | 失敗 |
| `#include` 違反核准規則，且不在 grandfather 清單 | 失敗 |
| grandfather 清單比 `origin/main` 多出項目 | 失敗 |
| ARCHITECTURE.md 的標記區塊與 json 不一致 | 失敗（提示重新產生） |
| 資料夾已刪除但仍在 json 或文件中 | 警告 |

## 7. Review 政策

`harness/review-policy.json`：

```json
{
  "misra": {"standard": "MISRA C:2012", "mode": "advisory"},
  "block_on": ["critical"],
  "forbid_self_review": true,
  "language": "zh-TW"
}
```

`misra.mode` 可設為 `off`、`advisory`（預設）、`required`：

- `advisory`：MISRA 問題最高列為 🟢，不擋合併
- `required`：違反 required 規則且沒有 deviation 紀錄時列為 🔴

分級：

- 🔴 **Critical（擋合併）**：未定義行為、陣列或指標越界、整數溢位造成錯誤、ISR 與主迴圈共用資料沒保護、該加 `volatile` 卻沒加、錯誤回傳碼被忽略、未驗證的外部長度、除錯口或寫死金鑰、違反核准分層（非 grandfather）
- 🟡 **Important**：新邏輯缺測試、資源未釋放、阻塞呼叫出現在時間敏感路徑、magic number 牽涉暫存器位址
- 🟢 **Suggestion**：命名、註解、可讀性、MISRA advisory

報告格式（`harness/reviews/FW-NNNN_<reviewer-slug>_<日期>.md`）：檔頭記錄 reviewer 身分、票號、審查的 commit 範圍；先放分級統計表；每條 finding 含嚴重度、`path:line`、問題、為什麼重要、建議修法、信心度。每條 finding 都要經過自我驗證（重讀程式碼，確認不是上游已處理的誤判）。patch 只提議，不自動套用。

review 完成後，`fw-ticket` 寫入 `kind: review` 的 evidence，`open_critical` 取自報告。作者修正後重跑 review，產生新報告與新 evidence，以最新一筆為準。

`.github/instructions/c-fw-review.instructions.md` 是同一份分級與 checklist 的精簡版，供 GitHub 網頁上的 Copilot PR review 使用；它由 `fw-harness-init` 從同一份來源產生，確保兩者一致。

## 8. 錯誤處理原則

- 所有腳本：失敗時非 0 結束，訊息寫明「哪個檢查、哪個檔案、怎麼修」。
- 讀寫一律 UTF-8；Windows 下不依賴 `cp950`。
- 寫入票檔採「讀取 → 修改 → 寫入暫存檔 → rename」，避免寫到一半損毀。
- 離線時（`git fetch` 失敗）：票號分配與棘輪比對改用本地資料並明確警告，不靜默略過。
- `fw-harness-init` 遇到既有同名檔案：不覆寫，改產生 `<檔名>.harness-proposed` 並列出差異。

## 9. 測試 plugin 本身

- `harness/scripts/` 的 Python 以 pytest 測試：身分 slug、票號分配與 renumber、狀態轉換檢查、include 依賴解析、棘輪比對、索引產生。
- `tests/fixtures/sample-fw/`：一個小型 CMake C 專案（含一個 vendor 資料夾、一個故意的反向依賴、Unity 測試）。端對端測試會在暫存目錄複製它，執行 init 產生流程，並驗證 `check` 的通過與失敗情境。
- 以兩個不同 git 身分模擬並行：同時開票撞號、各自 active、互相 review，驗證第 5 節規則。
- Skills 無法自動測試，改用人工檢查清單：在 Claude Code 與 Copilot 各跑一次完整循環（init → session-start → ticket → implement → review → done）。

## 10. 推行步驟

1. 在 `sample-fw` 上完成 plugin 並通過第 9 節測試。
2. 找一個真實 FW repo 試點，由一到兩人使用兩週，累積 CLAUDE.md 的第一批事故規則。
3. 依試點回饋調整後，推到公司 GitHub，公告安裝方式。
