---
name: review-fix
description: 全方位進行專案程式碼審查，產生詳細且清楚的審查報告，並根據報告自動建立 OpenSpec change 的所有提案文件，用來規劃並修復所有發現的問題。另支援供 review-pr 等流程呼叫的輕量驗證模式。
license: MIT
metadata:
    version: "2.2"
    # disable-model-invocation: true is intentionally omitted because
    # other skills (review-pr, refactor-django, etc.) may trigger this
    # skill via description matching when users request code reviews.
---

# 全方位程式碼審查與 OpenSpec 修復提案自動化

本 skill 提供兩種模式：

- **完整模式（預設）**：前置作業 → 階段一（全面審查）→ 階段二（建立 OpenSpec 提案）→ 階段三（迭代修復循環）→ 階段四（收尾與回報）。
- **輕量驗證模式**：由 `review-pr`、`review-pr-2x` 等流程於 commit/push 前呼叫，或使用者明確要求「只驗證、不走完整流程」時採用；僅審查改動範圍並執行測試驗證，不切分支、不建立 OpenSpec change、不產出完整報告、不整併文件、不詢問發 PR。規範見「附錄 B」。

## 前置作業

1. **建立修復分支：** 在任何實作開始前，先從目前分支切出專用修復分支（例如 `review-fix/<change-name>`），名稱需可追溯本輪 review-fix change。

2. **執行 bootstrap 腳本：** 自動產生審查骨架與 OpenSpec 指令清單，降低重複工：

    ```bash
    python3 "$(codegraph which review-fix)/scripts/bootstrap_review_fix.py" --repo .
    ```

    > **備援：** 若 `codegraph` CLI 不可用，請先 `cd` 至 skills 根目錄，再執行相對路徑：`python3 review-fix/scripts/bootstrap_review_fix.py --repo .`。

    常用參數：

    - `--change-name <name>`：指定 OpenSpec change 名稱。
    - `--report-out <path>`：指定報告輸出位置（預設 `docs/CODE_REVIEW_REPORT.md`）。
    - `--plan-out <path>`：指定 OpenSpec 計畫輸出位置（預設 `docs/OPENSPEC_REVIEW_FIX_PLAN.md`）。
    - `--print-only`：僅輸出內容，不寫入檔案。

3. **依賴安全掃描：**

    ```bash
    # npm
    npm audit --production 2>/dev/null || true
    # pip
    pip-audit 2>/dev/null || true
    # trivy
    trivy filesystem --severity HIGH,CRITICAL . 2>/dev/null || true
    ```

    若任一掃描回報 `CRITICAL` 漏洞，需先記錄至審查報告再進行修復。

4. **提交紀律（橫向規範，適用全程）：**
    - **高頻提交（Small-Batch Commits）**：每完成一個小階段就立即提交，不可累積大量變更才一次提交。
    - 小階段範例：完成一個漏洞修補、完成一組對應測試、完成一份 OpenSpec artifact、完成一輪文件整併。
    - 每筆 commit 訊息需清楚描述該小階段目的與影響範圍；建議前綴順序：`fix:`（漏洞修補）→ `test:`（測試補強）→ `docs:`（報告與文件同步）→ `chore:`（文件整併/歸檔與收尾）。
    - 最終應留下一組可閱讀的 commit 歷史，能清楚追溯每個修復階段。

## 階段一：全面程式碼審查

1. **蒐集專案脈絡：**
    - 運用檔案讀取與搜尋工具掃描目前專案結構與核心模組（包含前端與後端、設定檔等）。
    - 閱讀 `README.md` 或其他架構文件了解系統現況與業務邏輯。

