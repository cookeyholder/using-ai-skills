#!/usr/bin/env python3
"""
獨立的 CSS 類別搜尋工具

不依賴 Django，可以直接執行。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


def load_css_classes(snapshots_dir: Path) -> dict[str, Any]:
    """載入 CSS 類別掃描結果"""
    css_file = snapshots_dir / "snapshot_css_classes.json"

    if not css_file.exists():
        print(f"錯誤: 找不到 CSS 類別檔案: {css_file}", file=sys.stderr)
        print("請先執行快照生成以建立 CSS 類別檔案", file=sys.stderr)
        sys.exit(1)

    with css_file.open("r", encoding="utf-8") as f:
        return json.load(f)


def search_class(
    data: dict[str, Any],
    pattern: str,
    use_regex: bool = False,
    custom_only: bool = False,
) -> dict[str, list[str]]:
    """搜尋 CSS 類別"""
    results = {}

    # 決定要搜尋的類別類型
    if custom_only:
        search_categories = {"custom_classes": data.get("custom_classes", {})}
    else:
        search_categories = {
            "bootstrap_classes": data.get("bootstrap_classes", {}),
            "tailwind_classes": data.get("tailwind_classes", {}),
            "bootstrap_icons": data.get("bootstrap_icons", {}),
            "custom_classes": data.get("custom_classes", {}),
        }

    # 編譯正則表達式
    if use_regex:
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            print(f"錯誤: 無效的正則表達式: {e}", file=sys.stderr)
            sys.exit(1)

    # 搜尋每個模板
    for category_name, category_data in search_categories.items():
        for template, classes_or_dict in category_data.items():
            matched_classes = []

            # 處理不同的資料結構
            if isinstance(classes_or_dict, dict):
                # Bootstrap/Tailwind 類別（分類的）
                all_classes = []
                for class_list in classes_or_dict.values():
                    all_classes.extend(class_list)
            elif isinstance(classes_or_dict, list):
                # Icons 或 Custom 類別（列表）
                all_classes = classes_or_dict
            else:
                continue

            # 搜尋匹配的類別
            for css_class in all_classes:
                if use_regex:
                    if regex.search(css_class):
                        matched_classes.append(css_class)
                else:
                    if pattern.lower() in css_class.lower():
                        matched_classes.append(css_class)

            # 儲存結果
            if matched_classes:
                if template not in results:
                    results[template] = []
                results[template].extend(matched_classes)

    # 去重
    for template in results:
        results[template] = sorted(set(results[template]))

    return results


def display_results(results: dict[str, list[str]], pattern: str) -> None:
    """顯示搜尋結果"""
    if not results:
        print(f"\n找不到相符的類名: '{pattern}'")
        return

    print("\n" + "=" * 100)
    print(f"搜尋結果: '{pattern}'")
    print("=" * 100)

    total_templates = len(results)
    total_matches = sum(len(classes) for classes in results.values())

    print(f"\n找到 {total_matches} 個匹配的類別，出現在 {total_templates} 個模板中\n")

    # 按模板顯示
    for template, classes in sorted(results.items()):
        print(f"\n📄 {template}")
        print(f"   找到 {len(classes)} 個匹配:")
        for cls in classes:
            print(f"     • {cls}")


def main():
    """主程式進入點"""
    parser = argparse.ArgumentParser(
        description="獨立的 CSS 類別搜尋工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例：
  # 搜尋包含 "btn" 的類別
  python standalone_find_class.py btn

  # 使用正則表達式搜尋
  python standalone_find_class.py "col-.*" --regex

  # 僅搜尋自訂類別
  python standalone_find_class.py navbar --custom-only

  # 指定快照目錄
  python standalone_find_class.py btn -s /path/to/snapshots

  # JSON 格式輸出
  python standalone_find_class.py btn --json
        """,
    )

    parser.add_argument("pattern", type=str, help="要搜尋的 CSS 類別名稱或模式")

    parser.add_argument(
        "-s",
        "--snapshots",
        type=str,
        default="snapshots",
        help="快照目錄路徑（預設: snapshots）",
    )

    parser.add_argument("--regex", action="store_true", help="使用正則表達式搜尋")

    parser.add_argument("--custom-only", action="store_true", help="僅搜尋自訂類別")

    parser.add_argument("--json", action="store_true", help="以 JSON 格式輸出結果")

    args = parser.parse_args()

    try:
        snapshots_dir = Path(args.snapshots).resolve()
        if not snapshots_dir.exists():
            print(f"錯誤: 快照目錄不存在: {snapshots_dir}", file=sys.stderr)
            sys.exit(1)

        # 載入 CSS 類別資料
        data = load_css_classes(snapshots_dir)

        # 搜尋
        results = search_class(
            data, args.pattern, use_regex=args.regex, custom_only=args.custom_only
        )

        # 輸出結果
        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            display_results(results, args.pattern)

        # 返回狀態碼
        sys.exit(0 if results else 1)

    except KeyboardInterrupt:
        print("\n\n中斷執行")
        sys.exit(130)
    except Exception as e:
        print(f"\n錯誤: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
