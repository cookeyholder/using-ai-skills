#!/bin/bash

# Django Snapshot Skill 執行腳本（獨立版本）
# 此腳本使用獨立的 Python 腳本，不依賴 Django 管理命令

set -e  # 遇到錯誤立即退出

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"

# 顏色定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 函數：顯示使用說明
show_usage() {
    echo -e "${BLUE}Django Snapshot Skill - 增強版 v2.1${NC}"
    echo ""
    echo "用法: $0 [命令] [選項]"
    echo ""
    echo "命令:"
    echo "  generate              生成專案快照（預設）"
    echo "  status                顯示遷移狀態"
    echo "  find <class>          搜尋 CSS 類別"
    echo "  scan-css              掃描 CSS 類別"
    echo "  search <pattern>      全文搜尋原始碼與模板"
    echo "  url-refs              分析 URL name 引用情況"
    echo "  template-deps         分析模板繼承與依賴關係"
    echo "  help                  顯示此說明"
    echo ""
    echo "選項 (generate):"
    echo "  -p, --project         專案目錄路徑（預設: 當前目錄）"
    echo "  -o, --output          輸出目錄路徑（預設: snapshots）"
    echo ""
    echo "選項 (search):"
    echo "  --regex               使用正則表達式"
    echo "  --include <glob>      檔案篩選（例：*.py、*.html）"
    echo "  --app <name>          只搜尋特定 app"
    echo "  --context <N>         顯示前後 N 行"
    echo "  --case-sensitive      區分大小寫"
    echo ""
    echo "選項 (url-refs):"
    echo "  --list                列出所有 URL names"
    echo "  --url <name>          分析特定 URL name"
    echo "  --unused              列出未被引用的 URL"
    echo ""
    echo "選項 (template-deps):"
    echo "  --template <name>     分析特定模板"
    echo "  --tree                顯示繼承樹"
    echo "  --orphans             列出未被引用的模板"
    echo "  --summary             顯示統計摘要"
    echo ""
    echo "範例:"
    echo "  $0 generate"
    echo "  $0 search 'LoginRequired' --regex --app accounts"
    echo "  $0 url-refs --unused"
    echo "  $0 template-deps --tree"
    echo "  $0 find btn"
}

# 函數：執行獨立 Python 腳本
run_standalone_script() {
    local script_name=$1
    shift
    local script_path="$SCRIPT_DIR/$script_name"

    if [ ! -f "$script_path" ]; then
        echo -e "${RED}錯誤: 找不到腳本 $script_name${NC}"
        exit 1
    fi

    echo -e "${BLUE}▶ 執行: python $script_name $@${NC}"
    python3 "$script_path" "$@"
}

# 主要邏輯
COMMAND=${1:-generate}
shift || true  # 移除第一個參數，如果沒有參數則忽略錯誤

case $COMMAND in
    generate)
        echo -e "${GREEN}🔍 生成 Django 專案快照...${NC}"
        run_standalone_script "standalone_snapshot.py" -p "$PROJECT_ROOT" -o snapshots "$@"

        # 生成完成後，執行 CSS 掃描
        echo ""
        echo -e "${GREEN}🎨 掃描 CSS 類別...${NC}"
        SNAPSHOTS_DIR="${PROJECT_ROOT}/snapshots"
        if [ -f "$SNAPSHOTS_DIR/snapshot_templates.json" ]; then
            run_standalone_script "css_scanner.py" \
                -s "$SNAPSHOTS_DIR/snapshot_templates.json" \
                -o "$SNAPSHOTS_DIR/snapshot_css_classes.json"
                
            # CSS 掃描完成後，生成遷移狀態
            echo ""
            echo -e "${GREEN}📊 生成遷移狀態...${NC}"
            run_standalone_script "generate_migration_status.py" -s "$SNAPSHOTS_DIR"
        else
            echo -e "${YELLOW}⚠ 找不到模板快照，跳過 CSS 掃描與遷移狀態生成${NC}"
        fi

        echo ""
        echo -e "${GREEN}✅ 快照生成完成！${NC}"
        echo -e "${YELLOW}📂 快照檔案位置: $SNAPSHOTS_DIR${NC}"
        echo -e "   - snapshot.json (完整快照)"
        echo -e "   - snapshot_migration_status.json (遷移狀態)"
        ;;

    status)
        echo -e "${GREEN}📊 檢查遷移狀態...${NC}"
        SNAPSHOTS_DIR="${PROJECT_ROOT}/snapshots"
        run_standalone_script "standalone_migration_status.py" -s "$SNAPSHOTS_DIR" "$@"
        ;;

    find)
        if [ -z "$1" ]; then
            echo -e "${RED}❌ 錯誤: 請指定要搜尋的 CSS 類別${NC}"
            echo "用法: $0 find <class_name> [--regex] [--custom-only]"
            exit 1
        fi
        echo -e "${GREEN}🔎 搜尋 CSS 類別: $1${NC}"
        PATTERN=$1
        shift
        SNAPSHOTS_DIR="${PROJECT_ROOT}/snapshots"
        run_standalone_script "standalone_find_class.py" "$PATTERN" -s "$SNAPSHOTS_DIR" "$@"
        ;;

    scan-css)
        echo -e "${GREEN}🎨 掃描 CSS 類別...${NC}"
        SNAPSHOTS_DIR="${PROJECT_ROOT}/snapshots"

        if [ ! -f "$SNAPSHOTS_DIR/snapshot_templates.json" ]; then
            echo -e "${RED}❌ 錯誤: 找不到模板快照檔案${NC}"
            echo "請先執行: $0 generate"
            exit 1
        fi

        run_standalone_script "css_scanner.py" \
            -s "$SNAPSHOTS_DIR/snapshot_templates.json" \
            -o "$SNAPSHOTS_DIR/snapshot_css_classes.json" \
            -v
        ;;

    help|--help|-h)
        show_usage
        ;;

    search)
        if [ -z "$1" ]; then
            echo -e "${RED}❌ 錯誤: 請指定搜尋字串${NC}"
            echo "用法: $0 search <pattern> [--regex] [--include *.py] [--app <name>] [--context N]"
            exit 1
        fi
        echo -e "${GREEN}🔎 全文搜尋: $1${NC}"
        run_standalone_script "standalone_search.py" -p "$PROJECT_ROOT" "$@"
        ;;

    url-refs)
        echo -e "${GREEN}🔗 分析 URL 引用...${NC}"
        SNAPSHOTS_DIR="${PROJECT_ROOT}/snapshots"
        run_standalone_script "standalone_url_refs.py" -p "$PROJECT_ROOT" -s "$SNAPSHOTS_DIR" "$@"
        ;;

    template-deps)
        echo -e "${GREEN}🌲 分析模板依賴...${NC}"
        run_standalone_script "standalone_template_deps.py" -p "$PROJECT_ROOT" "$@"
        ;;

    help|--help|-h)
        show_usage
        ;;

    *)
        echo -e "${RED}❌ 未知命令: $COMMAND${NC}"
        echo ""
        show_usage
        exit 1
        ;;
esac
