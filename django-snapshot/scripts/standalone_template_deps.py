#!/usr/bin/env python3
"""
standalone_template_deps.py — 分析 Django 模板的繼承與引入依賴關係

功能等同 django-vibe-snapshot 的 snapshot_template_deps management command，
但完全不依賴 Django 環境。直接掃描 HTML 模板，分析 extends/include 依賴鏈。

用法：
  python standalone_template_deps.py [選項]
  python standalone_template_deps.py --template base.html   # 分析特定模板
  python standalone_template_deps.py --orphans              # 找未被引用的模板
  python standalone_template_deps.py --tree                 # 印出繼承樹
"""
from __future__ import annotations

import argparse
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


def _find_template_dirs(project_root: Path) -> list[Path]:
    """找出所有模板目錄"""
    src_dir = _get_src_dir(project_root)
    dirs: list[Path] = []
    exclude = {".venv", "__pycache__", "node_modules", ".git"}
    for candidate in [
        src_dir / "templates",
        project_root / "templates",
    ]:
        if candidate.exists():
            dirs.append(candidate)
    for d in src_dir.rglob("*/templates"):
        if d.is_dir() and not any(p in d.parts for p in exclude):
            if d not in dirs:
                dirs.append(d)
    return dirs


# ===== 模板掃描 =====

_EXTENDS_RE  = re.compile(r"""{%[-\s]*extends\s+['"]([^'"]+)['"]""")
_INCLUDE_RE  = re.compile(r"""{%[-\s]*include\s+['"]([^'"]+)['"]""")
_BLOCK_RE    = re.compile(r"""{%[-\s]*block\s+(\w+)""")


def _iter_templates(template_dirs: list[Path]) -> Iterator[tuple[Path, str]]:
    """產生 (絕對路徑, 模板名稱)，模板名稱為相對於 templates/ 的路徑"""
    seen: set[Path] = set()
    for base in template_dirs:
        for f in base.rglob("*.html"):
            if f in seen:
                continue
            seen.add(f)
            try:
                rel = str(f.relative_to(base))
            except ValueError:
                rel = f.name
            yield f, rel


def _scan_all_templates(template_dirs: list[Path]) -> dict[str, dict]:
    """掃描所有模板，回傳 {name: {extends, includes, blocks, file}} 字典"""
    result: dict[str, dict] = {}
    for file_path, name in _iter_templates(template_dirs):
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            continue
        extends_list = _EXTENDS_RE.findall(content)
        includes_list = _INCLUDE_RE.findall(content)
        blocks_list = list(set(_BLOCK_RE.findall(content)))
        result[name] = {
            "file": str(file_path),
            "extends": extends_list[0] if extends_list else None,
            "includes": sorted(set(includes_list)),
            "blocks": sorted(blocks_list),
            "lines": len(content.splitlines()),
        }
    return result


# ===== 依賴分析 =====

def _build_reverse_map(templates: dict[str, dict]) -> dict[str, list[str]]:
    """建立反向依賴圖：{被引用模板 → [引用它的模板]}"""
    reverse: dict[str, list[str]] = {}
    for name, info in templates.items():
        if info["extends"]:
            reverse.setdefault(info["extends"], []).append(name)
        for inc in info["includes"]:
            reverse.setdefault(inc, []).append(name)
    return reverse


def _find_dependents(
    template_name: str,
    reverse_map: dict[str, list[str]],
    visited: set[str] | None = None,
) -> list[str]:
    """找出所有（直接與間接）依賴 template_name 的模板"""
    if visited is None:
        visited = set()
    if template_name in visited:
        return []
    visited.add(template_name)
    direct = reverse_map.get(template_name, [])
    all_deps = list(direct)
    for dep in direct:
        all_deps.extend(_find_dependents(dep, reverse_map, visited))
    return list(dict.fromkeys(all_deps))  # 保留順序並去重


def _inheritance_chain(
    template_name: str,
    templates: dict[str, dict],
    visited: set[str] | None = None,
) -> list[str]:
    """追溯 extends 繼承鏈（自底向上）"""
    if visited is None:
        visited = set()
    if template_name in visited:
        return []
    visited.add(template_name)
    info = templates.get(template_name)
    if not info or not info["extends"]:
        return [template_name]
    return [template_name] + _inheritance_chain(info["extends"], templates, visited)


# ===== 輸出格式 =====

def _print_template_info(
    template_name: str,
    templates: dict[str, dict],
    reverse_map: dict[str, list[str]],
) -> None:
    info = templates.get(template_name)
    if not info:
        print(f"錯誤: 找不到模板 '{template_name}'")
        print("\n可用的模板:")
        for name in sorted(templates):
            print(f"  {name}")
        return

    chain = _inheritance_chain(template_name, templates)

    print(f"\n📄 模板: {template_name}")
    print(f"   檔案: {info['file']}")
    print(f"   行數: {info['lines']}")
    print()

    print("繼承鏈 (extends):")
    for i, t in enumerate(chain):
        indent = "  " * i
        print(f"  {indent}→ {t}")

    if info["includes"]:
        print(f"\n引入的模板 (include)  [{len(info['includes'])} 個]:")
        for inc in info["includes"]:
            print(f"  • {inc}")

    if info["blocks"]:
        print(f"\nBlock 定義  [{len(info['blocks'])} 個]:")
        for b in info["blocks"]:
            print(f"  {{ {b} }}")

    dependents = _find_dependents(template_name, reverse_map)
    if dependents:
        print(f"\n被以下模板引用  [{len(dependents)} 個]:")
        for d in sorted(dependents):
            print(f"  ← {d}")
    else:
        print("\n沒有其他模板引用此模板")


