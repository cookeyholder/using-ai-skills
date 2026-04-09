---
name: refactor-django
description: 任意 Django 專案的波浪式重構工作流程。當使用者想要提升測試覆蓋率、從 Fat View 抽取 Service 層、拆解 Fat Model、解耦 Django signals、修復技術債、整備 type hints / mypy、設定 pre-commit 工具鏈、或需要一套安全且可追蹤的重構計畫時使用。觸發詞：refactor、重構、service 層抽取、測試覆蓋率提升、fat view、fat model、技術債清理、clean code、service layer、安全網測試、Django 重構、type hints。
license: MIT
metadata:
    version: "1.2"
---

# Django 波浪式重構工作流程

這份 skill 封裝了一套可套用於任意 Django 專案的重構流程，涵蓋從覆蓋率分析到 Service 層抽取、Model 拆解、Signal 解耦、Type Hints 整備、Celery 清理，以及 pre-commit 工具鏈設定。

---

## 核心哲學：Safety Net First（安全網優先）

> **永遠先補測試，再動邏輯。**

```
❌ 錯誤順序：重構邏輯 → 補測試（不知道是否破壞了舊行為）
✅ 正確順序：補測試（覆蓋現有行為）→ 重構邏輯（測試持續通過 = 行為未改變）
```

---

## 整體流程概覽

```
[1] 分析現況        → 覆蓋率報告 + Fat View/Model 識別
[2] 規劃提案        → openspec-ff-change（父提案 + 子提案）
[3] Wave 1 安全網   → 純新增測試，不動任何業務邏輯
[4] Wave 2 Service  → 有安全網後，才搬移 View/Model 邏輯
[5] Wave 3 補覆蓋率 → 其餘 App 補足測試至 ≥85%
[6] Wave 4 強制門檻 → CI 加入 --cov-fail-under=85
[7] Wave Final 收尾 → 全部子提案 merge 後，彙整遲到 review 意見再開一個改善 PR
```

---

## Phase 1：現況分析

### 1.1 執行覆蓋率報告

```bash
# 在容器內（或本機）執行
pytest --cov=src --cov-report=html --cov-omit="*/migrations/*,manage.py"
# 開啟 htmlcov/index.html 找出最低覆蓋率 App
```

重點關注：

| 指標             | 高風險閾值 | 行動                               |
| ---------------- | ---------- | ---------------------------------- |
| App 覆蓋率       | < 30%      | Wave 1 優先建立安全網              |
| views.py 行數    | > 300 行   | Fat View 候選，Wave 2 抽取 Service |
| models.py 方法數 | > 15 個    | Fat Model 候選，評估邊界           |

### 1.2 識別樣板 App

找出專案中**已有良好 Service 層**的 App 作為範本：

```
src/<reference_app>/
  services/
    __init__.py
    <domain>_service.py
  tests/
    test_<domain>_service.py
```

---

## Phase 2：建立 OpenSpec 提案

使用 `review-fix` 和 `code-reviewer` 產生審查報告，再用 `openspec-ff-change` 建立波浪式計畫。

### 父提案結構

```
openspec/changes/<project>-refactor/
  proposal.md   # 動機、目標、Non-Goals
  design.md     # 技術決策（D1~Dn）
  tasks.md      # Wave 1-4 的 PR 清單（含依賴關係）
```

### 子提案命名規則

```
refactor-wave{N}-{NN}-{slug}
```

---

## Phase 3：Wave 1 — 建立測試安全網

**只新增測試，零邏輯改動。**

### PR-01：測試基礎設施

`pyproject.toml`（Wave 1 先**不**開 `fail-under`）：

```toml
[tool.pytest.ini_options]
addopts = """
  --cov=src
  --cov-report=html
  --cov-omit=*/migrations/*,manage.py,*/generate_testing_data/*
"""
```

`tests/factories.py`：

```python
import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model

User = get_user_model()

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    password = factory.PostGenerationMethodCall("set_password", "testpass123")

class ArticleFactory(DjangoModelFactory):
    class Meta:
        model = "blog.Article"
    author = factory.SubFactory(UserFactory)   # FK
    title = factory.Faker("sentence", nb_words=5)
    body = factory.Faker("paragraphs", nb=3, as_text=True)

    class Params:
        published = factory.Trait(            # Trait：快速切換狀態
            status="published",
            published_at=factory.Faker("past_datetime"),
        )
```

`tests/conftest.py`：

