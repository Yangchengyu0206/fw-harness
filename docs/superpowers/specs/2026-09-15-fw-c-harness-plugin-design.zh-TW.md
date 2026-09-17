# fw-c-harness plugin 設計

- 日期：2026-09-15
- 作者：Yang cheng
- 狀態：草稿，待審
- 翻譯：本文為 [English](2026-09-15-fw-c-harness-plugin-design.md) 的繁體中文版，兩者有出入時以英文版為準

## 1. 目標

一個開源 plugin，韌體團隊的每位成員裝一次就同時拿到：

1. **Harness**：由 skill 產生到各自的 C 韌體 repo，包含入口文件、狀態檔、驗證閘門、git hooks 與架構文件。
2. **Skills**：涵蓋整個工作循環，包括開工、選票、實作、review、除錯與收尾。

限制：

- 必須同時支援 **Claude Code** 與 **GitHub Copilot**。
- **多人協作同一份程式碼**：每一筆狀態變更都記錄是誰做的，並行工作不能造成票號衝突或頻繁的合併衝突。
- 預設工具鏈：GCC（`arm-none-eabi`）加 CMake、host `gcc` 跑 Unity 測試、`cppcheck`、`clang-format`。
- MISRA C:2012 **只當參考標準**：預設 advisory，可逐專案調整。

### 非目標

- 不內建 IAR/Keil、Zephyr、ESP-IDF 的設定（文件只提供替換指引）。
- 不自動燒錄正式板，也不提供 HIL 測試框架。
- 不整合 GitHub Issues，票存在 repo 內。
- 不附 MISRA 規則原文（有版權），只列規則編號和我們自己寫的一行摘要。

### 語言與授權

