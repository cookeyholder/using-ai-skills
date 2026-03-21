---
name: django-snapshot
description: 自動掃描 Django 專案結構、追蹤 CSS 框架使用，並提供智能建議。支援 Bootstrap 5 和 Tailwind CSS 雙框架掃描，用於開發新功能前了解專案架構，或追蹤 CSS 遷移進度。
---

這個 skill 能掃描和分析 Django 專案，生成結構化的 JSON 快照，幫助 AI 快速理解專案架構並提供精準的開發建議。

**新增 Tailwind CSS 支援** - 現在可以同時掃描 Bootstrap 5 和 Tailwind CSS 類別，支援響應式前綴（sm:, md:, lg:, xl:, 2xl:）和狀態變體（hover:, focus:, active: 等）。

## 使用時機

當遇到以下情況時，自動或手動執行此 skill：

1. **開發新功能前** - 需要了解最新的專案結構
2. **進行代碼審查** - 確認代碼符合架構標準
3. **重構專案** - 需要全面了解現有結構
4. **不確定專案架構** - AI 需要準確的專案資訊來回答問題
5. **定期檢查** - 定期生成 snapshot 追蹤專案演進

## 🤖 如何讓 AI 使用快照

生成快照後，你可以使用以下 Prompt 引導 AI 分析專案：

- **了解架構**：
  > "請讀取 `snapshots/snapshot.json`，為我解析這個 Django 專案的核心架構、主要 App 及其職責。"

- **追蹤遷移進度**：
  > "請查看 `snapshots/snapshot_migration_status.json`，告訴我目前 Bootstrap 到 Tailwind 的遷移進度，並列出依賴性最高、最需要優先處理的模板。"

- **尋找代碼範例**：
  > "讀取 `snapshots/snapshot_css_classes.json`，幫我找出所有使用 `btn-primary` 的地方，我想參考它們的寫法。"

## 🤖 AI Agent 運作指引 (AI Agent Instructions)

當 AI Agent 執行此 Skill 時，應遵循以下標準作業程序：

1.  **執行生成**：在開始新任務或需要了解架構時，優先執行 `./.claude/skills/django-snapshot/scripts/run_snapshot.sh generate`。
2.  **主動讀取**：快照生成成功後，AI Agent **必須主動讀取** 專案根目錄下 `snapshots/` 資料夾中的 JSON 檔案（優先讀取 `snapshot.json`）以建立對專案結構的全面理解。
3.  **整合資訊**：將讀取到的快照資訊與當前任務結合，提供基於真實專案架構的建議或程式碼修改。

## 快速開始

### 方式一：使用包裝腳本（推薦）⭐

```bash
# 生成完整快照（獨立執行，不需要 Django 環境）
./.claude/skills/django-snapshot/scripts/run_snapshot.sh generate

# 查看遷移狀態
./.claude/skills/django-snapshot/scripts/run_snapshot.sh status

# 搜尋 CSS 類別
./.claude/skills/django-snapshot/scripts/run_snapshot.sh find "bg-blue"

# 掃描 CSS 類別（詳細輸出）
./.claude/skills/django-snapshot/scripts/run_snapshot.sh scan-css

# 顯示幫助
./.claude/skills/django-snapshot/scripts/run_snapshot.sh help
```

### 方式二：直接執行獨立 Python 腳本

```bash
# 生成快照（指定專案路徑）
python3 ./.claude/skills/django-snapshot/scripts/standalone_snapshot.py -p /path/to/project

# 查看遷移狀態（詳細列表）
python3 ./.claude/skills/django-snapshot/scripts/standalone_migration_status.py --list

# 搜尋 CSS 類別（正則表達式）
python3 ./.claude/skills/django-snapshot/scripts/standalone_find_class.py "col-.*" --regex

# 掃描 CSS 類別
python3 ./.claude/skills/django-snapshot/scripts/css_scanner.py \
  -s snapshots/snapshot_templates.json \
  -o snapshots/snapshot_css_classes.json
```

### 方式三：在其他專案中使用

```bash
# 複製 scripts 目錄到其他專案
cp -r .claude/skills/django-snapshot/scripts /path/to/other/project/

# 在新專案中執行
cd /path/to/other/project
./scripts/run_snapshot.sh generate
```