```python
import pytest
from .factories import UserFactory

@pytest.fixture
def user():
    return UserFactory()

@pytest.fixture
def staff_user():
    return UserFactory(is_staff=True)

@pytest.fixture
def client_for(db):
    """回傳一個已登入指定用戶的 Client 工廠函式"""
    from django.test import Client

    def _make(user):
        c = Client()
        c.force_login(user)
        return c

    return _make
```

### View 整合測試（守衛場景優先）

```python
@pytest.mark.django_db
class TestApplicationUpdateView:
    URL = "/applications/{pk}/update/"

    def test_redirect_unauthenticated(self, client):
        """未登入應導向登入頁"""
        resp = client.get(self.URL.format(pk=1))
        assert resp.status_code == 302

    def test_403_wrong_role(self, client_for, regular_user):
        """角色不符應回 403"""
        c = client_for(regular_user)
        resp = c.get(self.URL.format(pk=1))
        assert resp.status_code == 403

    def test_200_happy_path(self, client_for, staff_user, application_factory):
        """正常情況應顯示表單"""
        app = application_factory(owner=staff_user)
        c = client_for(staff_user)
        resp = c.get(self.URL.format(pk=app.pk))
        assert resp.status_code == 200

    @pytest.mark.parametrize("field,value,expected_field", [
        ("email", "not-an-email", "email"),
        ("phone", "abc", "phone"),
    ])
    def test_form_invalid_returns_errors(
        self, client_for, staff_user, application_factory,
        field, value, expected_field
    ):
        """parametrize：多組無效輸入應各自回傳正確欄位錯誤"""
        app = application_factory(owner=staff_user)
        c = client_for(staff_user)
        resp = c.post(self.URL.format(pk=app.pk), data={field: value})
        assert resp.status_code == 200
        assert expected_field in resp.context["form"].errors
```

---

## Phase 4：Wave 2 — Service 層抽取

### 4.1 Service 層標準結構

```
src/<app>/services/
  __init__.py              # 只匯出公開 class 和 Error（避免循環匯入）
  <domain>_service.py
```

`services/__init__.py`：

```python
from .<domain>_service import DomainService, DomainServiceError

__all__ = ["DomainService", "DomainServiceError"]
```

### 4.2 Service 技術規範

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from django.db import transaction

# ── 輸入：frozen dataclass（可型別檢查、不可變）
@dataclass(frozen=True)
class IssueTicketParams:
    application_id: int
    staff_user_id: int
    note: Optional[str] = None   # 可選欄位放後面

# ── 錯誤：XxxServiceError(ValueError) + field 屬性
class TicketServiceError(ValueError):
    def __init__(self, field: str, message: str) -> None:
        super().__init__(message)
        self.field = field          # ← View 用 form.add_error(e.field, str(e))

# ── Service：靜態方法，無 self 狀態
class TicketService:
    @staticmethod
    @transaction.atomic
    def issue_ticket(params: IssueTicketParams) -> "Application":
        """原子性發放准考證，防止 TOCTOU 競態條件。"""
        application = (
            Application.objects
            .select_for_update()    # 行級鎖（必須在 atomic 內）
            .get(id=params.application_id)
        )
        if application.admission_ticket:
            raise TicketServiceError(
                field="admission_ticket",
                message="此申請書已完成收件。"
            )
        from django.db.models import Max
        setup = Setup.objects.select_for_update().get(id=1)   # 序列化鎖
        max_num = Application.objects.aggregate(Max("admission_ticket"))
        application.admission_ticket = (max_num["admission_ticket__max"] or 0) + 1
        application.save(update_fields=["admission_ticket"])
        return application
```

### 4.3 Thin View 改造

```python
class TakeApplicationView(LoginRequiredMixin, View):
    def form_valid(self, form):
        params = IssueTicketParams(
            application_id=self.kwargs["pk"],
            staff_user_id=self.request.user.id,
        )
        try:
            application = TicketService.issue_ticket(params)
        except TicketServiceError as exc:
            form.add_error(exc.field, str(exc))    # 使用 exc.field 而非硬編碼
            return self.form_invalid(form)
        return redirect("registration:show_ticket", pk=application.pk)
