## Why

`refactor-django/SKILL.md` 目前過於冗長（26KB+），導致代理人與使用者在工作過程中難以快速、精準地掌握核心重構管線。此外，針對重構實務中高風險的「複雜相依解耦」、「零停機資料庫遷移」與「回滾策略」缺乏標準指南，亟需精進以提升重構效率與安全性。

## What Changes

- **架構重整**：將單一技能文件SHALL 劃分 (SHALL divide)為「核心流程管線 (Pipeline)」與「專家技術指南 (Expert Guide)」兩大部分。
- **流程精確化**：將原本分散的 10 個 Phase SHALL 濃縮 (SHALL condense)為 4 大 Wave（分析佈樁、實作重構、工具整備、收尾歸檔）。
- **新增專家專題**：SHALL 整合 (SHALL integrate)複雜相依處理（解耦 Signal/Circular Imports）、零停機遷移模式（Expand/Migrate/Contract）及回滾 SOP。
- **範例精簡與修復**：修正 Factory 範例縮排並移除冗餘重複的代碼片段。

## Capabilities

### New Capabilities
- `django-expert-tactics`: 提供針對 Django 重構中深度技術挑戰（如遷移與相依解耦）的專家級操作指引。

### Modified Capabilities
- `refactor-django-skill`: 優化現有的 Django 波浪式重構工作流文件結構與內容密度。

## Impact

- **文件影響**：主要修改 `/refactor-django/SKILL.md`。
- **工作流影響**：提升重構任務的執行速度並降低高風險操作（如資料庫異動）的出錯率。
