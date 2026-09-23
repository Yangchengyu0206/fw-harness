# cdev

給一位開發者在 C 與 Python 專案使用的 markdown-first harness，支援 VS Code 的 GitHub Copilot 與 Claude Code。

它讓 agent 知道自己在哪裡、下一步要做什麼，並補上一般寫程式技能不會帶的領域規則：韌體、Linux 驅動、Windows 驅動、一般 C，以及 Python。

English: [README.md](README.md)

## 安裝

只裝在會用到的 repository，不要全域開啟：plugin 在哪裡生效，agent 會自行叫用的 skills 就會在那裡一起載入。

**VS Code 的 GitHub Copilot**

1. 加進你的 user settings JSON（**Preferences: Open User Settings (JSON)**）：

   ```json
   "chat.plugins.enabled": true,
   "chat.plugins.marketplaces": ["Yangchengyu0206/fw-harness"]
   ```

2. 在 Extensions 面板（Ctrl+Shift+X）搜尋 `@agentPlugins`，安裝 `cdev`。
3. VS Code 可以全域或個別 workspace 啟用 plugin。只在你會用到的 workspace 啟用。

**Claude Code**，在 repository 裡開一個 shell：

```bash
claude plugin marketplace add Yangchengyu0206/fw-harness
claude plugin install cdev@fw-harness --scope local
```

在 session 內改用 `/plugin install cdev@fw-harness`，它會問你要裝在哪個範圍。

**Copilot CLI**

```bash
copilot plugin marketplace add Yangchengyu0206/fw-harness
copilot plugin install cdev@fw-harness
```

接著在你的 repository 打開 agent chat，輸入一次 `/cdev-init`。之後 plugin 更新過，每個 repository 再輸入一次 `/cdev-upgrade`。

**沒有 marketplace 可用時**（例如同事的機器連不到），從 checkout 打包一份：

```bash
py -3 scripts/pack_cdev.py
```

它會產生 `dist/cdev-<版本>.zip`，裡面有 plugin 本體、兩份 README、授權，以及安裝腳本。收到的人解壓後照 [INSTALL.zh-TW.md](INSTALL.zh-TW.md) 做：用 `chat.pluginLocations` 設定註冊那個資料夾，或用 `py -3 install_local.py --repo <路徑>` 把 skills 放進單一 repository。

## 會寫進你 repository 的東西

```
AGENTS.md            所有規則：領域、驗證等級、可以改哪裡、怎麼開場、
                     怎麼回答問題、功能開發流程、done 的定義
CLAUDE.md            只有一行 @AGENTS.md，讓 Claude Code 讀到同一份規則
ARCHITECTURE.md      整個 repository 的地圖，以及決策與其理由
<資料夾>/ARCHITECTURE.md
                     職責、每個檔案一行、流程、進入點、相依關係
PROGRESS.md          ## Now（做到哪、已確認的事實、等你處理的事），以及按日期的紀錄
feature_list.json    正在做什麼，唯一的真實來源
tools/feature.py     確保 feature_list.json 有效
tools/doc_check.py   回報架構文件和實際檔案不一致的地方
tools/hooks.py       回應 session hooks
tools/mcp_list.py    列出這台機器與這個 repo 設定了哪些 MCP server
.vscode/settings.json
                     唯讀資料夾改不動；具破壞性的指令要經過你同意
.github/instructions/architecture.instructions.md
                     Copilot 處理有文件的程式碼時會自動附上
.github/hooks/cdev.json
                     SessionStart 把 ## Now、功能清單、文件檢查結果直接送到 agent 面前；
                     Stop 回報文件漂移。hooks 在 VS Code 目前是 preview
.github/agents/cdev-explorer.agent.md
                     唯讀的 agent，在自己的上下文裡讀 code，只回傳結論和出處
docs/reviews/        review 報告
```

這兩個腳本只回報，不會擋住任何 commit。

大型 repository 不必一次全部寫完文件：`cdev-init` 把你實際工作的資料夾寫完整，其餘只留骨架。`doc_check` 會把骨架列為「尚未撰寫」而不是漂移，等工作真的碰到那個資料夾時，`cdev-architecture-sync` 再補上。

## 在 GitHub Copilot 的一天

