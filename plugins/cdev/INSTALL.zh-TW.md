# 離線安裝 cdev

你手上這包是完整的 cdev plugin，不需要連到 GitHub 或任何 marketplace。

English: [INSTALL.md](INSTALL.md)

需要 Python 3（Windows 上用 `py -3` 執行）。

## 先選一種

| 你的情況 | 選哪一種 |
|---|---|
| 和別人共用同一個專案，大家都要用 | **方式二**：skills 放進那個 repo。之後 harness 更新，大家 pull 就拿到新版，不用重發一包、也不用各自改設定 |
| 你有好幾個專案都想用 | **方式一**：裝成 plugin，每個 workspace 都有 |

兩種可以並用，但同一個 repo 只選一種，免得同一個 skill 被載入兩次。

## 方式一：裝成 plugin（所有專案都能用）

1. 把這包解壓到一個**不會被刪掉**的位置，例如 `C:\tools\cdev`。VS Code 會一直從這裡讀取，所以不要放在下載或暫存資料夾。

2. 印出要加的設定：

   ```
   py -3 C:\tools\cdev\install_local.py
   ```

   它會輸出類似這樣的內容：

   ```json
   {
     "chat.pluginLocations": {
       "C:/tools/cdev": true
     }
   }
   ```

3. 在 VS Code 按 Ctrl+Shift+P，執行 **Preferences: Open User Settings (JSON)**，把 `chat.pluginLocations` 這一項加進你的設定檔（如果已經有這個項目，就把那一行加進去）。

4. 重開 VS Code。在 agent chat 輸入 `/` 應該會看到 `cdev-` 開頭的指令。

## 方式二：放進單一 repository（跟著 repo 走）

適合讓每個 clone 這個 repo 的人都自動拿到 skills，不必各自改設定。

```
py -3 C:\tools\cdev\install_local.py --repo D:\work\my-project
```

這會把 skills 複製到那個 repo 的 `.github/skills/`。把它們 commit 進去，之後每個人 clone 下來就有。

用 Claude Code 的人加上 `--tool claude`，skills 會複製到 `.claude/skills/`。

## 安裝完之後

**這個 repo 還沒有 harness**：在 agent chat 輸入一次 `/cdev-init`。它會偵測專案屬於哪些領域，寫出 AGENTS.md、架構文件、PROGRESS.md 和功能清單，最後把成果交給你 review。

**這個 repo 已經有 AGENTS.md**：不要跑 init。規則已經在 repo 裡，直接開始工作就好。如果那份 harness 是舊版本產生的，跑一次 `/cdev-upgrade` 補上缺的部分。

先讀 [README.zh-TW.md](README.zh-TW.md) 了解它實際會怎麼運作。

## 之後要更新

**用方式一的人**：拿到新的一包後，解壓覆蓋掉舊資料夾，重開 VS Code。

**用方式二的人**：什麼都不用做。維護的人更新完 `.github/skills/` 並 commit，你 `git pull` 就是新版。

兩種情況下，如果某個 repo 的 harness 檔案（AGENTS.md、架構文件那些）也需要跟著更新，在那個 repo 跑一次 `/cdev-upgrade`。通常由一個人跑完 commit，其他人 pull 就好，不必每個人各跑一次。

## 遇到問題

- **打 `/` 看不到 cdev 指令**：確認 `chat.pluginLocations` 裡的路徑用的是正斜線（`C:/tools/cdev`），資料夾裡有 `plugin.json`，並且重開過 VS Code。
- **`py -3` 找不到**：改用 `python`，或先安裝 Python 3。
- **skills 會自己跑起來**：`cdev-implement`、`cdev-review`、`cdev-debug` 這幾個是設計成由 agent 自行判斷要不要用的。其他七個要你自己打 `/`。