## 執行流程

### Phase 1: 生成專案快照

```bash
./.claude/skills/django-snapshot/scripts/run_snapshot.sh generate --verbose
```

**預期輸出檔案**:
- `snapshots/snapshot.json` - 主快照檔案
- `snapshots/snapshot_css_classes.json` - CSS 類別掃描結果
- `snapshots/snapshot_migration_status.json` - 遷移狀態追蹤

**掃描內容**: Models、Views、URLs、Templates、Forms、Apps、Middleware、CSS Classes

### Phase 2: 分析遷移狀態

```bash
./.claude/skills/django-snapshot/scripts/run_snapshot.sh status
```

顯示：
- 總模板數量
- 已完成/待處理數量
- 平均複雜度
- CSS 衝突統計

### Phase 3: 生成遷移計畫

```bash
./.claude/skills/django-snapshot/scripts/run_snapshot.sh plan
```

產生基於複雜度和依賴關係的遷移順序建議。

### Phase 4: 讀取並分析快照

使用 Read 工具讀取生成的 JSON 檔案供 AI 分析使用：
- `snapshots/snapshot.json`
- `snapshots/snapshot_css_classes.json`
- `snapshots/snapshot_migration_status.json`

## 進階用法

### 搜尋 CSS 類別

```bash
# 搜尋精確類別名稱
./.claude/skills/django-snapshot/scripts/run_snapshot.sh find "btn"

# 使用正則表達式搜尋
docker compose exec web python src/manage.py snapshot_find_class --regex "col-.*"

# 僅搜尋自訂類別
docker compose exec web python src/manage.py snapshot_find_class --custom-only "navbar"
```

### 分析特定模板

```bash
# 分析模板的依賴關係和複雜度
./.claude/skills/django-snapshot/scripts/run_snapshot.sh analyze base.html

# 或直接使用 Django 命令
docker compose exec web python src/manage.py snapshot_migration_dependencies --analyze-template base.html
```

### 強制重新生成

```bash
# 清除快取並重新生成所有快照
./.claude/skills/django-snapshot/scripts/run_snapshot.sh generate --force
```

## 腳本架構 ⭐ 極簡設計

此 skill 採用**極簡的扁平架構**，所有腳本都在 `scripts/` 目錄下，無需複雜的目錄層級。

### 📂 完整腳本清單

```
.claude/skills/django-snapshot/scripts/
├── standalone_snapshot.py          (13KB) - 獨立快照生成器
├── standalone_migration_status.py  (7.4KB) - 遷移狀態查看器
├── standalone_find_class.py        (5.8KB) - CSS 類別搜尋工具
├── generate_migration_status.py    (2KB)  - 遷移狀態生成器
├── css_scanner.py                  (34KB) - CSS 類別掃描器
├── migration_tracker.py            (14KB) - 遷移狀態追蹤器
└── run_snapshot.sh                 (4KB) - 統一執行介面
```

### 🎯 腳本功能說明

#### `standalone_snapshot.py` - 快照生成器
- ✅ 不依賴 Django，直接掃描檔案系統
- ✅ 自動搜尋 Templates、Models、Views、Apps
- ✅ 支援自訂專案路徑和輸出目錄
- 📝 輸出：`snapshot_templates.json`, `snapshot_models.json`, `snapshot.json` 等

#### `standalone_migration_status.py` - 狀態查看器
- ✅ 顯示遷移進度統計和複雜度分布
- ✅ 支援狀態過濾（未開始/進行中/已完成）
- ✅ 支援 JSON 和表格輸出
- 📝 讀取：`snapshot_migration_status.json`

#### `generate_migration_status.py` - 狀態生成器
- ✅ 整合 CSS 掃描結果與模板依賴關係
- ✅ 計算遷移複雜度與衝突
- ✅ 生成標準化的遷移狀態報告
- 📝 輸出：`snapshot_migration_status.json`

#### `standalone_find_class.py` - CSS 搜尋
- ✅ 搜尋 CSS 類別使用位置
- ✅ 支援正則表達式搜尋
- ✅ 支援僅搜尋自訂類別
- 📝 讀取：`snapshot_css_classes.json`

