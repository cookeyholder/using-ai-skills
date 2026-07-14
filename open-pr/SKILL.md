---
name: open-pr
description: 發起 GitHub Pull Request 並以臺灣繁體中文撰寫完整 PR 訊息。Use when 需要從目前分支建立 PR、整理變更重點與測試結果、避免中國用語，並在 PR 建立後自動用 review-pr-3x 追蹤最新審查與 CI 狀態。
---

# Open PR

使用 `gh` 從目前分支發起 PR，產出詳細且可審閱的 PR message（臺灣繁體），並在發起後自動執行 `review-pr-3x` 持續追蹤。

在使用任何指令前，先 `cd` 到專案根目錄。

## 前置檢查

1. 確認目前在 Git 儲存庫且 `gh` 可用。
2. 確認目前分支不是 `main`、`master`。
3. 確認有可提交的變更，並先完成必要測試。
4. 確認遠端 origin 存在，若無則提示設定：
```bash
git remote get-url origin
```
5. 推送目前分支：
```bash
git push -u origin "$(git branch --show-current)"
```

## 語言規範（強制）

PR 標題與內文都必須使用臺灣繁體中文，避免中國常見用語。

常見替換：
- 拉取請求 -> Pull Request
- 默認 -> 預設
- 配置 -> 設定
- 資源庫 -> 儲存庫
- 用戶 -> 使用者
- 視圖 -> 檢視
- 代碼 -> 程式碼
- 視頻 -> 影片
- 網絡 -> 網路
- 運行 -> 執行
- 優化 -> 最佳化

若偵測到不符合的詞，先改寫再發 PR。

## 產生 PR 內文

先進入專案根目錄，再從該目錄執行腳本（使用絕對路徑避免分析到 skill 儲存庫）。

```bash
cd <專案根目錄>

export BASE_BRANCH="$(gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name')"
export CURRENT_BRANCH="$(git branch --show-current)"

<agent-skills-root>/open-pr/scripts/build_pr_body.sh generate
```

腳本會自動分析 commit log、diff 產生：
- 變更摘要（列出所有變更模組與 commit 列表）
- 主要變更項目（含檔案與變更類型：新增/修改/刪除）
- 測試與驗證 checkbox 與預設測試細節
- 風險與回滾預設值
- 相關議題

**可選**：若需補充測試細節、風險說明，請編輯 `/tmp/pr_body.md`。

## 驗證 PR 內文

```bash
<agent-skills-root>/open-pr/scripts/build_pr_body.sh validate
```

驗證項目：
- 無字面 `\n` 字串（會導致 PR 頁面顯示異常）
- 無未填寫的「請填入」欄位
- 至少有 2 項測試 checkbox

## 發起 PR

```bash
gh pr create \
  --base "${BASE_BRANCH}" \
  --head "${CURRENT_BRANCH}" \
  --title "<臺灣繁體中文標題>" \
  --body-file /tmp/pr_body.md
```

建立後擷取 PR 編號與連結：

```bash
PR_URL="$(gh pr view --json url --jq .url)"
PR_NUMBER="$(gh pr view --json number --jq .number)"
echo "PR: ${PR_URL}"
```

## 自動追蹤（強制）

PR 建立成功後，立即執行：

```bash
review-pr-3x "${PR_NUMBER}"
```

若執行環境不支援直接呼叫 skill 指令，改用明確委派方式：
- 在同一回合明確接續執行 `$review-pr-3x`。
- 帶入剛建立的 PR 編號。
- 回報三輪追蹤的最新審查狀態與 CI 結果。

## 輸出回報格式

完成後回報以下資訊：
1. PR 標題與連結。
2. PR message 重點摘要。
3. `review-pr-3x` 三輪結果（含是否有新評論、CI 是否通過、是否有新增提交）。
4. 仍待處理事項（若有）。

## Guardrails

- 不要改動與本 PR 無關的檔案。
- 未完成必要測試時，不要宣稱已驗證通過。
- 若 `gh auth status` 未登入，先中止並提示使用者先完成登入。
- 若 `review-pr-3x` 無法執行，明確說明阻塞原因並提供下一步。
