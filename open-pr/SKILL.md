---
name: open-pr
description: 發起 GitHub Pull Request 並以臺灣繁體中文撰寫完整 PR 訊息。Use when 需要從目前分支建立 PR、整理變更重點與測試結果、避免中國用語，並在 PR 建立後自動用 review-pr-3x 追蹤最新審查與 CI 狀態。
---

# Open PR

使用 `gh` 從目前分支發起 PR，產出詳細且可審閱的 PR message（臺灣繁體），並在發起後自動執行 `review-pr-3x` 持續追蹤。

## 前置檢查

1. 確認目前在 Git 儲存庫且 `gh` 可用。
2. 確認目前分支不是 `main`、`master`。
3. 確認有可提交的變更，並先完成必要測試。
4. 推送目前分支：
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

## 產生詳細 PR 訊息

先蒐集變更資訊：

```bash
BASE_BRANCH="${BASE_BRANCH:-main}"
CURRENT_BRANCH="$(git branch --show-current)"
git fetch origin

git log --oneline "origin/${BASE_BRANCH}..${CURRENT_BRANCH}"
git diff --stat "origin/${BASE_BRANCH}...${CURRENT_BRANCH}"
```

建立 PR 內文檔案（務必完整填寫）：

```bash
cat > /tmp/pr_body.md <<'MD'
## 變更摘要
- 說明這次變更解決的問題與核心做法。
- 描述主要模組、流程或介面調整。

## 主要變更項目
- 項目 1：影響範圍、設計考量、相容性。
- 項目 2：關鍵邏輯、例外處理、風險控管。
- 項目 3：必要的設定、文件或腳本調整。

## 測試與驗證
- [ ] 單元測試
- [ ] 整合測試
- [ ] 手動驗證
- [ ] 靜態檢查（Lint/型別檢查）

測試細節：
- 指令：`<請填入實際執行的測試指令>`
- 結果：`<請填入測試結果與重現方式>`

## 風險與回滾
- 潛在風險：<請填入>
- 監控指標：<請填入>
- 回滾方式：<請填入>

## 相關議題
- Closes #<issue-number>
- Ref: #<issue-number>
MD
```

## 檢查 PR 內文格式

在提交之前，先檢查 `/tmp/pr_body.md` 是否含有字面 `\n`（單次）或 `\n\n`（連續），這些會導致 PR 頁面顯示怪異：

```bash
rg -n "\\\\n" /tmp/pr_body.md
rg -n "\\\\n\\\\n" /tmp/pr_body.md
```

若輸出非空，請把該位置改成自然分行或以中文敘述代替 `\n`，再重新確認沒有字串殘留。

PR 標題與內文都要切合本次變更，避免泛用敘述。

```text
<類型>: <以臺灣繁體中文描述本次變更重點>
```

類型示例：`feat`、`fix`、`refactor`、`docs`、`test`、`chore`。

## 發起 PR

```bash
gh pr create \
  --base "${BASE_BRANCH}" \
  --head "${CURRENT_BRANCH}" \
  --title "<請填入臺灣繁體中文標題>" \
  --body-file /tmp/pr_body.md
```

建立後擷取 PR 編號與連結：

```bash
PR_URL="$(gh pr view --json url --jq .url)"
PR_NUMBER="$(gh pr view --json number --jq .number)"
echo "PR: ${PR_URL}"
```

## 自動模板與驗證

使用 `open-pr/scripts/build_pr_body.sh` 來自動補齊模板並在發 PR 前複查：

1. 執行 `scripts/build_pr_body.sh generate`（或搭配 `PR_BODY`/`BASE_BRANCH` 環境變數）建立 `/tmp/pr_body.md`。這會根據 commit log、diff、branch/issue 抽出「自動產生」段落、建議標題以及關鍵字。
2. 編輯 `/tmp/pr_body.md`：填入實際變更摘要、主要變更項目、測試指令/結果、風險與回滾、相關議題（或把這份檔案搬進 repo 以檢查 diff）。
3. 執行 `scripts/build_pr_body.sh validate`，它會：
   - 確保沒有 `<請填入…>` placeholder 或 `\n`/`\n\n` 字串、
   - 檢查測試指令與結果已填入且至少有 2 項 checkbox、
   - 比對推論關鍵字與 PR 內文是否吻合、
   - 確認無多餘的未追蹤檔案、branch 對應的 issue 存在。
4. 檢查通過後，才執行 `gh pr create`，再接 `review-pr-3x`。

驗證失敗時，腳本會以中文提醒錯誤項目並中止，請依提示補齊再重試。

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