#### `css_scanner.py` - CSS 掃描器
- ✅ 支援 Bootstrap 5 和 Tailwind CSS 3.4+
- ✅ 自動識別響應式前綴（sm:, md:, lg:, xl:, 2xl:）
- ✅ 自動識別狀態變體（hover:, focus:, active: 等）
- 📝 輸出：`snapshot_css_classes.json`

#### `migration_tracker.py` - 遷移追蹤器
- 複雜度計算
- 依賴關係分析
- CSS 衝突檢測

#### `run_snapshot.sh` - 包裝腳本
- 統一的命令介面
- 自動調用獨立腳本
- 彩色輸出和錯誤處理

### ✨ 設計優勢

✅ **極簡結構** - 所有腳本在同一目錄，易於管理
✅ **完全獨立** - 不需要 Django 環境即可運行
✅ **靈活部署** - 可複製到任何專案使用
✅ **快速執行** - 直接執行，無需 Django 初始化
✅ **易於維護** - 無複雜的目錄層級

## 輸出檔案說明

### snapshot.json
完整的 Django 專案結構快照，包含：
- Models（資料模型）
- Views（視圖函式/類別）
- URLs（路由配置）
- Templates（模板檔案）
- Forms（表單定義）
- Apps（應用配置）
- Middleware（中間件）

### snapshot_css_classes.json
CSS 類別掃描結果，分類為：
- **Bootstrap 類別**（基於 Bootstrap 5 官方定義）
  - Layout、Spacing、Typography、Components、Utilities、Grid
- **Tailwind CSS 類別**（支援完整的 Tailwind CSS 3.4+ 類別模式）
  - Layout、Flexbox & Grid、Spacing、Sizing、Typography
  - Backgrounds、Borders、Effects、Transitions、Transforms
  - Interactivity、Positioning、Visibility、Overflow
  - 支援響應式前綴：sm:, md:, lg:, xl:, 2xl:
  - 支援狀態變體：hover:, focus:, active:, disabled:, dark: 等
- **Bootstrap Icons**（bi-* 圖示類別）
- **自訂類別**（非 Bootstrap 和 Tailwind 的自訂 CSS）

### snapshot_migration_status.json
遷移狀態追蹤檔案，包含：
- 各模板的遷移狀態（未開始/進行中/已完成）
- 複雜度評分（1-10 分）
- 依賴關係圖
- CSS 衝突檢測結果

## 最佳實踐

1. **定期更新快照** - 每次開發新功能前執行
2. **快照檔案管理** - 已加入 `.gitignore`，不提交到版控
3. **效能考量** - 完整掃描約 1-3 秒（115 個模板）
4. **使用包裝腳本** - 使用 `run_snapshot.sh` 提供更好的使用體驗
5. **遷移前分析** - 修改模板前先分析依賴關係

## 常見使用情境

### 情境 1: 開始新功能開發
```bash
# 1. 生成最新快照
./.claude/skills/django-snapshot/scripts/run_snapshot.sh generate --verbose

# 2. 讀取快照檔案
# AI 使用 Read 工具讀取 snapshots/*.json

# 3. 基於快照提供開發建議
```

### 情境 2: Bootstrap → Tailwind 遷移
```bash
# 1. 生成遷移計畫
./.claude/skills/django-snapshot/scripts/run_snapshot.sh plan

# 2. 分析要遷移的模板
./.claude/skills/django-snapshot/scripts/run_snapshot.sh analyze target_template.html

# 3. 檢查 CSS 類別使用情況
./.claude/skills/django-snapshot/scripts/run_snapshot.sh find "btn-primary"

# 4. 執行遷移並更新狀態
# （手動修改模板後更新 snapshot_migration_status.json）

# 5. 檢查進度
./.claude/skills/django-snapshot/scripts/run_snapshot.sh status
```

### 情境 3: 追蹤專案演進
```bash
# 定期執行（例如每週）
./.claude/skills/django-snapshot/scripts/run_snapshot.sh generate

# 比較快照變化（可結合 git diff）
git diff snapshots/
```

## 故障排除

### 問題：命令執行失敗
```bash
# 確認 Docker 容器運行中
docker compose ps

# 確認腳本有執行權限
chmod +x ./.claude/skills/django-snapshot/scripts/run_snapshot.sh
```

