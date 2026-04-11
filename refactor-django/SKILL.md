---
name: refactor-django
description: 任意 Django 專案的波浪式重構工作流程。觸發詞：refactor、重構、service 層抽取、測試覆蓋率提升、fat view、fat model、技術債清理、clean code、service layer、安全網測試、Django 重構、type hints。
license: MIT
metadata:
    version: "2.0"
---

# Django 波浪式重構工作流程

## 目錄 (Table of Contents)

- [核心流程管線 (Core Pipeline)](#核心流程管線-core-pipeline)
    - [Wave 1：現況分析與測試安全網](#wave-1現況分析與測試安全網)
    - [Wave 2：實作重構與 Service 抽取](#wave-2實作重構與-service-抽取)
    - [Wave 3：工具整備與型別補強](#wave-3工具整備與型別補強)
    - [Wave 4：收尾與強制門檻](#wave-4收尾與強制門檻)
- [專家戰術指南 (Expert Tactical Guide)](#專家戰術指南-expert-tactical-guide)
    - [相依解耦 (Decoupling)](#相依解耦-decoupling)
    - [安全代碼遷移 (Zero-downtime Migration)](#安全代碼遷移-zero-downtime-migration)
    - [進階測試模式](#進階測試模式)
    - [關鍵技術決策清單](#關鍵技術決策清單)

---

## 核心流程管線 (Core Pipeline)

### 核心哲學：Safety Net First（安全網優先）
> **永遠先補測試，再動邏輯。** 確保重構過程中測試持續通過。

---

### Wave 1：現況分析與測試安全網 (Analysis & Safety Net)

**目標：** 在不變動任何業務邏輯的前提下，摸清專案底細並建立防回歸的安全網。

#### 1.1 分析現況 (Discovery Checklist)
- [ ] **執行快照**：使用 `django-snapshot` 產生 `snapshot.json`，掌握專案分佈。
- [ ] **產生覆蓋率報告**：`pytest --cov=src --cov-report=html`。
- [ ] **三輪掃描 (via code-reviewer)**：
    - 第一輪：識別 Service 候選者。
    - 第二輪：識別 Clean Code 問題。
    - 第三輪：識別資安風險。

#### 1.2 建立安全網 (Safety Net)
- [ ] **建立測試基礎設施**：設定 `factories.py` 與 `conftest.py`。
- [ ] **View 整合測試**：優先覆蓋「守衛場景」（403/302）與「Happy Path」（200）。

---

### Wave 2：實作重構與 Service 抽取 (Implementation & Refactoring)

**目標：** 執行原子化的業務邏輯遷移與解耦。

#### 2.1 建立 OpenSpec 提案 (Proposal Strategy)
- [ ] **建立 Parent 提案**：管理整體進度。
- [ ] **建立 Child 提案**：遵循 `refactor-wave2-{NN}-{slug}` 命名。

#### 2.2 實作與審查 (Execution Loop)
- [ ] **原子化實作**：使用 `openspec-apply-change` 實施邏輯搬移。
- [ ] **持續掃描**：每完成一個核心 Task，使用 `review-fix` 進行最嚴格掃描。
- [ ] **品質查核**：
    - `Thin View`：邏輯 < 10 行。
    - `Service Object`：單一職責、靜態入口、具備 Dataclass 與錯誤型別。

#### 2.3 Model 與 Signals 解耦
- [ ] **Model 減脂**：業務流程搬至 Service，Model 僅留資料結構與純計算 property。
- [ ] **斷開 Signal 鏈**：改為在 Service 中「明確呼叫」。

---

### Wave 3：工具整備與型別補強 (Tooling & Types)

**目標：** 透過強型別與靜態工具規範新代碼品質，避免回潮。

- [ ] **mypy 整備**：設定 `disallow_untyped_defs = true` 並對 Service 層標註型別。
- [ ] **pre-commit 整合**：導入 `ruff` 與 `djlint` 掃描。
- [ ] **Celery Tasks 重構**：改為 `Thin Task` 模式，商務邏輯委託 Service 執行。

---

### Wave 4：收尾與強制門檻 (Completion & Enforcement)

**目標：** 彙整遺漏項並設定 CI 護欄。

- [ ] **彙整收尾 PR (Final Followups)**：集中優化子 PR 遺漏的 Review 留言。
- [ ] **設定覆蓋率護欄**：在 `pyproject.toml` 開啟 `--cov-fail-under=85`。
- [ ] **歸檔 OpenSpec Change**：執行 `openspec archive change`。

---

## 專家戰術指南 (Expert Tactical Guide)

### 相依解耦 (Decoupling Tactics)

#### 中斷 Signal 鏈 (Interrupting Signal Chain)
1. **明確呼叫**：將業務關聯從 Signal 搬到 Service。
2. **靜音 Signal (Silent Save)**：極端情況使用 `filter(...).update(...)`。
3. **輕量化 Handler**：Signal 只負責 Audit Log 等非關鍵動作。

#### 解決循環引用 (Handling Circular Imports)
- **延遲匯入 (Local Import)**：在方法內部匯入。
- **TYPE_CHECKING**：僅在型別檢查時匯入，配合 `from __future__ import annotations`。

---

### 安全代碼遷移 (Zero-downtime Migration)
**模式：Expand / Migrate / Contract**
1. **Expand**：新增欄位，代碼同時寫入新舊欄位。
2. **Migrate**：執行 Data Migration 將存量資料搬移至新欄位。
3. **Contract**：確認資料一致後，代碼改由新欄位讀取，並移除舊欄位。

---

### 回滾與故障排除 (Rollback & Troubleshooting)
- **代碼回退**：執行 `git revert <commit>`。
- **資料補償**：準備反向 Data Migration，或利用 Audit Log 回復。
- **監控指標**：觀察 `HTTP 5xx` 率、`Database Locking Timeout` 與 `Celery` 隊列情況。

---

### 進階測試模式 (Advanced Testing Patterns)

#### 測試基礎設施範例
```python
class UserFactory(DjangoModelFactory):
    class Meta:
        model = get_user_model()
    username = factory.Sequence(lambda n: f"user_{n}")

class ArticleFactory(DjangoModelFactory):
    class Meta:
        model = "blog.Article"
    author = factory.SubFactory(UserFactory)
    class Params:
        published = factory.Trait(status="published")
```

#### View 整合測試與 Mocking
- **守衛測試**：確保 302/403 邏輯正確。
- **Mocking**：使用 `unittest.mock.patch` 隔離外部服務。

---

### 關鍵技術決策清單 (Decision Table)

| 決策點       | 建議做法                                               |
| ------------ | ------------------------------------------------------ |
| Service 輸入 | `@dataclass(frozen=True)`                              |
| 錯誤處理     | `XxxServiceError(ValueError)` + `field` 屬性           |
| 並發保護     | `select_for_update()` + `atomic`                       |
| Model 邊界   | 純計算 property 留 Model；業務流程移 Service           |
| Signal 替代  | 核心流程改「明確呼叫」；次要動作（Log）留 Signal        |
| Celery 模式  | Thin Task (只做重試) + Service (商務邏輯)              |
| 覆蓋率排除   | `migrations`, `manage.py`, `generate_testing_data`     |
