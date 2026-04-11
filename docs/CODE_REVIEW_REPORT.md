# 程式碼審查報告 (Code Review Report)

## 審查概覽
- **專案/模組**：`refactor-django/SKILL.md`
- **審查日期**：2026-04-11
- **審查者**：Gemini CLI (review-fix skill)
- **當前狀態**：✅ 已完成初步修復

---

## 審查發現 (Findings)

### P0_CRITICAL: 程式碼區塊縮排錯誤導致不可執行
- **位置**：`refactor-django/SKILL.md` 中的 `UserFactory`, `ArticleFactory` (Wave 1) 與 `OrderFactory` (Phase 10) 範例。
- **問題描述**：
  - `factory.Trait` 內部的參數（如 `status`, `published_at`）縮排混亂，出現 11、13、20+ 個空格的狀況。
  - 此種非標準縮排（非 4 或 8 的倍數）在 Python 中可能導致 `IndentationError`，或者雖然在某些 Hanging Indent 情境下可執行但極度不美觀且難以維護。
- **修復建議**：
  - 統一將 `factory.Trait(` 內部的參數縮排至 12 個空格。
  - 移除 `Trait(` 後方多餘的 trailing spaces。
- **狀態**：✅ 已修復 (Fixed)

---

## 改善建議 (Recommendations)

1. **自動化檢查**：建議在 CI 流程中加入對 Markdown 文件中程式碼區塊的語法與縮排檢查，例如使用 `pymarkdown` 或 `mdl` 搭配自定義規則。
2. **範例驗證**：在更新重構指南時，應確保所有提供的代碼範例均能通過 `python3 -m py_compile` 或 `ruff` 檢查。

---

## 結論
本輪審查重點解決了文檔中關鍵範例代碼的執行力問題。目前 `refactor-django/SKILL.md` 的程式碼區塊縮排已恢復標準格式，其餘架構與敘述邏輯符合 OpenSpec 波浪式重構的實務規範。
