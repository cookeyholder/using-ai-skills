# open-pr 改善設計稿

## 目的
在目前 `open-pr` skill 上加強「PR 內容自動補模板」與「發布前驗證」，讓使用者能更快速、可靠地產生符合格式、敘述切題、無殘留 placeholder 的 Pull Request，並保持 `review-pr-3x` 的追蹤流程。

## 自動填模板的資料來源與策略
1. **commit log**：取最近 1~3 個 commit 的標題與第一行內文，摘出動詞與主要對象，作為 `<類型>`、## 變更摘要與## 主要變更項目的初步內容。
2. **diff 分析**：透過 `git diff --stat` 與 `git diff --name-only` 取得變更最多的目錄/檔案群，將這些信息插入 bullet 例如「調整 `src/components` 相關樣式」或「更新 `pkg/util` 核心驗證邏輯」。
3. **issue/branch 名稱**：若 branch 名稱包含 issue number（例如 `feat/123-add-login`）或已連結 issue，將該 issue 標題與編號引入「相關議題」/「變更摘要」，並可用 `gh issue view` 抓標題作為補充描述。
4. **模板輸出**：`/tmp/pr_body.md` 在各段落前填入自動產出的句子；用箭號 `-` bullet 列出 commit、diff、issue 的重點，讓使用者只需微調與確認。

## 嚴謹驗證流程
1. **placeholder 檢查**：在 `pr_body.md` 生成後，掃描 `<請填入…>` 或常見未填文字，如果匹配就停止並提示需補內容。
2. **測試敘述檢查**：確認 `測試細節` 中的指令與結果欄位不是原樣 `<請填入…>`，且至少有一組非空字串，若缺失就報錯。
3. **PR 一致性驗證**：從自動推斷的 summary 關鍵詞（commit/branch/issue）中擷取詞語，如「登入」「Cache」「CI」等，確保 PR 標題或 `## 變更摘要` 包含其中任一關鍵詞；否則給予提醒並允許使用者調整。
4. **字面 `\n`/`\n\n` 檢查**：保留現有 `rg -n` 檢查，並在發 PR 前最後再跑一次，必要時提示用自然段落替換。

## 發 PR 前補充檢查
1. **工作樹狀態**：`git status --porcelain` 只允許列出的變更（含 staged/unstaged），若有意外檔案阻擋發 PR，列出差異並中止。
2. **CI 標籤檢查**：若模版要求（例如 `## 測試與驗證` 中至少兩項需勾選），在 `pr_body.md` 中出現 `[ ]` 列表時驗證其文字描述不是 placeholder（非 `單元測試` 以外的描述）並提示補齊。
3. **Issue/branch 對應**：確認 branch 名稱符合 `feat/xxx-...` 或 issue 編號存在，如 `gh issue view <n>` 可以成功，否則警告並請完善 issue reference。

## 實作平方流
1. 先抓取 `CURRENT_BRANCH`、`BASE_BRANCH`、`COMMIT_SUMMARY`、`DIFF_FILES`、`ISSUE`。
2. 呼叫 helper 生 `pr_body.md`，同時記錄 `auto_keywords`、`auto_title_hint`。
3. 依序執行檢查（placeholder → 測試敘述 → keyword match → newline literal），若某步失敗，印出 Diagnostics 並中止。
4. 通過後再執行 `gh pr create`，最後觸發 `review-pr-3x`。

## 使用者呈現與訊息
- 在每项檢查失敗時都提供中文錯誤提示，說明哪一段需要重填並建議的修改方式。
- 每次自動填充的段落應用 `## 自動產生` 標籤或註記，讓使用者清楚哪些內容可直接更新。
- 若 `auto_keywords` 與 PR 標題差距過大，可列出「推論關鍵詞」供使用者參考。

## 風險與未來延伸
- 自動推論若過度簡化可能誤導內容：保持編輯自由，建議只填入參考句；預設先寫草稿，使用者仍可完全重寫。
- 若 `gh issue view` 請求頻繁可加 caching 或依 CI PAT 限制，但目前僅在有 issue/trunk 情況下才呼叫。
- 後續可考慮生成 PR message preview，讓使用者最後確認語氣與排版。
