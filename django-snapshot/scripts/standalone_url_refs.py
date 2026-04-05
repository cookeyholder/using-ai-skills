#!/usr/bin/env python3
"""
standalone_url_refs.py — 分析 URL name 在模板與 Python 程式碼中的引用

功能等同 django-vibe-snapshot 的 snapshot_url_refs management command，
但完全不依賴 Django 環境。從 snapshot_urls.json 讀取 URL 清單，
接著搜尋所有 {% url %} 標籤和 reverse()/redirect() 呼叫。

用法：
  python standalone_url_refs.py [選項]
  python standalone_url_refs.py --list          # 列出所有 URL names
  python standalone_url_refs.py --url login     # 分析特定 URL 的引用
  python standalone_url_refs.py --unused        # 找出未被引用的 URL
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterator


# ===== 路徑偵測 =====

def _find_project_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "manage.py").exists() or (candidate / "src" / "manage.py").exists():
            return candidate
    return start


def _get_src_dir(project_root: Path) -> Path:
    src = project_root / "src"
    return src if src.exists() else project_root


def _find_snapshot_dir(project_root: Path) -> Path | None:
    """尋找 snapshot_urls.json 所在目錄"""
    candidates = [
        project_root / "snapshots",
        project_root / "django-vibe-snapshot",
        project_root,
    ]
    for c in candidates:
        if (c / "snapshot_urls.json").exists():
            return c
    return None


# ===== URL 資料載入 =====

def _load_url_names(snapshot_dir: Path) -> list[str]:
    """從 snapshot_urls.json 取得所有 URL names"""
    urls_file = snapshot_dir / "snapshot_urls.json"
    try:
        data = json.loads(urls_file.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"警告: 無法讀取 {urls_file}: {e}", file=sys.stderr)
        return []

    names: list[str] = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and item.get("name"):
                names.append(item["name"])
    elif isinstance(data, dict):
        for entry in data.values():
            if isinstance(entry, dict) and entry.get("name"):
                names.append(entry["name"])
    return sorted(set(n for n in names if n))


# ===== 搜尋邏輯 =====

def _iter_files(root: Path, extensions: tuple[str, ...]) -> Iterator[Path]:
    exclude = {".venv", "__pycache__", "node_modules", ".git", "migrations"}
    for f in root.rglob("*"):
        if not f.is_file():
            continue
        if any(p in f.parts for p in exclude):
            continue
        if f.suffix in extensions:
            yield f


# 模板中 {% url 'name' %} 或 {% url "name" %}
_TEMPLATE_URL_RE = re.compile(r"""{%[-\s]*url\s+['"]([^'"]+)['"]""")
# Python 中 reverse('name') / redirect('name') / reverse_lazy('name')
_PYTHON_REF_RE = re.compile(
    r"""(?:reverse|redirect|reverse_lazy)\s*\(\s*['"]([^'"]+)['"]"""
)


def _find_template_references(src_dir: Path) -> dict[str, list[dict]]:
    """掃描所有模板，收集 {% url %} 引用"""
    refs: dict[str, list[dict]] = {}
    for f in _iter_files(src_dir, (".html",)):
        try:
            content = f.read_text(encoding="utf-8")
        except Exception:
            continue
        for i, line in enumerate(content.splitlines(), 1):
            for m in _TEMPLATE_URL_RE.finditer(line):
                name = m.group(1)
                refs.setdefault(name, []).append({"file": str(f), "lineno": i, "line": line.strip()})
    return refs


def _find_python_references(src_dir: Path) -> dict[str, list[dict]]:
    """掃描所有 Python 檔案，收集 reverse()/redirect() 引用"""
    refs: dict[str, list[dict]] = {}
    for f in _iter_files(src_dir, (".py",)):
        try:
            content = f.read_text(encoding="utf-8")
        except Exception:
            continue
        for i, line in enumerate(content.splitlines(), 1):
            for m in _PYTHON_REF_RE.finditer(line):
                name = m.group(1)
                refs.setdefault(name, []).append({"file": str(f), "lineno": i, "line": line.strip()})
    return refs


# ===== 輸出 =====

def _print_list(url_names: list[str]) -> None:
    print(f"共 {len(url_names)} 個 URL names:")
    for name in url_names:
        print(f"  {name}")


def _print_references(
    url_name: str,
    tmpl_refs: dict[str, list[dict]],
    py_refs: dict[str, list[dict]],
) -> None:
    t_list = tmpl_refs.get(url_name, [])
    p_list = py_refs.get(url_name, [])
    total = len(t_list) + len(p_list)
    print(f"\n🔗 URL name: '{url_name}'  (共 {total} 個引用)")

    if t_list:
        print(f"\n  模板引用 ({len(t_list)} 個):")
        for r in t_list:
            print(f"    {r['file']}:{r['lineno']}")
            print(f"      {r['line']}")
    if p_list:
        print(f"\n  Python 引用 ({len(p_list)} 個):")
        for r in p_list:
            print(f"    {r['file']}:{r['lineno']}")
            print(f"      {r['line']}")
    if not t_list and not p_list:
        print("  ⚠️  未找到任何引用")


def _print_unused(
    url_names: list[str],
    tmpl_refs: dict[str, list[dict]],
    py_refs: dict[str, list[dict]],
) -> None:
    unused = [n for n in url_names if n not in tmpl_refs and n not in py_refs]
    print(f"\n未被引用的 URL names（共 {len(unused)} 個）：")
    for name in unused:
        print(f"  ⚠️  {name}")
    if not unused:
        print("  ✅ 所有 URL names 都有被引用")


def _print_all_summary(
    url_names: list[str],
    tmpl_refs: dict[str, list[dict]],
    py_refs: dict[str, list[dict]],
) -> None:
    print("\nURL 引用摘要")
    print("=" * 60)
    referenced: set[str] = set(tmpl_refs) | set(py_refs)
    for name in url_names:
        t_count = len(tmpl_refs.get(name, []))
        p_count = len(py_refs.get(name, []))
        total = t_count + p_count
        status = "✅" if total > 0 else "⚠️ "
        print(f"  {status}  {name:50s}  模板:{t_count}  Python:{p_count}")
    orphans = sorted(referenced - set(url_names))
    if orphans:
        print(f"\n引用了但不在 snapshot 中的 URL names（共 {len(orphans)} 個）：")
        for name in orphans:
            print(f"  ❓ {name}")


# ===== 主程式 =====

def main() -> None:
    parser = argparse.ArgumentParser(
        description="分析 URL name 在模板與 Python 中的引用（無需 Django 環境）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例：
  python standalone_url_refs.py --list
  python standalone_url_refs.py --url registration:student-list
  python standalone_url_refs.py --unused
  python standalone_url_refs.py          # 顯示所有 URL 引用摘要
        """,
    )
    parser.add_argument("-p", "--project", default=".", help="專案根目錄")
    parser.add_argument("-s", "--snapshots", help="snapshot_urls.json 所在目錄（預設自動偵測）")
    parser.add_argument("--list", action="store_true", help="只列出所有 URL names")
    parser.add_argument("--url", metavar="NAME", help="分析特定 URL name 的引用")
    parser.add_argument("--unused", action="store_true", help="列出未被引用的 URL names")

    args = parser.parse_args()

    project_root = _find_project_root(Path(args.project).resolve())
    src_dir = _get_src_dir(project_root)

    if args.snapshots:
        snapshot_dir = Path(args.snapshots)
    else:
        snapshot_dir = _find_snapshot_dir(project_root)

    if snapshot_dir is None:
        print("錯誤: 找不到 snapshot_urls.json，請先執行 standalone_snapshot.py 生成快照", file=sys.stderr)
        sys.exit(1)

    url_names = _load_url_names(snapshot_dir)

    if args.list:
        _print_list(url_names)
        return

    print("掃描模板引用...")
    tmpl_refs = _find_template_references(src_dir)
    print("掃描 Python 引用...")
    py_refs = _find_python_references(src_dir)

    if args.url:
        _print_references(args.url, tmpl_refs, py_refs)
    elif args.unused:
        _print_unused(url_names, tmpl_refs, py_refs)
    else:
        _print_all_summary(url_names, tmpl_refs, py_refs)


if __name__ == "__main__":
    main()
