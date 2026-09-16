# fw-harness

給 C 韌體團隊的 harness 與技能組，同時支援 Claude Code 與 GitHub Copilot。English: [README.md](README.md)。

裝一次，團隊會得到兩樣東西：

1. **產生到自己 repo 裡的 harness**：入口文件、記錄「誰改了什麼」的票務狀態、驗證閘門、git hooks，以及依實際目錄樹產生的每個 C 原始碼資料夾一份 ARCHITECTURE.md。
2. **涵蓋整個工作迴圈的 skills**：開始一個 session、認領票、測試先行地實作、審查、除錯、收尾。

## 為什麼設計成這樣

- **多人共用同一份程式碼。** 每次狀態變更都會記下操作者，身分取自 `git config`。一票一檔，所以兩個人同時開票時 git 會報衝突，而不是默默覆蓋掉一邊。
- **規則放在 repo 裡，不放在 plugin 裡。** 閘門是提交進韌體 repo 的 Python 腳本，因此手動 commit 的人、agent、CI 遵守的是同一套規則。plugin 只帶會跟著版本更新的東西。
- **閘門是棘輪。** `cppcheck` 抑制清單與架構的 grandfather 清單只能變短，比較基準是 `origin/main`。
- **「寫完」與「完成」是兩回事。** 程式碼通過 `check`、但還欠板子驗證或審查的票會停在 `verifying`，欠的項目要寫下來。

## 安裝

**Claude Code**

```
/plugin marketplace add Yangchengyu0206/fw-harness
/plugin install fw-c-harness@fw-harness
```

**Copilot CLI**

```
copilot plugin marketplace add Yangchengyu0206/fw-harness
copilot plugin install fw-c-harness@fw-harness
```

接著在你的韌體 repo 裡執行一次 `fw-harness-init`。

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

支援 Windows、macOS、Linux。在 Windows 上腳本以 `py -3` 執行，不論主控台代碼頁為何都以 UTF-8 讀寫，git hooks 使用 Git for Windows 內附的 POSIX shell。

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
| `fw-c-test-gap` | agent 自己會用 | 哪些行為沒有測試，P0 到 P3 |
| `fw-c-debug` | agent 自己會用 | 先重現，再修 |
| `fw-misra-deviation` | agent 自己會用 | 記錄偏差並取得核准人 |
| `fw-guide` | 你自己輸入 | 現在該用哪個 skill |

每個 skill 各有一頁說明，放在 [docs/skills](docs/skills)。設計文件在 [spec](docs/superpowers/specs/2026-09-15-fw-c-harness-plugin-design.zh-TW.md)。

## 參與開發

以 `py -3 -m pytest tests -q` 執行測試。skills 無法自動測試，所以相關改動要對照 [docs/manual-checklist.md](docs/manual-checklist.md) 人工走一次。

## 授權

MIT。改寫自其他專案的內容列在 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
