#!/usr/bin/env python3
"""
standalone_search.py — 獨立的 Django 專案全文搜尋工具

功能等同 django-vibe-snapshot 的 snapshot_search management command，
但完全不依賴 Django 環境。

用法：
  python standalone_search.py <pattern> [選項]
  python standalone_search.py "def create" --include "*.py" --context 3
  python standalone_search.py "LoginRequired" --regex --app accounts
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterator


# ===== 目錄偵測 =====

def _find_project_root(start: Path) -> Path:
    """從起始路徑向上搜尋 manage.py"""
    for candidate in [start, *start.parents]:
        if (candidate / "manage.py").exists():
            return candidate
        if (candidate / "src" / "manage.py").exists():
            return candidate
    return start


def _get_src_dir(project_root: Path) -> Path:
    src = project_root / "src"
    return src if src.exists() else project_root


def _get_search_dirs(project_root: Path, app_filter: str | None) -> list[Path]:
    """取得要搜尋的目錄清單（模仿 snapshot_search._get_search_dirs）"""
    src_dir = _get_src_dir(project_root)
    dirs: list[Path] = []

    for candidate in src_dir.iterdir():
        if not candidate.is_dir():
            continue
        if any(p in candidate.parts for p in (".venv", "__pycache__", "node_modules", ".git")):
            continue
        if (candidate / "__init__.py").exists() and (candidate / "apps.py").exists():
            if app_filter is None or candidate.name == app_filter:
                dirs.append(candidate)

    # 加入模板目錄
    for tmpl_dir in [src_dir / "templates", project_root / "templates"]:
        if tmpl_dir.exists() and (app_filter is None):
            dirs.append(tmpl_dir)

    # 若 app_filter 為 None 且 dirs 為空，改為掃描 src_dir
    if not dirs:
        dirs = [src_dir]

    return sorted(set(dirs))


# ===== 搜尋邏輯 =====

def _iter_files(directories: list[Path], include_pattern: str) -> Iterator[Path]:
    """遞迴列舉符合 include_pattern 的檔案"""
    for d in directories:
        for f in d.rglob(include_pattern):
            if not f.is_file():
                continue
            parts = f.parts
            if any(p in parts for p in (".venv", "__pycache__", "node_modules", ".git", "migrations")):
                continue
            yield f


def _search_file(
    file_path: Path,
    pattern: re.Pattern,
    context_lines: int,
    project_root: Path,
) -> list[dict]:
    """在單一檔案中搜尋，回傳匹配結果列表"""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return []

    lines = content.splitlines()
    results: list[dict] = []

    for i, line in enumerate(lines):
        if pattern.search(line):
            start = max(0, i - context_lines)
            end = min(len(lines), i + context_lines + 1)
            context = []
            for j in range(start, end):
                context.append({
                    "lineno": j + 1,
                    "content": lines[j],
                    "is_match": j == i,
                })
            try:
                rel_path = str(file_path.relative_to(project_root))
            except ValueError:
                rel_path = str(file_path)
            results.append({
                "file": rel_path,
                "lineno": i + 1,
                "line": line,
                "context": context,
            })

    return results


def _build_pattern(query: str, use_regex: bool, case_sensitive: bool) -> re.Pattern:
    raw = query if use_regex else re.escape(query)
    flags = 0 if case_sensitive else re.IGNORECASE
    return re.compile(raw, flags)


# ===== 輸出格式 =====

def _print_results(
    all_results: list[dict],
    query: str,
    context_lines: int,
    total_files: int,
) -> None:
    if not all_results:
        print(f"未找到符合 '{query}' 的結果")
        return

    # 按檔案分組
    from itertools import groupby
    sorted_results = sorted(all_results, key=lambda r: (r["file"], r["lineno"]))

    print(f"\n搜尋結果: '{query}'")
    print("=" * 70)

    match_count = 0
    for file_path, matches in groupby(sorted_results, key=lambda r: r["file"]):
        match_list = list(matches)
        match_count += len(match_list)
        print(f"\n📄 {file_path}  ({len(match_list)} 個匹配)")
        print("-" * 50)
        for m in match_list:
            if context_lines > 0:
                for ctx in m["context"]:
                    marker = "→ " if ctx["is_match"] else "  "
                    print(f"  {marker}{ctx['lineno']:4d}: {ctx['content']}")
                print()
            else:
                print(f"  {m['lineno']:4d}: {m['line']}")

    print("=" * 70)
    print(f"共找到 {match_count} 個匹配，遍歷 {total_files} 個檔案")


# ===== 主程式 =====

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Django 專案全文搜尋工具（無需 Django 環境）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例：
  python standalone_search.py "class.*View"
  python standalone_search.py "LoginRequired" --regex --app accounts
  python standalone_search.py "TODO" --include "*.py" --context 2
  python standalone_search.py "{% url" --include "*.html" --case-sensitive
        """,
    )
    parser.add_argument("pattern", help="搜尋字串或正則表達式")
    parser.add_argument("-p", "--project", default=".", help="專案根目錄")
    parser.add_argument("--regex", action="store_true", help="將 pattern 視為正則表達式")
    parser.add_argument("--include", default="*", help="檔案 glob 篩選（例：*.py、*.html）")
    parser.add_argument("--app", help="只搜尋指定 app 目錄")
    parser.add_argument("--context", type=int, default=0, metavar="N", help="顯示前後 N 行上下文")
    parser.add_argument("--case-sensitive", action="store_true", help="區分大小寫（預設不區分）")

    args = parser.parse_args()

    project_root = _find_project_root(Path(args.project).resolve())
    search_dirs = _get_search_dirs(project_root, args.app)

    try:
        pattern = _build_pattern(args.pattern, args.regex, args.case_sensitive)
    except re.error as e:
        print(f"正則表達式錯誤: {e}", file=sys.stderr)
        sys.exit(1)

    all_results: list[dict] = []
    scanned = 0
    for file_path in _iter_files(search_dirs, args.include):
        scanned += 1
        all_results.extend(_search_file(file_path, pattern, args.context, project_root))

    _print_results(all_results, args.pattern, args.context, scanned)


if __name__ == "__main__":
    main()
