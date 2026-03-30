---
name: review-fix
description: 全方位進行專案程式碼審查，產生詳細且清楚的審查報告，並根據報告自動建立 OpenSpec change 的所有提案文件，用來規劃並修復所有發現的問題。
license: MIT
metadata:
    version: "1.1"
---

# 全方位程式碼審查與 OpenSpec 修復提案自動化

當使用者要求全面程式碼審查（Comprehensive Code Review）並建立對應的 OpenSpec 修復計畫時，請自動執行以下兩個主要階段：

## 階段一：全面程式碼審查 (Comprehensive Code Review)

1. **蒐集專案脈絡：**
    - 運用您的檔案讀取與搜尋工具掃描目前專案結構與核心模組（包含前端與後端、配置檔等）。
    - 閱讀 `README.md` 或其他架構文件了解系統現況與業務邏輯。

2. **多維度深入分析：**
   請以擁有 20 年經驗的資深架構師與資安工程師的視角，針對以下面向進行最嚴格的審查：
    - **資安 (Security)**：權限控管、SQL/XSS 防禦、CSRF、資料洩露風險、不安全的配置、過期的依賴套件。
    - **效能 (Performance)**：N+1 查詢問題、記憶體洩漏風險、大資料量處理瓶頸、資源未釋放問題。要求在修復過程中絕對不能犧牲系統的執行效能。
    - **Clean Code 與規範 (Code Style)**：程式碼可讀性、DRY (Don't Repeat Yourself)、SOLID 原則、命名慣例、是否符合嚴格的 Linter 規範（Python Ruff/mypy 嚴格模式，JS/TS ESLint）、型別註解完整度、Docstring/JSDoc 說明。
    - **架構與老舊遺跡 (Architecture & Legacy)**：不符合目前架構方向的技術債、過時套件綁定、高耦合或職責不清的模組。
    - **潛在邏輯錯誤 (Logic Bugs)**：極端情境邊界值漏判、錯誤處理與重試機制、交易 (Transaction) 完整性。
    - **使用者體驗 (UX)**：錯誤提示是否友善、有無包含敏感系統資訊。

3. **產出審查報告：**
    - 將所有發現的問題彙整，建立一份結構清晰、詳細的 Markdown 文件。
    - 為每個問題標示優先級別（例如：`P0_CRITICAL` 致命, `P1_HIGH` 嚴重, `P2_MEDIUM` 中等, `P3_LOW` 輕微）。
    - 將詳細的審查報告儲存至專案目錄的 `docs/CODE_REVIEW_REPORT.md`（若是後續的迭代審查，則附加在原報告後方或建立新版本的報告，例如 `docs/CODE_REVIEW_REPORT_v2.md`）。

## 階段二：建立 OpenSpec 修復提案 (OpenSpec Change Creation)

在產出報告後，須自動把這些問題轉化為具有行動力的 OpenSpec 修改提案：

1. **建立新的 OpenSpec Change：**
    - 根據審查總結，提出一個適合的 change 名稱，例如 `comprehensive-code-review-fixes` 或針對特定模組更具體的名稱（若是迭代修復可附加序列號，如 `fixes-iteration-2`）。
    - 執行 bash 指令建立 change，例如：`openspec new change "comprehensive-code-review-fixes"`。

2. **產生並填寫 OpenSpec 提案文件：**
   主動根據審查報告來撰寫接下來的核心計畫 artifacts，省去使用者反覆確認的步驟：
    - **Proposal (`proposal.md`)**：
      執行 `openspec instructions proposal --change "<change-name>"`。
      說明發起原因為全面程式碼審查，目標為消除 P0-P3 的各項風險，並列出影響範圍。
    - **Design (`design.md`)**：
      執行 `openspec instructions design --change "<change-name>"`。
      針對報告中提出的問題，逐一給出詳細的架構修改或技術實作設計。**必須確保設計符合 Clean Code 標準並兼顧最佳執行效能**。
    - **Tasks (`tasks.md`)**：
      執行 `openspec instructions tasks --change "<change-name>"`。
      將修復設計拆解為具體、細粒度可執行的開發與測試步驟，並包含驗收標準 (AC)。

## 階段三：全自動迭代修復與文件同步循環 (Fully Automated Iterative Review-Fix Cycle)

由於一次修復可能無法根絕所有問題，或者修復過程中可能產生新的副作用，因此必須採用 **「自動審查 $\to$ 自動修復 $\to$ 自動審查」** 的無縫迭代循環：

1. **自動啟動實作：** 階段二的文件建立並驗證就緒後，請**主動啟動 `/opsx-apply` (或執行 `openspec-apply-change` 原理流程)** 來根據 `tasks.md` 自動完成所有程式碼修復與測試，不需要等待使用者下指令。
2. **自動二次審查：** 當一輪的修復任務完成後，必須**自動**再次執行 **階段一、二**，對修復後的程式碼進行嚴格的二次審查。
3. **建立新一輪提案：** 若發現新的問題、未完全修復的舊問題，或是不符合 Clean Code 與效能標準的實作，則產生新的審查報告，並自動建立下一輪的 OpenSpec change 修復任務（如 `fixes-iteration-2`），然後回到第 1 步繼續自動實作。
4. **直到完美為止：** 此循環將持續自動進行，**直到確認專案內所有的程式碼皆以最安全、效能最佳、且符合 Clean Code 的方式重構和修復為止**。
5. **對應與擴充測試 (Update & Add Tests)：** 由於新程式碼或架構的加入，原本的測試程式碼可能無法直接對接或覆蓋率不足。在更新文件前，**必須**調整現有測試或新增測試程式，確保所有測試皆與最新的程式碼行為一致。
6. **確保測試綠燈 (Ensure Tests / CI Pass)：** **必須要執行並通過專案內所有的測試，或確認 CI 流程成功完成**，證明修復成果沒有破壞任何既有功能。
7. **更新專案文件 (Update Documentation)**：當該循環的程式碼變更與審查完全通過（即再也找不到 P0-P3 問題），且所有測試均 PASS 後，**必須**盤點受影響的業務邏輯、配置或 API 介面，並相應地自動更新：
    - 專案根目錄的 `README.md`。
    - 專案內 `docs/` 資料夾（或其他專用文件資料夾）中的相關文件與架構圖說明，確保文件與最新的程式碼實作保持絕對一致。
8. **移除中間版本文件 (Remove Intermediate Versions)**：在最終確認專案已達到 Clean Code 與效能要求，且所有文件已更新完畢後，**可以選擇性地將中間版本的審查報告與提案文件（如 `CODE_REVIEW_REPORT_v2.md`、`fixes-iteration-2` 等）進行整理或歸檔**，以保持專案文件的整潔與可讀性。
9. **歸檔中間產生的迭代修復 OpenSpec Change (Archive OpenSpec Change)**：當確認該系列的修復任務已完全結束，且專案已達到預期的品質標準後，**請執行 `openspec archive change "<change-name>"` 來正式歸檔該 OpenSpec change**，並在 CHANGELOG.md 中記錄此次修復的核心內容與影響。

## 輸出回報 (Output)

在過程中可適時讓使用者知道目前進度。當「所有迭代循環完全結束」且「文件更新完畢」後，請以「臺灣繁體中文」向使用者總結：

1. `docs/CODE_REVIEW_REPORT.md`（及其迭代版本）已產生，並簡述盤點與修復的核心問題。
2. 已歷經多少次的自動循環修復，並且專案已達標 Clean Code 與效能要求。
3. `README.md` 與 `docs/` 相關文件已經同步更新完畢。

## 效率強化：快速啟動腳本 (Bootstrap Script)

為了降低重複工，先執行以下腳本自動產生審查骨架與 OpenSpec 指令清單，再進入人工審查與修復：

```bash
python3 review-fix/scripts/bootstrap_review_fix.py --repo .
```

常用參數：

- `--change-name <name>`：指定 OpenSpec change 名稱。
- `--report-out <path>`：指定報告輸出位置（預設 `docs/CODE_REVIEW_REPORT.md`）。
- `--plan-out <path>`：指定 OpenSpec 計畫輸出位置（預設 `docs/OPENSPEC_REVIEW_FIX_PLAN.md`）。
- `--print-only`：僅輸出內容，不寫入檔案。

### 迭代停止條件（建議）

避免無限循環，最多迭代 3 輪；若連續 2 輪無新增 P0/P1 問題，或僅剩 P3 非阻斷項，即可結束並彙整後續改善項目。
