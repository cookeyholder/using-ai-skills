## ADDED Requirements

### Requirement: 相依解耦模式指引
系統應提供將 Django Signals 邏輯移至明確 Service 層的標準模式。

#### Scenario: 重構 post_save 信號
- **WHEN** 開發者識別出帶有核心業務邏輯的 `post_save` 信號時
- **THEN** 指南應指示將該邏輯移動至 `Service` 方法，並以明確的 Service 呼叫取代信號觸發。

### Requirement: 擴展/遷移/收縮 (Expand/Migrate/Contract) 模式
系統應定義執行資料庫結構變更的三階段安全維護流程。

#### Scenario: 零停機更換欄位
- **WHEN** 需要更換或重命名資料庫欄位時
- **THEN** 指南應規定：(1) 新增可為空的欄位，(2) 透過指令回填資料，(3) 棄用並移除舊欄位。

### Requirement: 資料補償式回滾 SOP
系統應針對重構部署失敗後的資料不一致情況，提供標準的補償流程。

#### Scenario: 資料遷移腳本失敗
- **WHEN** 資料遷移腳本導致資料庫處於不一致狀態時
- **THEN** 指南應提供「修復/補償指令」模板，用於識別並修正受影響的紀錄。
