#!/usr/bin/env python3
"""
獨立的 CSS 遷移狀態查看器

不依賴 Django，可以直接執行。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional


def load_migration_status(snapshots_dir: Path) -> dict[str, Any]:
    """載入遷移狀態檔案"""
    status_file = snapshots_dir / 'snapshot_migration_status.json'

    if not status_file.exists():
        print(f"錯誤: 找不到遷移狀態檔案: {status_file}", file=sys.stderr)
        print("請先執行快照生成以建立遷移狀態檔案", file=sys.stderr)
        sys.exit(1)

    with status_file.open('r', encoding='utf-8') as f:
        return json.load(f)


def display_summary(data: dict[str, Any]) -> None:
    """顯示遷移進度摘要"""
    templates = data.get('templates', {})

    total = len(templates)
    not_started = sum(1 for t in templates.values() if t.get('status') == 'not_started')
    in_progress = sum(1 for t in templates.values() if t.get('status') == 'in_progress')
    completed = sum(1 for t in templates.values() if t.get('status') == 'completed')

    # 計算平均複雜度
    complexities = [t.get('complexity', 0) for t in templates.values()]
    avg_complexity = sum(complexities) / len(complexities) if complexities else 0

    # 計算有衝突的模板數
    conflicts = sum(1 for t in templates.values() if t.get('conflicts', 0) > 0)

    # 複雜度分布
    very_simple = sum(1 for c in complexities if 1 <= c <= 2)
    simple = sum(1 for c in complexities if 3 <= c <= 4)
    moderate = sum(1 for c in complexities if 5 <= c <= 6)
    complex_count = sum(1 for c in complexities if 7 <= c <= 8)
    very_complex = sum(1 for c in complexities if 9 <= c <= 10)

    # 完成率
    completion_rate = (completed / total * 100) if total > 0 else 0

    print("=" * 100)
    print("📊 遷移進度統計")
    print("=" * 100)
    print(f"總模板數:           {total}")
    print(f"未開始:             {not_started}")
    print(f"進行中:             {in_progress}")
    print(f"已完成:             {completed}")
    print(f"完成百分比:         {completion_rate:.1f}% ({completed}/{total})")
    print(f"平均複雜度:         {avg_complexity:.2f}/10")
    print(f"有衝突的模板:       {conflicts}")
    print()
    print("複雜度分布:")
    if very_simple > 0:
        completion = sum(
            1 for t in templates.values()
            if 1 <= t.get('complexity', 0) <= 2 and t.get('status') == 'completed'
        )
        rate = (completion / very_simple * 100)
        print(f"  非常簡單        {very_simple:3d} 個 ({completion:3d} 完成, {rate:5.1f}%)")

    if simple > 0:
        completion = sum(
            1 for t in templates.values()
            if 3 <= t.get('complexity', 0) <= 4 and t.get('status') == 'completed'
        )
        rate = (completion / simple * 100)
        print(f"  簡單          {simple:3d} 個 ({completion:3d} 完成, {rate:5.1f}%)")

    if moderate > 0:
        completion = sum(
            1 for t in templates.values()
            if 5 <= t.get('complexity', 0) <= 6 and t.get('status') == 'completed'
        )
        rate = (completion / moderate * 100)
        print(f"  中等          {moderate:3d} 個 ({completion:3d} 完成, {rate:5.1f}%)")

    if complex_count > 0:
        completion = sum(
            1 for t in templates.values()
            if 7 <= t.get('complexity', 0) <= 8 and t.get('status') == 'completed'
        )
        rate = (completion / complex_count * 100)
        print(f"  複雜          {complex_count:3d} 個 ({completion:3d} 完成, {rate:5.1f}%)")

    if very_complex > 0:
        completion = sum(
            1 for t in templates.values()
            if 9 <= t.get('complexity', 0) <= 10 and t.get('status') == 'completed'
        )
        rate = (completion / very_complex * 100)
        print(f"  非常複雜        {very_complex:3d} 個 ({completion:3d} 完成, {rate:5.1f}%)")


def display_template_list(data: dict[str, Any], status_filter: Optional[str] = None) -> None:
    """顯示模板列表"""
    templates = data.get('templates', {})

    # 過濾模板
    if status_filter:
        filtered = {
            k: v for k, v in templates.items()
            if v.get('status') == status_filter
        }
    else:
        filtered = templates

    if not filtered:
        print("\n沒有符合條件的模板")
        return

    print("\n" + "=" * 100)
    print("遷移狀態列表")
    print("=" * 100)
    print(f"{'模板名稱':<45s} {'狀態':<12s} {'複雜度':<8s} {'依賴':<8s} {'衝突':<6s}")
    print("-" * 100)

    # 排序：依複雜度
    sorted_templates = sorted(
        filtered.items(),
        key=lambda x: x[1].get('complexity', 0)
    )

    for name, info in sorted_templates:
        status = info.get('status', 'unknown')
        complexity = info.get('complexity', 0)
        dependencies = len(info.get('dependencies', []))
        conflicts = info.get('conflicts', 0)

        # 狀態顯示
        status_map = {
            'not_started': '未開始',
            'in_progress': '進行中',
            'completed': '已完成',
        }
        status_display = status_map.get(status, status)

        print(f"{name:<45s} {status_display:<12s} {complexity:<8d} {dependencies:<8d} {conflicts:<6d}")


def main():
    """主程式進入點"""
    parser = argparse.ArgumentParser(
        description='獨立的 CSS 遷移狀態查看器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例：
  # 顯示遷移狀態摘要
  python standalone_migration_status.py

  # 指定快照目錄
  python standalone_migration_status.py -s /path/to/snapshots

  # 僅顯示特定狀態的模板
  python standalone_migration_status.py --filter not_started
  python standalone_migration_status.py --filter completed

  # 詳細列表
  python standalone_migration_status.py --list
        """
    )

    parser.add_argument(
        '-s', '--snapshots',
        type=str,
        default='snapshots',
        help='快照目錄路徑（預設: snapshots）'
    )

    parser.add_argument(
        '--filter',
        type=str,
        choices=['not_started', 'in_progress', 'completed'],
        help='過濾特定狀態的模板'
    )

    parser.add_argument(
        '--list',
        action='store_true',
        help='顯示詳細的模板列表'
    )

    parser.add_argument(
        '--json',
        action='store_true',
        help='以 JSON 格式輸出'
    )

    args = parser.parse_args()

    try:
        snapshots_dir = Path(args.snapshots).resolve()
        if not snapshots_dir.exists():
            print(f"錯誤: 快照目錄不存在: {snapshots_dir}", file=sys.stderr)
            sys.exit(1)

        # 載入資料
        data = load_migration_status(snapshots_dir)

        # JSON 輸出
        if args.json:
            print(json.dumps(data, indent=2, ensure_ascii=False))
            sys.exit(0)

        # 顯示摘要
        display_summary(data)

        # 顯示列表
        if args.list or args.filter:
            display_template_list(data, args.filter)

        sys.exit(0)

    except KeyboardInterrupt:
        print("\n\n中斷執行")
        sys.exit(130)
    except Exception as e:
        print(f"\n錯誤: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
