# cdev 測試說明

這份寫給第一批試用的人。安裝方式在 [INSTALL.zh-TW.md](INSTALL.zh-TW.md)，完整說明在 [README.zh-TW.md](README.zh-TW.md)。

English: [TESTING.md](TESTING.md)

## 這包在做什麼

一句話：**讓 agent 知道現在在哪、規則是什麼、東西在哪裡，而且這些知識不會因為換對話就消失。**

它不是 AI，也不會讓模型變聰明。它做的事是把「每次都要重講一遍」的東西寫進 repo 的檔案，讓 agent 每次自己讀。

裝進 repo 的東西：

| 檔案 | 作用 |
|---|---|
| `AGENTS.md` | 所有規則。Copilot 每次對話自動載入 |
| `ARCHITECTURE.md`（根目錄與各資料夾） | 地圖：每個檔案做什麼、主要流程怎麼走、決策與理由、術語 |
| `PROGRESS.md` | `## Now` 做到哪、確認了什麼事實、等你處理什麼；`## Log` 歷史 |
| `feature_list.json` | 正在做什麼，狀態是 next / active / verifying / done |
| `tools/` 四個腳本 | 功能清單、文件漂移檢查、session hook、MCP 盤點 |
| `.vscode/settings.json` | vendor 資料夾唯讀、危險指令要你確認 |
| `.github/hooks/`、`.github/agents/`、`.github/instructions/` | 開場自動注入狀態、唯讀的讀碼 agent、改 code 時的提醒 |

14 個 skill 分兩種：`cdev-implement`、`cdev-review`、`cdev-debug` 這類由 agent 自己判斷要不要用；`/cdev-init`、`/cdev-grill`、`/cdev-done` 這類由你輸入。

## 有這包和沒這包的差別

### 沒有它

**好處**

- 零安裝、零維護，repo 裡不會多出任何檔案
- 每次對話乾淨，不會被任何規則影響
- 問一個小問題時最輕，沒有額外負擔

**代價**

- 每次開新對話都要重新講「上次做到哪、下一步要做什麼」
- 問架構問題，agent 每次從頭 grep，答案的深度看它這次運氣
- 它可能改到 vendor SDK，或跑出你沒預期的指令
- 做完沒有紀錄。為什麼當初這樣決定，三個月後沒人記得
- 對話被摘要時，查到的暫存器值、timing 這些會一起消失

### 有它

**好處**

- 開新對話時，agent 自己知道做到哪、下一步是什麼（由 hook 注入，不靠模型自覺）
- 架構文件當地圖，定位快，而且答案會標明哪些是回頭驗證過的
- 決策和理由留在 repo 裡，不是留在某個人的對話紀錄裡
- 完成的標準一致，而且一定要你點頭才算 done
- 文件和實際檔案不一致時，腳本會抓出來
- vendor 資料夾唯讀、危險指令要確認
- repo 答不出來的問題（其他分支、datasheet），它會先去找手上的工具，而不是直接說不知道
- 動工前可以用 `/cdev-grill` 把假設攤開來追問一輪

**代價**

- 第一次 `/cdev-init` 要花幾分鐘，而且會用掉一次比較大的上下文
- 多了一批要維護的文件。過時的文件會誤導人，所以有 `doc_check` 和規則在擋，但不是零成本
- 規則本身每次對話佔約 3 到 4 KB
- **大部分行為是規則導向，不是機制保證**。模型多數時候會照做，對話很長時最容易漏
- 只問一個小問題的情境，它沒有幫助，甚至稍微更重

### 適合與不適合

**適合**：跨好幾天的任務、需要上板驗證的工作、會交接給別人的專案、你自己三個月後還要回來看的 code。

**不適合**：一次性的小修改、只問一個問題就結束的情境。

## 哪些是保證的，哪些不是

這點請特別留意，它決定你該期待什麼：

| 行為 | 保證程度 |
|---|---|
| 開場注入目前狀態 | 機制（hook 腳本）。VS Code 標示 hooks 為 preview |
| 文件漂移偵測 | 機制（`doc_check.py`） |
| vendor 唯讀、危險指令確認 | 編輯器設定。**尚未實測，這次請幫忙確認** |
| 回答前先查文件再驗證 code | 規則 |
| 答不出來先去找工具 | 規則 |
| 每步更新 `## Now` | 規則 |
| 改 code 同步文件 | 規則 + 偵測 |
| done 要你確認 | 規則 |

## 請幫忙測這幾項

由上而下，越前面越重要：

1. **安裝**：照 INSTALL 裝完後，在 agent chat 打 `/`，有沒有看到 14 個 `cdev-` 指令。
2. **開場**：在已經有 harness 的 repo 開新對話，隨便問一句。它有沒有主動說「上次做到哪、下一步是什麼」？沒有的話，是完全沒提，還是講得不完整？
3. **唯讀設定**：打開 vendor 資料夾裡的檔案，是不是不能編輯？叫 agent 跑 `git push`，會不會停下來等你確認？
4. **問架構問題**：問一個要跨幾個檔案的問題。它有沒有先讀 ARCHITECTURE.md？答案有沒有標明哪些驗證過？
5. **`/cdev-init`**：在還沒有 harness 的專案跑一次。會不會跑到一半失敗或爆掉？產出的文件正不正確？
6. **`/cdev-upgrade`**：在舊版 harness 的專案跑，看你寫的內容有沒有被保留。
7. **長對話**：做一件比較久的事，中途打 `/cdev-checkpoint`，然後開新對話，看它接不接得回去。
8. **`/cdev-grill`**：動工前叫它追問一輪，問題有沒有問到點上。

## 回報時請附上

- VS Code 版本（Help → About）和 GitHub Copilot Chat 擴充套件版本
- 用哪一種安裝方式（plugin 資料夾，還是複製進 repo）
- 當下用哪個模型
- 你做了什麼、預期看到什麼、實際看到什麼
- 錯誤訊息的話，附上 View → Output → `GitHub Copilot Chat` 裡的內容

回報到 [GitHub issues](https://github.com/Yangchengyu0206/fw-harness/issues)，或直接告訴維護的人。

## 已知還沒驗證的地方

- VS Code 的唯讀與指令確認設定是照官方文件寫的，還沒有人實際確認過生效
- agent hooks 在 VS Code 目前是 preview，格式可能會變
- Linux 與 Windows 驅動的領域參考資料還沒經過驅動工程師審閱
- 所有指令以 Windows 為準（`py -3`），macOS 和 Linux 請改用 `python3`