```

---

## Phase 5：Model 層重構

### 邊界規則（何者留在 Model，何者移至 Service）

| 場景                          | 推薦位置         | 理由                   |
| ----------------------------- | ---------------- | ---------------------- |
| `__str__`, `get_absolute_url` | Model            | Django 慣例            |
| `@property` 純計算展示值      | Model            | 無副作用，不做 DB 查詢 |
| `clean()` 欄位級驗證          | Model            | DB 層保障，仍可呼叫    |
| 涉及多個 Model 的業務邏輯     | Service          | 真正的業務流程         |
| 發送通知/觸發其他動作         | Service          | 避免隱藏副作用         |
| 複雜 queryset 組裝            | Manager/QuerySet | 讓 Service 呼叫        |

### Fat Model 重構範例

```python
# ❌ 重構前：Model 承擔過多
class Order(models.Model):
    def complete(self):
        # 複雜業務邏輯
        self.status = "completed"
        self.save()
        send_email(self.user.email, "訂單完成")   # 副作用！
        inventory_deduct(self.items.all())         # 跨 Model 操作
        generate_invoice(self)

# ✅ 重構後：Model 只保留資料結構
class Order(models.Model):
    status = models.CharField(...)

    @property
    def is_paid(self) -> bool:    # 純計算，無副作用
        return self.status == "paid"

    def __str__(self) -> str:
        return f"Order #{self.pk}"

# Service 承擔業務流程
class OrderService:
    @staticmethod
    @transaction.atomic
    def complete_order(params: CompleteOrderParams) -> Order:
        order = Order.objects.select_for_update().get(id=params.order_id)
        order.status = "completed"
        order.save(update_fields=["status"])
        EmailService.send_order_completion(order)
        InventoryService.deduct(order.items.all())
        return order
```

---

## Phase 6：Django Signals 解耦

### Signals 的隱藏耦合問題

```python
# ❌ 問題：signal handler 隱藏在別處，難以追蹤、測試困難
@receiver(post_save, sender=Application)
def _on_application_saved(sender, instance, created, **kwargs):
    if created:
        send_welcome_email(instance)    # 無法在 Service 測試中控制
```

### 診斷：何時用 Signal vs. 明確呼叫

| 判斷條件                                   | 推薦方式                        |
| ------------------------------------------ | ------------------------------- |
| 邏輯屬於目前 App 的核心業務流程            | **明確呼叫** Service 方法       |
| 跨 App 的次要動作（如 audit log、metrics） | Signal 可接受                   |
| 測試時需要精確控制是否觸發                 | **明確呼叫**（Signal 難以測試） |
| 第三方 App 觸發的後置動作                  | Signal 通常是唯一選擇           |

### 解耦步驟

```python
# Step 1：在 Service 中明確呼叫
class ApplicationService:
    @staticmethod
    def create_application(params: CreateApplicationParams) -> Application:
        app = Application.objects.create(**asdict(params))
        EmailService.send_welcome_email(app)    # 明確、可測試
        return app

# Step 2：保留 signal 但只做輕量操作（logging/metrics）
@receiver(post_save, sender=Application)
def _log_application_created(sender, instance, created, **kwargs):
    if created:
        logger.info("application_created", extra={"id": instance.pk})
```

---

## Phase 7：Type Hints 與 mypy 整備

### pyproject.toml 設定

```toml
[tool.mypy]
python_version = "3.13"
ignore_missing_imports = true       # 初期：忽略第三方缺型別
disallow_untyped_defs = true        # 所有函式須有完整 annotations
warn_return_any = true
warn_unused_ignores = true
# 逐步強化：等 100% 通過後再加 strict = true
```

### Service 層 type annotation 範例

```python
from __future__ import annotations
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from myapp.models import Application

class TicketService:
    @staticmethod
    def issue_ticket(params: IssueTicketParams) -> Application: ...

    @staticmethod
    def invalidate_ticket(
        application_id: int,
        reason: Optional[str] = None,
    ) -> bool: ...
```

### CI 整合

```yaml
# .github/workflows/ci.yml
- name: Type check
  run: mypy src/ --config-file pyproject.toml
```

---

## Phase 8：Celery Tasks 重構

### 標準模式：Thin Task + Service 分離

```python
# src/<app>/tasks.py — Thin wrapper，只負責重試邏輯
from celery import shared_task
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, time_limit=60)
def send_enrollment_email_task(self, params_dict: dict) -> None:
    """發送課程報名確認信。"""
    try:
        import <app>.services.email_service as email_service
        email_service.send_enrollment_email(**params_dict)
    except email_service.EmailServiceError as exc:
        logger.warning("email_send_failed", extra={"error": str(exc), "params": params_dict})
    except Exception as exc:
        # 指數退避重試
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

```python
# src/<app>/services/email_service.py — 純 Python，可獨立測試
def send_enrollment_email(user_id: int, course_id: int) -> None:
    """發送報名確認信（不依賴 Celery，可直接呼叫測試）"""
    user = User.objects.get(pk=user_id)
    course = Course.objects.get(pk=course_id)
    send_mail(
        subject=f"報名成功：{course.name}",
        message=render_to_string("emails/enrollment.txt", {"user": user, "course": course}),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
```

