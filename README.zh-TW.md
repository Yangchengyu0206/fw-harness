# fw-harness

給 C 與 Python 開發用的 harness 與技能組，支援 VS Code 上的 GitHub Copilot 與 Claude Code。English: [README.md](README.md)。

## 目前狀態：預覽版

`cdev` 目前是 0.2.0，`fw-c-harness` 是 0.1.0。兩個 plugin 的內容都已完成，腳本也有自動化測試，但 skill 還沒有實際讓 agent 從頭到尾跑過。使用上可能會遇到不順的地方，歡迎到 [GitHub issues](https://github.com/Yangchengyu0206/fw-harness/issues) 回報。

這個版本已知的限制：

- **只檢查過格式，還沒實際使用過。** 測試能確認每個 skill 格式正確、連結有效、文件裡的指令都能解析，但無法確認 agent 會照 skill 做。還需要人工試過的項目列在 [docs/manual-checklist.md](docs/manual-checklist.md)。
- **還沒在工具裡實際試過。** 安裝方式與每個 skill 都依照 VS Code 上的 GitHub Copilot、Claude Code、Copilot CLI 公開的格式撰寫，但都還沒實際執行過。主要目標是 VS Code 上的 GitHub Copilot：`cdev` 把所有規則放在 Copilot 會自動載入的 AGENTS.md，CLAUDE.md 只是匯入它給 Claude Code 用。
- **`cdev` 寫出的編輯器設定還沒驗證過。** `.vscode/settings.json` 用 `files.readonlyInclude` 把 vendor 資料夾設為唯讀，用 `chat.tools.terminal.autoApprove` 讓具破壞性的指令必須經你同意。兩者都是照文件寫的，還沒有在實際執行的 VS Code 上確認過，請當成未驗證來看待。
- **指令以 Windows 寫法為準。** skill 裡要 agent 用 `py -3` 執行 Python；在 macOS 與 Linux 上請改用 `python3`。腳本本身三個平台都能執行。
- **驅動參考資料還沒經過審閱。** `cdev` 裡 Linux 與 Windows 驅動的內容還沒有請驅動工程師看過，歡迎指正。

## 兩個 plugin

這個 marketplace 裡有兩個 plugin，每個 repo 裝其中一個。

| | `fw-c-harness` | `cdev` |
|---|---|---|
| 適用 | 共用同一個 repo 的韌體團隊 | 單人開發 |
| 語言與領域 | C 韌體 | C 與 Python：一般 C、韌體、Linux 驅動、Windows 驅動 |
| 驗證 | `check` 七道閘門、git hooks、棘輪 | AGENTS.md 裡一行 `Verification:`，可設為 `off`、`light`、`full`，預設 `off`；任何等級都不會擋住 commit |
| 狀態 | 一票一檔，記錄誰改了什麼 | 一份 `feature_list.json` 加一份 `PROGRESS.md` |
| 審查 | 必須由作者以外的人審 | 自我審查，每個發現都重新驗證 |
| 長對話中不遺失的狀態 | 票務檔案與交接文件 | PROGRESS.md 的 `## Now`，每完成一步就重寫，另有 `/cdev-checkpoint` 補存 |
| 寫進 repo 的腳本 | 閘門與狀態腳本 | 兩個，`tools/feature.py` 與 `tools/doc_check.py`，都只回報 |
| 安裝 | 在 VS Code 的 `@agentPlugins` 安裝 `fw-c-harness` | 在 VS Code 的 `@agentPlugins` 安裝 `cdev`，或在連不到 marketplace 的機器上用 zip 安裝 |
| 讓既有 repo 跟上新版 | `/fw-harness-upgrade` | `/cdev-upgrade` |

`cdev` 的中文說明在 [plugins/cdev/README.zh-TW.md](plugins/cdev/README.zh-TW.md)，英文版在 [plugins/cdev/README.md](plugins/cdev/README.md)。要給連不到 marketplace 的人，執行 `py -3 scripts/pack_cdev.py`，把產生的 `dist/cdev-<版本>.zip` 交給對方，對方照 [plugins/cdev/INSTALL.zh-TW.md](plugins/cdev/INSTALL.zh-TW.md) 安裝。

本頁其餘內容說明 `fw-c-harness`。

## fw-c-harness

裝一次，團隊會得到兩樣東西：

1. **產生到自己 repo 裡的 harness**：入口文件、記錄「誰改了什麼」的票務狀態、驗證閘門、git hooks，以及依實際目錄樹產生的每個 C 原始碼資料夾一份 ARCHITECTURE.md。
2. **涵蓋整個工作迴圈的 skills**：開始一個 session、認領票、測試先行地實作、審查、處理審查意見、除錯、收尾。

## 為什麼設計成這樣

- **多人共用同一份程式碼。** 每次狀態變更都會記下操作者，身分取自 `git config`。一票一檔，所以兩個人同時開票時 git 會報衝突，而不是默默覆蓋掉一邊。
- **規則放在 repo 裡，不放在 plugin 裡。** 閘門是提交進韌體 repo 的 Python 腳本，因此手動 commit 的人、agent、CI 遵守的是同一套規則。plugin 只帶會跟著版本更新的東西。
- **閘門是棘輪。** `cppcheck` 抑制清單與架構的 grandfather 清單只能變短，比較基準是 `origin/main`。
- **「寫完」與「完成」是兩回事。** 程式碼通過 `check`、但還欠板子驗證或審查的票會停在 `verifying`，欠的項目要寫下來。

## 安裝

加入 marketplace 與安裝 plugin 是兩個步驟。請只在使用 harness 的 repo 啟用，不要對所有專案啟用：plugin 啟用的地方，agent 自己會用的 skill 都會載入，在無關的專案裡請 agent 做審查或除錯時也會被觸發。

**VS Code 上的 GitHub Copilot**

1. 開啟使用者設定的 JSON（**Preferences: Open User Settings (JSON)**），加入：

   ```json
   "chat.plugins.enabled": true,
   "chat.plugins.marketplaces": ["Yangchengyu0206/fw-harness"]
   ```

2. 開啟 Extensions 視圖（Ctrl+Shift+X），搜尋 `@agentPlugins`，安裝 `fw-c-harness`。
3. VS Code 可以對 plugin 做全域或單一工作區的啟用與停用，請只在韌體工作區啟用。

**Claude Code**，在韌體 repo 的 shell 裡：

```bash
claude plugin marketplace add Yangchengyu0206/fw-harness
claude plugin install fw-c-harness@fw-harness --scope project
```

在 session 裡用 `/plugin install fw-c-harness@fw-harness` 則會讓你選範圍。`project` 會把 plugin 記錄在 repo 裡給所有人用；`local` 只有你、只在這個 repo；`user` 會在你的每個專案都啟用。

**Copilot CLI**

```bash
copilot plugin marketplace add Yangchengyu0206/fw-harness
copilot plugin install fw-c-harness@fw-harness
```

接著在韌體 repo 開啟 agent 對話，輸入一次 `/fw-harness-init`。

### 加入一個已經有 harness 的 repo

`fw-harness-init` 會把這個 marketplace 和 plugin 寫進 repo 的 `.claude/settings.json`。Claude Code、VS Code 上的 GitHub Copilot、Copilot CLI 都會讀這個檔案，但都不會自動安裝：

- **VS Code** 在你第一次送出對話訊息時跳出通知，到 Extensions 視圖用 `@agentPlugins @recommended` 篩選後安裝。
- **Claude Code** 在你信任資料夾後加入 marketplace，回報 plugin 尚未安裝，並印出要執行的 `claude plugin install` 指令。

## 會產生到 repo 裡的東西

```
AGENTS.md              所有工具共用的簡短入口
CLAUDE.md              手冊：session 流程、工作規則、完成定義，以及每道閘門的理由
ARCHITECTURE.md        模組地圖，由 harness/architecture.json 產生
harness/
  config.json          所有外部指令，以 argv 陣列表示
  architecture.json    核准的分層，規則的唯一來源
  tickets/FW-NNNN.json 一票一檔
  scripts/             閘門邏輯的唯一實作
.githooks/             commit-msg、post-commit、post-merge
init.sh / init.ps1     薄包裝，不自己加任何旗標
```

`check` 依序執行七個步驟，遇到第一個失敗就停：對變動的 C 原始碼跑格式檢查、`cppcheck`、架構閘門、票務閘門、交叉編譯、主機端測試、體積預算。所有外部指令都來自 `harness/config.json`，換工具鏈不必改腳本。

## 需求

Python 3.9 以上、git，以及你在 `harness/config.json` 指定的工具鏈。預設是 `arm-none-eabi-gcc` 搭配 CMake、主機端 `gcc` 跑 Unity、`cppcheck`、`clang-format`。MISRA C:2012 只是參考標準，預設 advisory，可在 `harness/review-policy.json` 調整。

支援 Windows、macOS、Linux。在 Windows 上腳本以 `py -3` 執行（其他平台用 `python3`），不論主控台代碼頁為何都以 UTF-8 讀寫，git hooks 使用 Git for Windows 內附的 POSIX shell。

## Skills

| Skill | 呼叫方式 | 用途 |
|---|---|---|
| `fw-harness-init` | 你自己輸入 | 在韌體 repo 產生 harness |
| `fw-harness-upgrade` | 你自己輸入 | plugin 更新後同步 harness |
| `fw-architecture-sync` | agent 自己會用 | 重新草擬架構並更新文件 |
| `fw-session-start` | 你自己輸入 | 開始一個 session 並確認要做的票 |
| `fw-ticket` | agent 自己會用 | 所有票務寫入 |
| `fw-hil-verify` | 你自己輸入 | 以擷取的日誌償還板子驗證 |
| `fw-done` | 你自己輸入 | handoff、進度紀錄、更新票、commit 訊息 |
| `fw-c-implement` | agent 自己會用 | 測試先行的實作 |
| `fw-c-review` | agent 自己會用 | Standards 與 Spec 兩軸審查 |
| `fw-review-respond` | agent 自己會用 | 逐條查證審查意見，修正或附理由婉拒，再交回重審 |
| `fw-c-test-gap` | agent 自己會用 | 哪些行為沒有測試，P0 到 P3 |
| `fw-c-debug` | agent 自己會用 | 先讓問題能穩定重現、證實原因，再修 |
| `fw-misra-deviation` | agent 自己會用 | 記錄偏差並取得核准人 |
| `fw-guide` | 你自己輸入 | 現在該用哪個 skill |

每個 skill 各有一頁說明，放在 [docs/skills](docs/skills)。設計文件在 [spec](docs/superpowers/specs/2026-09-15-fw-c-harness-plugin-design.zh-TW.md)。

## 參與開發

以 `py -3 -m pytest tests -q` 執行測試，macOS 與 Linux 上用 `python3 -m pytest tests -q`。skills 無法自動測試，所以相關改動要對照 [docs/manual-checklist.md](docs/manual-checklist.md) 人工走一次。

## 授權

MIT。改寫自其他專案的內容列在 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