2. **多維度深入分析：**
   請以擁有 20 年經驗的資深架構師與資安工程師的視角，針對以下面向進行最嚴格的審查：
    - **資安 (Security)**：權限控管、SQL/XSS 防禦、CSRF、資料洩露風險、不安全的設定、過期的依賴套件。
    - **效能 (Performance)**：N+1 查詢問題、記憶體洩漏風險、大資料量處理瓶頸、資源未釋放問題。要求在修復過程中絕對不能犧牲系統的執行效能。
    - **Clean Code 與規範 (Code Style)**：程式碼可讀性、DRY (Don't Repeat Yourself)、SOLID 原則、命名慣例、是否符合嚴格的 Linter 規範（Python Ruff/mypy 嚴格模式，JS/TS ESLint）、型別註解完整度、Docstring/JSDoc 說明。
    - **架構與老舊遺跡 (Architecture & Legacy)**：不符合目前架構方向的技術債、過時套件綁定、高耦合或職責不清的模組。
    - **潛在邏輯錯誤 (Logic Bugs)**：極端情境邊界值漏判、錯誤處理與重試機制、交易 (Transaction) 完整性。
    - **使用者體驗 (UX)**：錯誤提示是否友善、有無包含敏感系統資訊。

3. **平行審查編排（Subagent 可用時）：**
   同時啟動 4 個 explorer，主責如下：
    - `security-explorer`：認證授權、輸入驗證、敏感資訊、注入風險。
    - `performance-explorer`：N+1、重複計算、I/O 熱點、快取策略。
    - `quality-explorer`：複雜度、重複邏輯、型別與可維護性。
    - `test-explorer`：測試覆蓋缺口、脆弱測試、CI 風險。

   每個 explorer 都必須輸出：
    - 依嚴重度排序的問題清單（含檔案與行號）。
    - 最多 3 個高價值修復建議（可落地、可驗證）。
    - 需要驗證的假設與潛在誤判。

   提示詞模板見「附錄 A」。

   **降級策略：** 若 subagent 環境無法啟動（例如 API 限制或不支援並行），改為線性執行：依序 security → performance → quality → test 分析，由主 agent 手動合併結果，並於最終輸出註明「以線性模式執行（subagent 不可用）」。

4. **整合與分級（主 agent）：**
    - 合併 4 份結果並去重。
    - 統一分級到 `P0_CRITICAL`、`P1_HIGH`、`P2_MEDIUM`、`P3_LOW`。

5. **產出審查報告：**
    - 將所有發現的問題彙整，建立一份結構清晰、詳細的 Markdown 文件。
    - 為每個問題標示優先級別；**報告全文必須使用「臺灣慣用語」的繁體中文撰寫**（包含標題、內文、建議與結論；避免簡體中文與中國慣用詞）。
    - 儲存至專案目錄的 `docs/CODE_REVIEW_REPORT.md`；迭代版本最終須回寫整併至同一主檔（見階段三「文件整併」）。

## 階段二：建立 OpenSpec 修復提案

在產出報告後，須自動把這些問題轉化為具有行動力的 OpenSpec 修改提案：

1. **建立新的 OpenSpec Change：**
    - 根據審查總結，提出一個適合的 change 名稱，例如 `comprehensive-code-review-fixes` 或針對特定模組更具體的名稱（若是迭代修復可附加序列號，如 `fixes-iteration-2`）。
    - 執行 bash 指令建立 change，例如：`openspec new change "comprehensive-code-review-fixes"`。

2. **產生並填寫 OpenSpec 提案文件（每輪僅建立單一 change，避免一輪多 change 造成分散）：**
   主動根據審查報告來撰寫核心計畫 artifacts，省去使用者反覆確認的步驟：
    - **Proposal (`proposal.md`)**：執行 `openspec instructions proposal --change "<change-name>"`。說明發起原因為全面程式碼審查，目標為消除 P0-P3 的各項風險，並列出影響範圍。
    - **Design (`design.md`)**：執行 `openspec instructions design --change "<change-name>"`。針對報告中提出的問題，逐一給出詳細的架構修改或技術實作設計。**必須確保設計符合 Clean Code 標準並兼顧最佳執行效能**。
    - **Tasks (`tasks.md`)**：執行 `openspec instructions tasks --change "<change-name>"`。將修復設計拆解為具體、細粒度可執行的開發與測試步驟，並包含驗收標準 (AC)。

3. **OpenSpec CLI 不可用時的備援：**
   若目標專案未導入 OpenSpec CLI，跳過上述 `openspec` 指令，改以 bootstrap 產生的 `docs/OPENSPEC_REVIEW_FIX_PLAN.md` 保存提案內容；後續階段中所有 `openspec` 相關動作（apply、archive）對應改為人工執行或略過。

## 階段三：迭代修復循環

由於一次修復可能無法根絕所有問題，或者修復過程中可能產生新的副作用，因此採用 **「自動審查 → 自動修復 → 自動審查」** 的無縫迭代循環：

1. **自動啟動實作：** 階段二的文件建立並驗證就緒後，請**主動啟動 `/opsx-apply`（或執行 `openspec-apply-change` 原理流程）**來根據 `tasks.md` 自動完成所有程式碼修復與測試，不需要等待使用者下指令。

2. **平行修復編排（Subagent 可用時）：**
   依模組切分 ownership 後，啟動多個 worker 平行修復。每位 worker 必須：
    - 僅修改分配到的檔案範圍，避免跨區衝突。
    - 同步補測試（或更新既有測試）。
    - 回報實際變更檔案、驗證方式、剩餘風險。

   協作規範：
    - 禁止不同 worker 修改同一檔案（除非主 agent 明確排程）。
    - 若發現 blocker，worker 先回報，不自行擴大改動邊界。
    - 主 agent 不重做 worker 的分析工作，只做整合與裁決，最後統一執行全域測試與回歸確認。
    - 提示詞模板見「附錄 A」。

   **降級策略：** subagent 不可用時，依 `tasks.md` 順序由主 agent 逐項修復與測試。

3. **自動二次審查：** 當一輪的修復任務完成後，必須**自動**重跑階段一、二，對修復後的程式碼進行嚴格的二次審查。

4. **進入下一輪：** 若發現新的問題、未完全修復的舊問題，或是不符合 Clean Code 與效能標準的實作，則產生新的審查報告，並自動建立下一輪的 OpenSpec change 修復任務（如 `fixes-iteration-2`），然後回到第 1 步繼續自動實作。若本輪審查乾淨但尚未滿足「連續 2 輪無新增 P0/P1」的成功條件，則不建立新 change，直接重複本階段的審查與測試步驟，直到成功條件滿足或達到 3 輪上限。

5. **對應與擴充測試 (Update & Add Tests)：** 由於新程式碼或架構的加入，原本的測試程式碼可能無法直接對接或覆蓋率不足。**必須**調整現有測試或新增測試程式，確保所有測試皆與最新的程式碼行為一致。

6. **確保測試綠燈 (Ensure Tests / CI Pass)：** **必須**執行並通過專案內所有的測試，或確認 CI 流程成功完成，證明修復成果沒有破壞任何既有功能。執行測試前，請先從專案設定檔自動發現測試指令（依序檢查 `package.json` → `pyproject.toml` → `Cargo.toml` → `Makefile`）。

7. **停止條件：**
    - **成功停止：** 連續 2 輪無新增 P0/P1 問題，且無任何未解決的 P0-P2（僅剩 P3 非阻斷項視為通過）→ 進入後續文件更新與歸檔步驟。
    - **上限停止：** 最多迭代 3 輪。若達到上限仍有未解決的 P0-P2，停止迭代並輸出剩餘阻斷項清單與建議，**不得視為修復完成**，不進入文件整併與歸檔完成宣告。
    - **單輪超時控制：** 每輪修復設定最長執行時間（如 30 分鐘）。若該輪修復在時間內未完成，先輸出當前進度（已修復項目與未修復項目），然後依停止條件判斷是否進入下一輪。

8. **更新專案文件 (Update Documentation)：** 當「成功停止」條件成立且所有測試 PASS 後，**必須**盤點受影響的業務邏輯、設定或 API 介面，並相應地自動更新：
    - 專案根目錄的 `README.md`。
    - 專案內 `docs/` 資料夾（或其他專用文件資料夾）中的相關文件與架構圖說明，確保文件與最新的程式碼實作保持絕對一致。
    - 若修補結果有「值得提醒使用者」的操作、安全、部署或相容性注意事項，**必須**寫入現有文件（例如 README 或對應 `docs/*`），不得只留在對話訊息中。
    - 文件更新時，**必須同步移除或改寫過時內容**，避免新舊規範並存造成誤導。

9. **文件整併 (Documentation Consolidation)：** 將 `docs/` 底下的重複與版本化審查檔案（如 `CODE_REVIEW_REPORT_v2.md`）及中間提案文件整併至單一 canonical 檔案，並清理或歸檔中間檔至 `docs/archive/review-fix/`。確認 `docs/` 根目錄僅保留一份 canonical 檔案。

10. **歸檔 OpenSpec Change (Archive OpenSpec Change)：** 當確認該系列的修復任務已完全結束，且專案已達到預期的品質標準後，執行 `openspec archive change "<change-name>"` 正式歸檔該 OpenSpec change，並在 `CHANGELOG.md` 中記錄此次修復的核心內容與影響。若專案未使用 OpenSpec，依階段二第 3 點的備援方式處理。

## 階段四：收尾與回報

1. **輸出回報：** 當所有迭代循環完全結束且文件更新完畢後，請以「臺灣繁體中文」向使用者總結：
    1. `docs/CODE_REVIEW_REPORT.md`（及其整併歷程）已產生，並簡述盤點與修復的核心問題。
    2. 已歷經多少次的自動循環修復，並且專案已達標 Clean Code 與效能要求。
    3. `README.md` 與 `docs/` 相關文件已經同步更新完畢。
    4. 若有重要提醒事項，已寫入對應文件且可被長期追蹤。
    5. 已完成 `docs/` 重複 Markdown 的整併，並說明 canonical 檔案與歸檔位置。
    6. 已完成分支建立與高頻提交摘要（列出關鍵 commit 階段）。
    7. 已列出本輪「新增提醒內容」與「移除/改寫的過時內容」清單。

2. **PR 收尾動作（僅完整模式）：** 當上述流程全部完成（含文件整併與最終 commit）後，**必須主動詢問使用者是否要發起 PR**，再進行後續 PR 建立動作。

## 附錄 A：Subagent 提示詞模板

Explorer 模板：

```text
你是 {domain} explorer。請只做審查，不要改碼。
輸出：
1) Findings（含檔案:行號，依嚴重度排序）
2) Top 3 修復建議（含驗證方法）
3) 不確定假設與需要人工確認項目
```

Worker 模板：

```text
你是 {module} worker，負責檔案範圍：{owned_files}。
你不是唯一在此 repo 工作的 agent，不可回退他人變更。
目標：修復指定 findings，補齊必要測試，回報變更檔案與測試結果。
```

## 附錄 B：輕量驗證模式（供 review-pr 等流程呼叫）

**適用時機：** 由 `review-pr`、`review-pr-2x` 於 commit/push 前呼叫，或使用者明確要求「只驗證、不走完整流程」時。

**執行範圍：**

1. 只審查本次改動範圍，且**必須涵蓋尚未提交的變更與未追蹤檔案**（例如並用 `git diff <base>...HEAD --name-only`、`git diff HEAD --name-only` 與 `git ls-files --others --exclude-standard` 列出），聚焦：正確性、安全性、測試覆蓋，以及是否夾帶與本次範圍無關的改動。
2. 執行受影響範圍的測試與 lint（測試指令的發現順序同階段三第 6 點）。
3. 輸出可執行的 findings 清單（含檔案:行號、嚴重度、建議修法）。
4. 若發現問題，修正後重跑本模式，直到沒有未解決的 actionable findings。

**明確排除（避免與 PR 流程衝突）：** 不切換或建立新分支、不建立 OpenSpec change、不產生 P0-P3 完整審查報告、不做文件整併、不詢問發起 PR、不啟動子代理平行化（除非呼叫者明確要求）。

輕量模式驗證通過後，呼叫端流程（如 `review-pr` 步驟 6）即可繼續進行 commit/push。