### Celery Service 測試

```python
# ❌ 不測 task（依賴 Celery infrastructure）
# ✅ 直接測 service 函式
@pytest.mark.django_db
def test_send_enrollment_email_renders_correct_subject(user_factory, course_factory, mailoutbox):
    user = user_factory()
    course = course_factory(name="Python 基礎")
    send_enrollment_email(user_id=user.pk, course_id=course.pk)
    assert len(mailoutbox) == 1
    assert "Python 基礎" in mailoutbox[0].subject
```

---

## Phase 9：pre-commit 工具鏈

### .pre-commit-config.yaml

```yaml
repos:
    - repo: https://github.com/astral-sh/ruff-pre-commit
      rev: v0.4.4
      hooks:
          - id: ruff # linting（取代 flake8）
            args: [--fix]
          - id: ruff-format # 格式化（取代 black）

    - repo: https://github.com/pre-commit/mirrors-mypy
      rev: v1.10.0
      hooks:
          - id: mypy
            additional_dependencies: [django-stubs, types-requests]

    - repo: https://github.com/Riverside-Healthcare/djLint
      rev: v1.34.1
      hooks:
          - id: djlint-reformat-django # Django 模板格式化（取代手動縮排）
            args: [--profile=django]
          - id: djlint-django # Django 模板 lint（偵測語法問題）
            args: [--profile=django]

    - repo: https://github.com/pre-commit/pre-commit-hooks
      rev: v4.6.0
      hooks:
          - id: trailing-whitespace
          - id: end-of-file-fixer
          - id: check-merge-conflict
          - id: debug-statements # 禁止 pdb/ipdb 進入 commit
```

### 啟用

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files   # 第一次全量掃描
```

### pyproject.toml ruff 設定

```toml
[tool.ruff]
line-length = 100
target-version = "py312"
fix = true

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP"]
ignore = ["E501"]   # 行長由 formatter 控制
```

---

## Phase 10：進階測試模式

### factory-boy 進階用法

```python
# RelatedFactory：建立關聯物件
class UserWithProfileFactory(UserFactory):
    profile = factory.RelatedFactory(
        "tests.factories.ProfileFactory",
        factory_related_name="user",
    )

# Trait：快速切換物件狀態
class OrderFactory(DjangoModelFactory):
    class Params:
        paid = factory.Trait(
            status="paid",
            paid_at=factory.Faker("past_datetime"),
            payment_ref=factory.Sequence(lambda n: f"TXN{n:06d}"),
        )

# 使用
paid_order = OrderFactory(paid=True)
```

### pytest.mark.parametrize 進階範例

```python
@pytest.mark.django_db
@pytest.mark.parametrize("role,expected_status", [
    ("student", 403),
    ("staff", 200),
    ("director", 200),
    ("superuser", 200),
])
def test_report_view_permission(client_for, user_factory, role, expected_status):
    user = user_factory(role=role)
    c = client_for(user)
    resp = c.get("/reports/annual/")
    assert resp.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize("invalid_data,error_field", [
    ({"email": "not-an-email"}, "email"),
    ({"phone": "abc123"}, "phone"),
    ({"birth_date": "2099-01-01"}, "birth_date"),
])
def test_form_field_validation(client_for, staff_user, invalid_data, error_field):
    c = client_for(staff_user)
    resp = c.post("/applications/create/", data=invalid_data)
    assert error_field in resp.context["form"].errors
```

### mock 範例（純 unittest.mock）

```python
from unittest.mock import patch, MagicMock

@pytest.mark.django_db
def test_email_service_retries_on_smtp_error(user_factory):
    user = user_factory()
    with patch("django.core.mail.send_mail") as mock_send:
        mock_send.side_effect = [Exception("SMTP timeout"), None]
        # 第一次拋錯，第二次成功
        send_welcome_email(user_id=user.pk)
    assert mock_send.call_count == 2