- 程式碼、註解、CLI 與錯誤訊息、skills、文件一律使用英文。spec 與 README 另附繁體中文翻譯（`*.zh-TW.md`），以英文版為準。
- 團隊的 harness 產生給人看的內容（review 報告、`fw-done` 草擬的 commit 訊息）依 `harness/config.json` 的 `language` 決定，預設 `en`。
- 授權：MIT。改寫自 [awesome-copilot](https://github.com/github/awesome-copilot) 與 [mattpocock/skills](https://github.com/mattpocock/skills)（皆為 MIT）的內容，在檔頭與 `THIRD_PARTY_NOTICES.md` 註明出處。

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
├─ docs/skills/                        每個 skill 一頁給人看的說明
├─ tests/                              plugin 自身的測試（第 9 節）
├─ LICENSE
├─ THIRD_PARTY_NOTICES.md
├─ README.md / README.zh-TW.md
└─ docs/superpowers/specs/
```

兩份 marketplace manifest 指向同一個 `plugins/fw-c-harness` 目錄，skills 只維護一份。

`fw-harness-init` 會在韌體 repo 的 `.claude/settings.json` 寫入 `extraKnownMarketplaces` 與 `enabledPlugins`。VS Code 上的 GitHub Copilot、Claude Code、Copilot CLI 都會讀這個檔案，所以成員 clone 之後會被提示安裝 plugin；但沒有一個工具會自動安裝。

**分工原則**：plugin 只放應該跟著 plugin 版本更新的東西（skills 和範本）。規則、狀態、閘門腳本與 git hooks **寫進韌體 repo 並 commit**，所以沒裝 plugin 的人、手動 commit 的人和 CI 都遵守同一套規則。

## 3. Skills（14 個）

所有 skill 使用 `SKILL.md` 格式，並遵守第 3.4 節的寫法規範。

### 3.1 Harness 生命週期

| Skill | 觸發 | 作用 |
|---|---|---|
| `fw-harness-init` | 人 | 在韌體 repo 產生整套 harness（第 4 節），包含依實際目錄產生的 ARCHITECTURE.md（第 6 節）。會先偵測既有檔案，絕不覆寫。 |
| `fw-harness-upgrade` | 人 | plugin 更新後比對 `harness/.harness-version`。**受管檔**（scripts、hooks）直接更新；**團隊自有檔**（AGENTS.md、CLAUDE.md 的事故與規則段落）顯示 diff 並逐項詢問。 |
| `fw-architecture-sync` | agent | `arch_check` 失敗時使用：替新資料夾草擬 ARCHITECTURE.md，並更新觀察到的依賴。核准規則仍需要人確認。 |

### 3.2 工作循環

| Skill | 觸發 | 作用 |
|---|---|---|
| `fw-session-start` | 人 | 六步：確認位置與 git 身分 → 跑 `init` → 讀自己的 handoff → 讀最近的 progress 與 `git log` → 列出候選票（自己 active 的票優先）→ **寫碼前先與使用者確認要做哪張票**。 |
| `fw-ticket` | agent | 開票、認領、轉狀態、加 evidence。所有寫入都透過 `harness/scripts/ticket.py`，由它自動填入身分與時間，並執行轉換規則（第 5.4 節）。 |
| `fw-hil-verify` | 人 | 補上 `verifying` 票欠的上板驗證：引導燒錄與串口擷取，把 log 存到 `harness/evidence/`，並記錄 `kind: hil` evidence。燒錄由人執行，skill 提供指令並收集證據。 |
| `fw-done` | 人 | 五步：看 diff → 更新 `harness/handoff/<slug>.md` → 在 `harness/progress/` 新增一輪 → 更新票 → 依設定的語言草擬含票號的 commit 訊息。**只顯示訊息，commit 由使用者自己執行。** |

### 3.3 實作與 review

改寫自 awesome-copilot（MIT），每個檔案註明出處。

| Skill | 觸發 | 來源 | 作用 |
|---|---|---|---|
| `fw-c-implement` | agent | `agents/expert-embedded-c-engineer.agent.md` | 讀票與相關 ARCHITECTURE.md → 寫 Unity 測試並確認它失敗 → 實作 → 跑 `check` → 記錄 evidence。references：`embedded-c-rules.md`（fixed-width 型別、`const`、`static`、macro、錯誤回傳碼）、`isr-concurrency.md`（`volatile`、臨界區、ISR 內要避免的事）、`memory-budget.md`（動態配置限制、stack、map 預算）、`module-template.md`（`.h`/`.c` 樣板）。 |
| `fw-c-review` | agent | `instructions/code-review-generic.instructions.md`（分級與格式）、`skills/security-review/SKILL.md`（自我驗證）、mattpocock `code-review`（兩軸） | 兩軸 review，每軸各用一個 sub-agent，並列回報（第 7 節）。 |
| `fw-review-respond` | agent | `skills/receiving-code-review`（obra/superpowers） | 作者這一側的審查處理：每條意見先對照程式碼查證，再修正、附證據婉拒，或交給使用者決定；一次修一條並跑 host 測試；在報告後附上作者回覆表；交回重審。不記錄審查證據，因為由負責人記錄等於自我審查。 |
| `fw-c-test-gap` | agent | `skills/test-gap-audit/SKILL.md` | 只讀的測試缺口稽核，嚴重度 P0 到 P3。沿用來源的證據標準：引用的那一行必須真的含有所指的內容，每個數字都附上產生它的指令。 |
| `fw-c-debug` | agent | `skills/engineering/diagnosing-bugs`（mattpocock/skills），並參考 `skills/bug-reproduction-brief` 與 `agents/gem-debugger.agent.md` | 先建立能穩定重現的驗證迴圈再推測原因，列出可推翻的假設並逐一證實。加上 HardFault 暫存器解讀、stack overflow、ISR 競態、`git bisect`，以及需要人手操作板子時用的腳本。每個修正都附回歸測試。 |
| `fw-misra-deviation` | agent | `expert-embedded-c-engineer` 的 deviation 段落 | 必須偏離 MISRA 規則時，產生 `docs/deviations/DEV-NNNN.md`（規則編號、理由、風險、範圍、核准人）。核准人必須是作者以外的人。 |
| `fw-guide` | 人 | mattpocock `ask-matt`（router 模式） | Router：列出其他所有 skill 以及各自的使用時機，讓人只需要記住一個 skill，而不是十四個。 |

### 3.4 Skill 寫法規範

依據 mattpocock/skills 的 `writing-for-agents`：

- **觸發方式要刻意選擇。** 只由人觸發的 skill 設 `disable-model-invocation: true`，不佔 context；它的 `description` 是一行給人看的摘要。可由 agent 觸發的 skill 保留給模型看的 `description`，把觸發詞放在最前面，每種不同情境一個觸發詞。只有當 agent 或其他 skill 必須自己叫出它時，才選 agent 觸發。
- **SKILL.md 保持短，參考資料揭露式放置。** `SKILL.md` 放步驟，以及每個分支都需要的參考資料。只有部分分支需要的內容，移到同資料夾的其他檔案，並用指標寫明何時要讀。
- **每一步都以完成條件結束**，而且是 agent 能檢查的條件，措辭要要求徹底完成（例如「每個改動過的函式都已處理」）。
- **正面措辭。** 寫出目標行為。禁止事項只用在無法用正面方式表達的硬性護欄，並同時寫出正面目標。
- **單一真相來源。** 每條規則只存在一個地方；skill 指向 harness 檔案（例如 `harness/review-policy.json`），不重抄內容。
- 所有文字**不使用 em-dash（—）**。
- 每個主要 skill 在 `docs/skills/<skill>.md` 有一頁說明，包含 **What it does**、**When to reach for it**、**Common questions**、**It's working if** 四節。

## 4. 寫進韌體 repo 的 harness

```
<fw-repo>/
├─ AGENTS.md                         共同入口（Copilot、Claude 等工具都會讀）
├─ CLAUDE.md                         權威手冊
├─ ARCHITECTURE.md                   頂層地圖（第 6 節）
├─ <各程式碼資料夾>/ARCHITECTURE.md   依實際目錄產生
├─ .github/
│  ├─ copilot-instructions.md        一行：先讀 AGENTS.md
│  └─ instructions/c-fw-review.instructions.md   applyTo: "**/*.{c,h}"，供 GitHub 上的 Copilot PR review 使用
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
   ├─ config.json                    工具鏈路徑、CMake preset、size 預算、cppcheck 參數、language
   ├─ architecture.json              核准的分層與依賴規則，以及 grandfather 清單
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

- 可以修改哪些目錄。vendor 與工具產生的程式碼由各自的 ARCHITECTURE.md 標示為唯讀。
- 硬性護欄：`git clean`、`git push`、`--no-verify`；修改 linker script、startup 檔、`harness/architecture.json` 的核准規則，或在 `cppcheck-suppressions.txt` 新增項目（只能刪除）；把票標成 `done`。
- Windows 注意事項：Python 啟動器（`py -3` 與 Microsoft Store stub 的差別）、cp950 等舊主控台編碼（腳本一律以 UTF-8 讀寫）、Git Bash 與 PowerShell 的差異。
- 指向 CLAUDE.md。

**CLAUDE.md** 分四塊：

1. **開工流程**：`fw-session-start` 的六步。
2. **工作規則**：每人一次一張 active 票；合併前在合併後的樹上跑 `check`；新的 C 檔要加進 CMake，不能只放在磁碟上；編譯旗標維持原樣。
3. **Definition of Done**：第 5.4 節。
4. **設計決策的理由**：每個旗標、每個閘門都附理由。範本附一個事故紀錄格式（日期、發生什麼事、長出哪條規則），留空由團隊填寫。

### 4.2 驗證閘門

**唯一實作**是 `harness/scripts/check.py`。`Makefile`、`init.sh`、`init.ps1` 都只是它的薄包裝，**不另加任何旗標**。

`init`（每個 session 開頭執行；只驗證、不安裝）：

1. Python 3 可用
2. `git config user.name/email` 已設定（沒設就失敗，因為身分是協作的基礎）
3. `core.hooksPath` 指向 `.githooks`
4. 工具存在並記錄版本：`arm-none-eabi-gcc`、`gcc`、`cmake`、`cppcheck`、`clang-format`
5. `harness/` 結構與 JSON schema 正確
6. 執行一次 `check`

log 寫到 `.verify_logs/<時間戳>.log`（gitignored）。

`check` 依序執行，遇到第一個失敗就停：

1. `clang-format --dry-run --Werror`，只檢查變更過的 C 檔：與 `origin/main` 的 merge base 相比有差異的檔案（沒有 `origin/main` 時與 HEAD 比），加上未追蹤的檔案，並略過 vendor 與工具產生的模組
2. `cppcheck`，使用 `harness/cppcheck-suppressions.txt`
3. `arch_check`（第 6.3 節）
4. `ticket_check`（第 5.5 節）
5. 交叉編譯（`target` preset，`-Wall -Wextra -Werror`）
6. host 端 Unity 測試（`host-test` preset）
7. size 預算：對 ELF 執行 size 工具（例如 `arm-none-eabi-size`）並讀取 Berkeley 格式輸出；flash 為 `text + data`，RAM 為 `data + bss`，任一項超過 `config.json` 的預算就失敗

每個指令都以 argv 陣列寫在 `harness/config.json`（`{python}` 會展開成目前執行的直譯器），團隊換工具不必改腳本。找不到工具時，該步驟失敗並提示安裝。

`check.py --record FW-NNNN` 會把結果寫成該票的 `kind: check` evidence，commit 為 HEAD，`passed` 依結果設定。工作樹不乾淨時拒絕執行，確保 evidence 描述的是真實存在的 commit。

**棘輪**：`cppcheck-suppressions.txt` 與 `architecture.json` 的 grandfather 清單只能縮短。前者由第 2 步、後者由第 3 步與 `origin/main` 比對，出現新增項目就失敗。沒有 `origin/main` 時兩者改與 HEAD 比對並發出警告。若清單在比對基準上還不存在，代表這次才引入，其中的項目不算新增。

### 4.3 git hooks（取代 Claude 專屬的 PostToolUse hook）

不論是人、Copilot 還是 Claude 做的 commit，git hooks 的行為都一樣。

| Hook | 作用 |
|---|---|
| `commit-msg` | 訊息必須含 `FW-NNNN`，或以 `harness:` / `chore:` 開頭；引用的票號都必須存在於 `harness/tickets/`。 |
| `post-commit` | 重新產生 `feature_list.json` 索引。**不修改任何被追蹤的檔案**，commit 後工作樹保持乾淨。 |
| `post-merge` | 重新產生索引並執行 `ticket_check`，票號衝突時提示使用 `ticket.py renumber`。 |

**commit 類 evidence 不寫進票檔。** 索引每次產生時從 `git log` 算出來。如果由 hook 寫入 evidence，多人 commit 時會讓工作樹變髒並造成合併衝突，所以改成動態計算。票檔只存 git 無法推導的 evidence（`check`、`hil`、`review`）。

## 5. 狀態與身分

### 5.1 身分

- 來源：`git config user.name` 與 `user.email`，沒有另外的帳號系統。
- slug（用於檔名）：取 email 的 local part；若含 `+`，取 `+` 之後的部分；轉小寫，`[a-z0-9-]` 以外的字元換成 `-`。可用 `harness/people.json` 覆寫。
- 所有寫入狀態的腳本都自行填入身分，沒有任何指令接受身分參數。

### 5.2 票檔 `harness/tickets/FW-NNNN.json`

```json
{
  "id": "FW-0042",
  "title": "UART driver supports DMA receive",
  "area": "drivers/uart",
  "status": "active",
  "priority": 2,
  "requires_hil": true,
  "created_by": {"name": "Alice Chen", "email": "alice@example.com"},
  "created_at": "2026-09-15T10:02:00+08:00",
  "assignee": {"name": "Alice Chen", "email": "alice@example.com"},
  "user_visible_behavior": "Receives 4 KB continuously at 115200 baud without dropping a byte",
  "verification_steps": ["host test: ring buffer overflow returns an error code", "on board: 4 KB loopback, CRC matches"],
  "dod_pending": ["on-board loopback verification"],
  "evidence": [
    {"kind": "check", "by": {...}, "at": "...", "commit": "a1b2c3d4e5", "summary": "check 7/7 passed", "passed": true},
    {"kind": "review", "by": {...}, "at": "...", "ref": "harness/reviews/FW-0042_bob_2026-09-16.md", "open_critical": 0},
    {"kind": "hil", "by": {...}, "at": "...", "ref": "harness/evidence/FW-0042/loopback.log"}
  ],
  "history": [
    {"by": {...}, "at": "...", "from": "next", "to": "active", "note": ""}
  ],
  "blocked_reason": null,
  "notes": ""
}
```

索引 `feature_list.json` 由腳本產生並 **gitignored**，內容是所有票的摘要加上動態算出的 commit evidence，讓 agent 能快速瀏覽工作佇列。

### 5.3 票號分配

- 新票號為 `max(本地票, origin/main 上的票) + 1`。腳本會先 `git fetch origin main`；離線時使用本地最大號並發出警告。
- **開票的 commit 合入 main 之後，票號才算佔住。**
- 兩個分支都新增了 `harness/tickets/FW-0096.json` 時，git 會在合併時回報 add/add 衝突，不會悄悄覆蓋。
- 合併前可執行 `ticket.py collisions`：fetch 後比對本地與 `origin/main` 上同號票檔的 `created_by` 和 `created_at`，不同即為撞號。`ticket.py renumber FW-0096` 會把本地那張改成下一個空號，並列出分支上訊息仍引用舊號的 commit。

### 5.4 狀態機與 Definition of Done

```
backlog → next → active → verifying → done
   ↘       ↘       ↘          ↘
     blocked（done 以外的狀態都可進入；須填 blocked_reason；解除後回到原狀態）
```

| 轉換 | 條件（由 `ticket.py` 檢查） |
|---|---|
| → `active` | 執行者成為 assignee；此人沒有其他 `active` 的票 |
| `active` → `verifying` | 至少一筆 `kind: check` 且 `passed: true`，其 commit 是 HEAD 或 HEAD 的祖先 |
| `verifying` → `done` | `dod_pending` 已清空；`requires_hil` 為 true 時要有 `kind: hil`；**最新一筆** `kind: review` 由 assignee 以外的人做，且 `open_critical == 0`；CLI 必須在互動式終端機（TTY）執行，並輸入票號確認 |

「寫完」與「完成」是兩回事：程式碼寫完、`check` 通過，但上板驗證或 review 還沒做時，票停在 `verifying`，欠的事列在 `dod_pending`。

**只有人能把票標成 `done`。** AGENTS.md 寫明這點，`fw-ticket` 不會代為執行，`ticket.py move <id> done` 也要求 stdin 是 TTY（agent 的 shell 通常不是）並輸入票號確認。機械上，`ticket_check` 能驗證 `done` 的票有 HIL evidence 和他人 review，但無法證明這些 evidence 是真人產生的。CLAUDE.md 寫明這個限制，最後的把關靠 PR review。

### 5.5 `ticket_check`（在 `check` 中執行）

- 所有票檔符合 schema；票號不重複且與檔名一致
- 每個 assignee 最多一張 `active` 的票
- 每張 `done` 的票都滿足第 5.4 節
- 每張 `blocked` 的票都有 `blocked_reason`

### 5.6 Progress 與 handoff

- `harness/progress/<YYYY-MM-DD>_<slug>_<n>.md`：一個 session 一個檔，檔頭有作者、票號、起訖 commit，內文附 `check` 摘要作為證據。每人每個 session 各自一檔，所以不會衝突。
- `harness/handoff/<slug>.md`：每人一份，每次覆寫：目標、完成事項、blockers、建議的下一步。
- 接手別人的票時，`fw-session-start` 會一併讀原 assignee 的 handoff。

## 6. ARCHITECTURE.md 的產生與同步

### 6.1 產生（`fw-harness-init`、`fw-architecture-sync`）

1. **掃描**：含 `.c`/`.h` 檔的資料夾都是候選。排除 `build/`、`out/`、`Debug/`、`Release/`、`.git/` 與 `.gitignore` 內的項目。預設深度兩層；只有當某個資料夾的 C 檔數超過 `config.json` 的門檻（預設 30）且子資料夾職責分明時，才往下切。
2. **分類**：
   - **自有程式碼**：完整版文件
   - **vendor 或工具產生的程式碼**：依名稱（`third_party`、`vendor`、`CMSIS`、`Drivers/STM32*` 等）或檔頭的 "generated" 字樣判斷；簡短版文件，寫明唯讀、來源與版本、升級方式
   - **測試**：框架、命名慣例、執行方式
3. **依賴分析**：解析 `#include "..."`，透過 CMake 的 include 路徑對應到資料夾，建立資料夾依賴圖，並列出循環依賴與疑似反向依賴。
4. **草稿內容**：職責（從檔名、函式名與既有註解推測，並標明為推測）、進入點、**觀察到的依賴**、**核准的依賴（空白，等待人確認）**、ISR 與記憶體注意事項。
5. **確認**：init 最後列出推測的分層順序，請使用者逐項確認或調整，再寫入 `harness/architecture.json`。現有的違規依賴放進 grandfather 清單。

### 6.2 真相來源

`harness/architecture.json` 是核准規則的唯一來源。每份 ARCHITECTURE.md 裡的核准依賴表格由它產生，放在標記區塊內；腳本只改寫標記區塊，人寫的段落不動。

```json
{
  "version": 1,
  "include_dirs": ["src/app", "src/drivers", "src/hal", "third_party/cmsis/Include"],
  "modules": {
    "src/app": {"kind": "owned", "allowed_deps": ["src/drivers"]},
    "src/drivers": {"kind": "owned", "allowed_deps": ["src/hal"]},
    "src/hal": {"kind": "owned", "allowed_deps": ["third_party/cmsis"]},
    "third_party/cmsis": {"kind": "vendor", "allowed_deps": []},
    "test": {"kind": "test", "allowed_deps": []}
  },
  "grandfathered": ["src/hal -> src/app"]
}
```

- 模組是 repo 內的相對資料夾；檔案屬於路徑最長且相符的模組。
- `kind` 為 `owned`、`vendor`、`generated` 或 `test`。只有 `owned` 模組會檢查 include；`vendor` 與 `generated` 模組是唯讀，format 步驟會略過。
- include（`"..."` 與 `<...>`）先以所在檔案的資料夾解析，再依序查 `include_dirs`。解析不到的 include 視為系統或工具鏈標頭，直接忽略。

### 6.3 `arch_check`

| 狀況 | 結果 |
|---|---|
| 含 C 檔的資料夾沒有 ARCHITECTURE.md，也沒有列在 `architecture.json` | 失敗 |
| `#include` 違反核准規則，且不在 grandfather 清單 | 失敗 |
| grandfather 清單有 `origin/main` 上沒有的項目 | 失敗 |
| ARCHITECTURE.md 的標記區塊與 json 不一致 | 失敗（提示重新產生） |
| 已刪除的資料夾仍列在 json 或文件中 | 警告 |

## 7. Review 政策

`harness/review-policy.json`：

```json
{
  "misra": {"standard": "MISRA C:2012", "mode": "advisory"},
  "block_on": ["critical"],
  "forbid_self_review": true
}
```

報告語言取自 `harness/config.json` 的 `language`。

`misra.mode` 可設為 `off`、`advisory`（預設）或 `required`：

- `advisory`：MISRA 問題最高列為 🟢，不擋合併
- `required`：違反 required 規則且沒有 deviation 紀錄時列為 🔴

`fw-c-review` 審查從某個固定點以來的 diff，分成**兩軸**，每軸各用一個 sub-agent 以免互相干擾，並列回報，不合併也不重新排序：

- **Standards**：程式碼是否符合 C/韌體 checklist、核准的分層與 MISRA 模式？
- **Spec**：程式碼是否做到票的 `user_visible_behavior` 與 `verification_steps`？回報缺少或部分完成的需求、沒人要求的行為，以及看似做了但做錯的需求。

Standards 分級：

- 🔴 **Critical（擋合併）**：未定義行為、陣列或指標越界、造成錯誤結果的整數溢位、ISR 與主迴圈共用資料卻沒有保護、缺少 `volatile`、忽略錯誤回傳碼、未驗證的外部長度、開著的除錯口或寫死的金鑰、不在 grandfather 清單內的分層違規
- 🟡 **Important**：新邏輯沒有測試、資源未釋放、時間敏感路徑上有阻塞呼叫、用 magic number 代替暫存器位址
- 🟢 **Suggestion**：命名、註解、可讀性、MISRA advisory

報告格式（`harness/reviews/FW-NNNN_<reviewer-slug>_<日期>.md`）：檔頭記錄 reviewer 身分、票號與審查的 commit 範圍；先放分級統計表；每條 finding 含嚴重度、`path:line`、問題、為什麼重要、建議修法與信心度。每條 finding 都經過自我驗證（重讀程式碼，排除上游已處理的誤判）。patch 只提議，由人決定是否套用。

review 完成後，`fw-ticket` 記錄 `kind: review` evidence，`open_critical` 取自報告。修正後重新 review 會產生新的報告與新的 evidence，以最新一筆為準。

`.github/instructions/c-fw-review.instructions.md` 是同一份 checklist 的精簡版，供 GitHub 上的 Copilot PR review 使用。`fw-harness-init` 從同一份來源產生它，確保兩者一致。

## 8. 錯誤處理

- 所有腳本失敗時以非 0 結束，並說明是哪個檢查、哪個檔案、怎麼修。
- 所有讀寫一律 UTF-8，不受 Windows 主控台編碼影響。
- 寫入票檔採「讀取 → 修改 → 寫入暫存檔 → rename」，當機也不會留下寫到一半的檔案。
- 離線（`git fetch` 失敗）時：票號分配與棘輪比對改用本地資料，並明確警告。
- `fw-harness-init` 遇到同名的既有檔案時，保留原檔、另寫 `<檔名>.harness-proposed` 並列出差異。

## 9. 測試 plugin 本身

- `harness/scripts/` 的 Python 以 pytest 測試：身分 slug、票號分配與改號、轉換規則、include 依賴解析、棘輪比對、索引產生。
- 測試會隔離貢獻者的全域 git 設定，個人的 `~/.gitconfig` 不會影響結果。
- `tests/fixtures/sample-fw/`：一個小型 CMake C 專案，含一個 vendor 資料夾、一個刻意的反向依賴與 Unity 測試。端對端測試把它複製到暫存目錄、執行 init 產生流程，並驗證 `check` 通過與失敗的情境。
- 以兩個 git 身分模擬並行工作：票號衝突、各自的 active 票、互相 review，涵蓋第 5 節。
- Skills 無法自動測試，改用人工檢查清單，在 Claude Code 與 Copilot 各跑一次完整循環（init → session-start → ticket → implement → review → done）。

## 10. 推行步驟

1. 以 `sample-fw` 完成 plugin，並通過第 9 節的測試。
2. 在一個真實的韌體 repo 上，由一到兩人試用兩週，累積 CLAUDE.md 第一批由事故長出的規則。
3. 依試用回饋調整後，在 GitHub 公開這個 repo，並撰寫安裝說明。