def _print_orphans(
    templates: dict[str, dict],
    reverse_map: dict[str, list[str]],
) -> None:
    orphans = [name for name in templates if name not in reverse_map]
    # 排除 base templates（通常是被 extends 的起點，但本身不繼承任何東西）
    base_templates = [name for name in orphans if not templates[name]["extends"]]
    pure_orphans = [name for name in orphans if templates[name]["extends"]]

    print(f"\n孤立模板（未被任何模板引用，且自身有 extends）：共 {len(pure_orphans)} 個")
    for name in sorted(pure_orphans):
        print(f"  ⚠️  {name}")

    print(f"\n根模板（未被引用、也無 extends）：共 {len(base_templates)} 個")
    for name in sorted(base_templates):
        print(f"  🌲 {name}")


def _print_tree(templates: dict[str, dict], reverse_map: dict[str, list[str]]) -> None:
    """印出以根模板為起點的繼承樹"""
    # 找根模板（無 extends 且被其他模板 extends）
    roots = sorted(
        name for name, info in templates.items()
        if not info["extends"] and name in reverse_map
    )

    def _print_node(name: str, depth: int, visited: set[str]) -> None:
        indent = "  " * depth
        marker = "├─ " if depth > 0 else "🌲 "
        info = templates.get(name, {})
        blocks = f"  [{', '.join(info.get('blocks', [])[:3])}]" if info.get("blocks") else ""
        print(f"{indent}{marker}{name}{blocks}")
        if name in visited:
            return
        visited.add(name)
        children = sorted(
            n for n, i in templates.items()
            if i.get("extends") == name
        )
        for child in children:
            _print_node(child, depth + 1, visited)

    print("\n模板繼承樹：")
    print("=" * 60)
    for root in roots:
        _print_node(root, 0, set())

    # 孤立的（有 extends 但 parent 不在 templates 中）
    broken = sorted(
        name for name, info in templates.items()
        if info["extends"] and info["extends"] not in templates
    )
    if broken:
        print(f"\n⚠️  繼承鏈中斷（parent 不在掃描範圍）：")
        for name in broken:
            print(f"  {name}  →  {templates[name]['extends']} (missing)")


def _print_summary(templates: dict[str, dict], reverse_map: dict[str, list[str]]) -> None:
    total = len(templates)
    with_extends = sum(1 for i in templates.values() if i["extends"])
    with_includes = sum(1 for i in templates.values() if i["includes"])
    referenced = len(reverse_map)
    orphans = total - referenced

    print("\n模板依賴關係摘要")
    print("=" * 50)
    print(f"  總模板數:       {total}")
    print(f"  有 extends:     {with_extends}")
    print(f"  有 include:     {with_includes}")
    print(f"  被引用的模板:   {referenced}")
    print(f"  未被引用:       {orphans}")
    print("=" * 50)


# ===== 主程式 =====

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Django 模板繼承與依賴分析工具（無需 Django 環境）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例：
  python standalone_template_deps.py --summary
  python standalone_template_deps.py --tree
  python standalone_template_deps.py --template base.html
  python standalone_template_deps.py --orphans
        """,
    )
    parser.add_argument("-p", "--project", default=".", help="專案根目錄")
    parser.add_argument("--template", metavar="NAME", help="分析特定模板的依賴關係")
    parser.add_argument("--orphans", action="store_true", help="列出未被引用的模板")
    parser.add_argument("--tree", action="store_true", help="顯示模板繼承樹")
    parser.add_argument("--summary", action="store_true", help="顯示摘要統計（預設）")

    args = parser.parse_args()

    project_root = _find_project_root(Path(args.project).resolve())
    template_dirs = _find_template_dirs(project_root)

    if not template_dirs:
        print("找不到任何模板目錄", file=sys.stderr)
        sys.exit(1)

    print(f"掃描 {len(template_dirs)} 個模板目錄...")
    templates = _scan_all_templates(template_dirs)
    print(f"  ✓ 找到 {len(templates)} 個模板")

    if not templates:
        print("未找到任何 .html 模板")
        sys.exit(0)

    reverse_map = _build_reverse_map(templates)

    if args.template:
        _print_template_info(args.template, templates, reverse_map)
    elif args.orphans:
        _print_orphans(templates, reverse_map)
    elif args.tree:
        _print_tree(templates, reverse_map)
    else:
        # 預設：顯示摘要
        _print_summary(templates, reverse_map)


if __name__ == "__main__":
    main()