### 問題：找不到模板
```bash
# 確認模板路徑正確
./.claude/skills/django-snapshot/scripts/run_snapshot.sh find "template_name"
```

### 問題：快照檔案過舊
```bash
# 強制重新生成
./.claude/skills/django-snapshot/scripts/run_snapshot.sh generate --force
```

## 相關文檔

- `CLAUDE.md` - 專案總覽
- `docs/snapshot-tailwind-migration.md` - CSS 遷移指南
- `docs/snapshot-api-reference.md` - API 文檔

## 目錄結構

```
.claude/skills/django-snapshot/
├── SKILL.md                        # 本文檔
└── scripts/                        # 所有腳本（扁平結構）
    ├── standalone_snapshot.py      # 快照生成器
    ├── standalone_migration_status.py  # 狀態查看器
    ├── standalone_find_class.py    # CSS 搜尋
    ├── css_scanner.py              # CSS 掃描器
    ├── migration_tracker.py        # 遷移追蹤器
    └── run_snapshot.sh             # 包裝腳本
```

**特點**：
- 🎯 扁平結構，無嵌套目錄
- 📦 所有腳本在同一位置
- 🚀 易於複製和部署
- 🔧 簡化維護成本

## 技術細節

### CSS 類別檢測規則

#### Bootstrap 5
- 150+ 類別模式，涵蓋所有 Bootstrap 5 官方類別
- 類別分組：Layout、Spacing、Typography、Components、Utilities、Grid

#### Tailwind CSS 3.4+
- 支援所有主流 Tailwind CSS 工具類別
- **響應式設計**：自動識別 sm:, md:, lg:, xl:, 2xl: 前綴
- **狀態變體**：自動識別 hover:, focus:, active:, disabled: 等前綴
- **前綴剝離**：智能移除多層前綴（如 md:hover:bg-blue-500）進行分類
- 類別分組：
  - Layout（container, flex, grid, hidden 等）
  - Flexbox & Grid（justify, items, gap, grid-cols 等）
  - Spacing（m-*, p-*, space-* 等）
  - Sizing（w-*, h-*, min-*, max-* 等）
  - Typography（text-*, font-*, leading-* 等）
  - Backgrounds（bg-*, gradient 等）
  - Borders（border-*, rounded-*, divide-* 等）
  - Effects（shadow-*, opacity-* 等）
  - Transitions（transition-*, duration-*, animate-* 等）
  - Transforms（rotate-*, scale-*, translate-* 等）
  - Interactivity（cursor-*, pointer-events-*, resize 等）
  - Positioning（static, relative, absolute, sticky, inset-* 等）
  - Visibility（visible, invisible, collapse）
  - Overflow（overflow-*, overscroll-* 等）

#### Bootstrap Icons
- 所有 `bi-*` 開頭的圖示類別

#### 自訂類別
- 不符合 Bootstrap 和 Tailwind 規則的其他類別

### 複雜度評分因素
1. HTML 行數
2. CSS 類別數量
3. Django 模板標籤數量
4. 依賴關係數量
5. Bootstrap 類別數量
6. JavaScript 互動程度

### 依賴關係分析
- 偵測 `{% extends %}` 和 `{% include %}` 標籤
- 建立模板依賴圖
- 計算影響範圍（子模板數量）

## 版本資訊

- **版本**: 2.0.0 🎉
- **最後更新**: 2024-12-26
- **重大更新**:
  - 🚀 **完全獨立架構** - 不再依賴 Django 管理命令
  - 🔧 **獨立 Python 腳本** - 可直接執行，無需 Django 環境
  - ⚡ **更快速度** - 跳過 Django 初始化，直接掃描檔案
  - 📦 **靈活部署** - 可在任何 Django 專案中使用
- **新增功能**:
  - ✅ 完整 Tailwind CSS 3.4+ 支援
  - ✅ 響應式前綴自動識別
  - ✅ 狀態變體自動識別
  - ✅ 雙框架掃描（Bootstrap + Tailwind）
- **相容性**: Python 3.9+（不再依賴 Django）
- **依賴**: 僅需標準 Python 函式庫

## 授權

此 skill 遵循專案主授權條款。