1. 開一個對話。session hook 會把 `## Now`、功能清單和文件檢查結果直接交給 agent，然後它問你要做哪個功能。hooks 不可用的環境下，AGENTS.md 的規則會讓它自己做一樣的事。
2. 問程式碼的問題時，先用架構文件當地圖，再回到程式碼驗證，並標明哪些說法驗證過、哪些沒有。需要讀好幾個檔案的問題會交給 `cdev-explorer` agent，它在自己的上下文裡讀，只把結論和出處帶回來。
3. 這個 repo 回答不了的問題（其他分支、datasheet、application note），agent 會先去翻這次 session 手上有哪些工具，而不是直接說不知道。之後新增 MCP server 不用改任何設定，因為規則指的是工具清單本身，不是寫死的 server 名單。
3. 開發功能的過程中，`## Now` 每完成一步就重寫，確認到的事實當下就寫進去，這樣對話被摘要也不會遺失。
4. build 或燒錄在廠商 IDE 裡進行時，功能會停在 `verifying`，`## Now` 裡留下要你做的事。你跑完回報結果，在原本的對話或新對話都可以。
5. 上下文用量偏高時，輸入 `/cdev-checkpoint`。
6. 驗證通過後，agent 會列出證據和它改過的文件，功能要經你確認才會變成 `done`。

## 動工之前先把假設攤開

移植出錯，代價最大的通常不是寫錯 code，而是動工前就決定錯了：時序照抄上一顆晶片、某個模組先關掉然後沒人記得、暫存器序列來自另一顆的 application note。`/cdev-grill` 會在動工前一輪一輪追問你的計畫，需要的事實它自己去查而不是問你，最後把你的決定和理由寫進根目錄 ARCHITECTURE.md 的「決策與理由」表格。

## 驗證預設是關閉的

`AGENTS.md` 有一行 `Verification: off`，`cdev-init` 把成果交給你時會說明另外兩個等級。`off` 不要求硬體結果、不寫清單：功能編得過、跑起來合理就可以關閉，每筆紀錄會註明哪些沒有在實際硬體上驗證。`light` 會把還欠的那一步寫成功能的下一步。`full` 會加上給你的清單、`docs/evidence/` 底下的 log，以及 `cdev-target-verify`。

新晶片的初期工作大多還沒到硬體階段，所以預設從 `off` 開始。改等級只要改一個字，不用重裝。

每個等級都不會改變的兩件事：功能一定要你確認才會變成 `done`，而 `## Log` 一定會記錄它是怎麼被檢查的。

## 測試是選配

沒有測試的 repository 是常態，不是缺陷。`cdev-init` 會在 AGENTS.md 寫下 `Test: none`，skills 不會擅自加測試框架，除非你要求。它們仍然會把每次修改跑在真實輸入上，並把指令和輸出列給你看，因為沒有跑過就說會動的 agent 只是在猜。功能的 `verification` 清單同樣是選配，`cdev-target-verify` 只在韌體和驅動才用得到。

## Skills

初始設定：`cdev-init`，plugin 更新後用 `cdev-upgrade`。
動工之前：`cdev-grill`。
日常工作：`cdev-session-start`、`cdev-implement`、`cdev-target-verify`、`cdev-checkpoint`、`cdev-done`，底下由 `cdev-feature` 支撐。
看程式碼：`cdev-review`、`cdev-test-gap`、`cdev-debug`。
結構改變時：`cdev-architecture-sync`。
導覽：`cdev-guide`。

每個 skill 各有一頁說明，放在 [docs/skills](../../docs/skills)。

## 領域

`cdev-init` 會偵測 repository 屬於哪些領域，一個 repository 可以同時屬於好幾個。implement、review、test-gap、debug 這幾個 skill 會從 `skills/cdev-implement/references/` 讀取對應領域的參考文件：規則、review 檢查表、debug 切入點，以及 build 和測試指令。

## 兩個工具的一個差異

有八個 skill 是設計成由你輸入的：`cdev-init`、`cdev-upgrade`、`cdev-session-start`、`cdev-grill`、`cdev-target-verify`、`cdev-checkpoint`、`cdev-done`、`cdev-guide`。它們帶著 `disable-model-invocation: true`，VS Code 的 GitHub Copilot 和 Claude Code 都記載這個欄位會阻止 agent 自行啟動它們；你在 chat 用 `/` 開始。Copilot CLI 沒有記載這個欄位，所以在那裡 agent 仍然可能自己叫用。

## 和 fw-c-harness 的差別

同一個 marketplace 裡的 `fw-c-harness` 是給韌體團隊用的：會擋下不合格 commit 的驗證閘門、記錄誰改了什麼的 ticket 狀態，以及必須由他人 review 的規則。`cdev` 為了單人開發拿掉這些，並把領域從韌體擴大到 C 和 Python。

一個 repository 只裝其中一個。

## 授權

MIT。改寫自其他專案的內容列在 [THIRD_PARTY_NOTICES.md](../../THIRD_PARTY_NOTICES.md)。