```

---

## 每個 PR 的標準節奏

```
[0] Section 0: 更新覆蓋率快照（確認基準）
[1] openspec-apply-change：依 tasks.md 逐步實作
[2] 測試：pytest — 確認綠燈
[3] git commit（臺灣繁體中文 Conventional Commit）
[4] git push → open-pr（建立 PR 並產生臺灣繁體中文說明）
[5] review-pr-3x（等待 CI + review bot）
[6] 解決 review 留言 → push
[7] gh pr merge --squash
[8] git checkout main && git pull
[9] openspec-archive-change（子提案歸檔）
```

> 上述節奏適用於「單一子提案 PR」。

## 全部子提案完成後：收尾彙整 PR（必做）

即使每個子提案都跑過 `review-pr-3x`，仍可能有**延遲出現**的審查意見。  
因此在「所有子提案都已 squash merge」後，必須再開一個收尾 PR，集中補齊漏掉的改善項。

```
[A] 確認所有子提案 PR 都已 squash merge 到 main
[B] 逐一回看所有子提案 PR：Review、Conversation、line comments、CI annotations
[C] 建立「未落地審查意見清單」：意見來源 PR、連結、風險、預計修法
[D] 實作所有漏網改善（可含測試補強、型別修正、命名/邊界一致性調整）
[E] git push → open-pr（建立「收尾彙整改善 PR」）
[F] review-pr-3x（再監看一次，確保收尾 PR 自身也乾淨）
[G] gh pr merge --squash
[H] git checkout main && git pull
[I] openspec-archive-change（最後才歸檔父提案）
```

### 收尾彙整 PR 建議命名

- Branch：`refactor-wave-final-review-followups`
- PR Title：`refactor: 彙整修復子提案遺漏審查意見`

### Commit Message 規範

```
type(scope): 中文動詞 + 描述

feat(registration): 建立 TicketService 並抽取准考證邏輯
test(accounts): 補充 EmailService 單元測試（mock send_mail）
fix(registration): 修復 TakeApplicationView TOCTOU 競態條件
refactor(report): 將統計邏輯移入 StatisticsService
chore(config): 開啟 pytest --cov-fail-under=85 門檻
```

---

## Wave 4：強制覆蓋率門檻

Wave 3 全部 merge 後，才在 `pyproject.toml` 開啟：

```toml
[tool.pytest.ini_options]
addopts = """
  --cov=src
  --cov-fail-under=85
  --cov-report=html
  --cov-omit=*/migrations/*,manage.py,*/generate_testing_data/*
"""
```

> ⚠️ 在 Wave 3 完成前開啟 `fail-under` 會讓所有 PR 的 CI 失敗。

---

## 關鍵技術決策清單

| 決策         | 建議做法                                                        |
| ------------ | --------------------------------------------------------------- |
| Service 輸入 | `@dataclass(frozen=True)` 封裝參數                              |
| 錯誤型別     | `class XxxServiceError(ValueError)` + `field: str` 屬性         |
| 並發保護     | `@transaction.atomic` + `select_for_update()`                   |
| Model 邊界   | 純計算 property 留 Model；業務邏輯移 Service                    |
| Signal 使用  | 核心流程用明確呼叫；次要動作（log/metrics）可用 Signal          |
| Type hints   | Service 層全覆蓋，mypy `disallow_untyped_defs = true`           |
| Celery 拆法  | Thin task + Service 分離，直接測 service 函式                   |
| 測試標記     | Unit（無 DB）`@pytest.mark.unit`；整合 `@pytest.mark.django_db` |
| 覆蓋率排除   | migrations、manage.py、generate_testing_data                    |
| URL 合約     | **不動**（確保向後相容）                                        |

---

## 常見陷阱

- **過早開 `fail-under`**：Wave 3 完成前開啟會讓所有 CI 失敗
- **沒安全網就搬邏輯**：測試通過才代表行為不變，不是「感覺沒問題」
- **`select_for_update()` 在 `atomic` 外呼叫**：鎖無法正常運作
- **Signal 做核心業務流程**：測試時難以控制觸發時機，造成隱藏副作用
- **`@dataclass` 沒加 `frozen=True`**：Service 參數應不可變，避免意外修改
- **Celery task 裡包含業務邏輯**：直接從 task 呼叫 service，讓 service 可獨立測試

---

## 相關 Skills

- `django-snapshot` — 掃描覆蓋率與 Fat View
- `code-reviewer` — 程式碼審查工具，提供改進建議
- `review-fix` — 全方位程式碼審查 + 自動建立 OpenSpec 提案
- `openspec-ff-change` — 快速建立父提案 + 子提案
- `openspec-apply-change` — 逐步實作各個子提案的 tasks
- `open-pr` — 建立 GitHub Pull Request，並用臺灣繁體中文整理變更重點與測試結果
- `review-pr-3x` — 三輪等待 CI + 處理 review 留言
- `squash-pr` — squash merge 並更新本地 main
- `openspec-archive-change` — 完成後歸檔 change
