## ADDED Requirements

### Requirement: 結構化內容編排
技能文件應劃分為「核心管線 (Core Pipeline)」與「專家戰術指南 (Expert Tactical Guide)」兩大部分。

#### Scenario: 存取核心工作流
- **WHEN** 使用者開啟技能文件時
- **THEN** 核心的 4-Wave 管線應位於文件的正文開頭部分，方便快速閱讀。

### Requirement: 濃縮重構生命週期
技能應定義精確的 4 個 Wave，以涵蓋完整的重構生命週期。

#### Scenario: 將 10 個階段對應至 4 個 Wave
- **WHEN** 更新文件內容時
- **THEN** 原有的 10 個階段必須無損地整合至新的 4-Wave 架構中（Wave 1: 分析佈樁, Wave 2: 實作重構, Wave 3: 品質與工具, Wave 4: 收尾歸檔）。
