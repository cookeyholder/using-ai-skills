#!/usr/bin/env python3
"""
獨立的 Django 專案快照生成器

不依賴 Django 管理命令，可以直接執行。
用於 django-snapshot skill，完全獨立運作。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


class StandaloneSnapshotGenerator:
    """獨立的 Django 專案快照生成器"""

    def __init__(self, project_root: Path, output_dir: Path):
        self.project_root = Path(project_root).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 儲存各類資料
        self.templates_data = {}
        self.models_data = {}
        self.views_data = {}
        self.urls_data = {}
        self.forms_data = {}
        self.apps_data = {}

        # 統計資訊
        self.stats = {
            "templates": 0,
            "models": 0,
            "views": 0,
            "urls": 0,
            "forms": 0,
            "apps": 0,
        }

    def find_template_files(self) -> list[Path]:
        """搜尋所有 HTML 模板檔案"""
        templates = []

        # 常見的 Django 模板目錄
        template_dirs = [
            self.project_root / "templates",
            self.project_root / "src" / "templates",
        ]

        # 也掃描各個 app 目錄下的 templates
        for app_dir in self.project_root.rglob("*/templates"):
            if app_dir.is_dir() and ".venv" not in str(app_dir):
                template_dirs.append(app_dir)

        # 收集所有 .html 檔案
        for template_dir in template_dirs:
            if template_dir.exists():
                for html_file in template_dir.rglob("*.html"):
                    # 排除虛擬環境和隱藏目錄
                    if ".venv" not in str(html_file) and "/.venv/" not in str(
                        html_file
                    ):
                        templates.append(html_file)

        return sorted(set(templates))

    def scan_template(self, template_path: Path) -> dict[str, Any]:
        """掃描單一模板檔案"""
        try:
            with template_path.open("r", encoding="utf-8") as f:
                content = f.read()

            # 計算基本統計
            lines = content.split("\n")

            # 偵測依賴關係
            extends_pattern = r'{%\s*extends\s+["\']([^"\']+)["\']\s*%}'
            includes_pattern = r'{%\s*include\s+["\']([^"\']+)["\']\s*%}'

            extends = re.findall(extends_pattern, content)
            includes = re.findall(includes_pattern, content)

            # 提取相對路徑
            try:
                rel_path = template_path.relative_to(self.project_root)
            except ValueError:
                rel_path = template_path.name

            return {
                "file_path": str(template_path),
                "relative_path": str(rel_path),
                "lines": len(lines),
                "size_bytes": len(content),
                "extends": extends,
                "includes": includes,
                "has_content": len(content.strip()) > 0,
            }

        except Exception as e:
            print(f"  警告: 無法讀取模板 {template_path}: {e}")
            return {}

    def scan_templates(self) -> None:
        """掃描所有模板"""
        print("掃描 Templates...")
        templates = self.find_template_files()

        for template_path in templates:
            template_info = self.scan_template(template_path)
            if template_info:
                # 使用相對路徑作為鍵
                key = template_info.get("relative_path", template_path.name)
                self.templates_data[key] = template_info
                self.stats["templates"] += 1

        print(f"  ✓ 找到 {self.stats['templates']} 個模板")

    def find_python_files(self, pattern: str = "*.py") -> list[Path]:
        """搜尋 Python 檔案"""
        python_files = []

        # 掃描 src 目錄
        src_dir = self.project_root / "src"
        if src_dir.exists():
            for py_file in src_dir.rglob(pattern):
                if ".venv" not in str(py_file) and "__pycache__" not in str(py_file):
                    python_files.append(py_file)

        # 也掃描根目錄
        for py_file in self.project_root.rglob(pattern):
            if (
                ".venv" not in str(py_file)
                and "__pycache__" not in str(py_file)
                and "migrations" not in str(py_file)
            ):
                python_files.append(py_file)

        return sorted(set(python_files))

    def scan_models(self) -> None:
        """掃描 Django Models"""
        print("掃描 Models...")

        model_files = [f for f in self.find_python_files() if f.name == "models.py"]

        for model_file in model_files:
            try:
                with model_file.open("r", encoding="utf-8") as f:
                    content = f.read()

                # 簡單的類別檢測
                class_pattern = r"class\s+(\w+)\s*\([^)]*Model[^)]*\):"
                models = re.findall(class_pattern, content)

                if models:
                    try:
                        rel_path = model_file.relative_to(self.project_root)
                    except ValueError:
                        rel_path = model_file.name

                    for model_name in models:
                        key = f"{rel_path.parent.name}.{model_name}"
                        self.models_data[key] = {
                            "name": model_name,
                            "file_path": str(model_file),
                            "relative_path": str(rel_path),
                            "app": rel_path.parent.name,
                        }
                        self.stats["models"] += 1

            except Exception as e:
                print(f"  警告: 無法讀取 {model_file}: {e}")

        print(f"  ✓ 找到 {self.stats['models']} 個 Models")

    def scan_views(self) -> None:
        """掃描 Django Views"""
        print("掃描 Views...")

        view_files = [f for f in self.find_python_files() if f.name == "views.py"]

        for view_file in view_files:
            try:
                with view_file.open("r", encoding="utf-8") as f:
                    content = f.read()

                # 檢測函數視圖
                func_pattern = r"def\s+(\w+)\s*\([^)]*request[^)]*\):"
                functions = re.findall(func_pattern, content)

                # 檢測類視圖
                class_pattern = r"class\s+(\w+)\s*\([^)]*View[^)]*\):"
                classes = re.findall(class_pattern, content)

                if functions or classes:
                    try:
                        rel_path = view_file.relative_to(self.project_root)
                    except ValueError:
                        rel_path = view_file.name

                    app_name = rel_path.parent.name

                    for func_name in functions:
                        key = f"{app_name}.{func_name}"
                        self.views_data[key] = {
                            "name": func_name,
                            "type": "function",
                            "file_path": str(view_file),
                            "relative_path": str(rel_path),
                            "app": app_name,
                        }
                        self.stats["views"] += 1

                    for class_name in classes:
                        key = f"{app_name}.{class_name}"
                        self.views_data[key] = {
                            "name": class_name,
                            "type": "class",
                            "file_path": str(view_file),
                            "relative_path": str(rel_path),
                            "app": app_name,
                        }
                        self.stats["views"] += 1

            except Exception as e:
                print(f"  警告: 無法讀取 {view_file}: {e}")

        print(f"  ✓ 找到 {self.stats['views']} 個 Views")

    def scan_apps(self) -> None:
        """掃描 Django Apps"""
        print("掃描 Apps...")

        # 查找所有包含 apps.py 的目錄
        app_files = [f for f in self.find_python_files() if f.name == "apps.py"]

        for app_file in app_files:
            try:
                app_dir = app_file.parent
                app_name = app_dir.name

                # 檢查是否為有效的 Django app（包含 __init__.py）
                if (app_dir / "__init__.py").exists():
                    try:
                        rel_path = app_dir.relative_to(self.project_root)
                    except ValueError:
                        rel_path = app_dir

                    self.apps_data[app_name] = {
                        "name": app_name,
                        "path": str(app_dir),
                        "relative_path": str(rel_path),
                        "has_models": (app_dir / "models.py").exists(),
                        "has_views": (app_dir / "views.py").exists(),
                        "has_urls": (app_dir / "urls.py").exists(),
                        "has_templates": (app_dir / "templates").exists(),
                    }
                    self.stats["apps"] += 1

            except Exception as e:
                print(f"  警告: 無法處理 app {app_file}: {e}")

        print(f"  ✓ 找到 {self.stats['apps']} 個 Apps")

    def save_json(self, data: dict[str, Any], filename: str) -> None:
        """儲存 JSON 檔案"""
        output_path = self.output_dir / filename
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"  ✓ {filename}")

    def generate(self) -> None:
        """生成所有快照"""
        print("開始生成獨立快照...")
        print(f"專案根目錄: {self.project_root}")
        print(f"輸出目錄: {self.output_dir}")
        print()

        # 掃描各類檔案
        self.scan_apps()
        self.scan_templates()
        self.scan_models()
        self.scan_views()

        # 儲存結果
        print("\n儲存快照檔案...")
        self.save_json(self.templates_data, "snapshot_templates.json")
        self.save_json(self.models_data, "snapshot_models.json")
        self.save_json(self.views_data, "snapshot_views.json")
        self.save_json(self.apps_data, "snapshot_apps.json")

        # 生成並儲存完整快照 snapshot.json
        from datetime import datetime

        full_snapshot = {
            "generated_at": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "apps": self.apps_data,
            "templates": self.templates_data,
            "models": self.models_data,
            "views": self.views_data,
            "stats": self.stats,
        }
        self.save_json(full_snapshot, "snapshot.json")

        # 儲存索引
        index_data = {
            "generator": "StandaloneSnapshotGenerator",
            "version": "2.0",
            "project_root": str(self.project_root),
            "stats": self.stats,
            "files": {
                "main": "snapshot.json",
                "templates": "snapshot_templates.json",
                "models": "snapshot_models.json",
                "views": "snapshot_views.json",
                "apps": "snapshot_apps.json",
            },
        }
        self.save_json(index_data, "snapshot_index.json")

        # 顯示摘要
        print("\n" + "=" * 60)
        print("📊 快照生成完成")
        print("=" * 60)
        print(f"Apps:      {self.stats['apps']} 個")
        print(f"Templates: {self.stats['templates']} 個")
        print(f"Models:    {self.stats['models']} 個")
        print(f"Views:     {self.stats['views']} 個")
        print("=" * 60)
        print(f"\n✓ 快照已儲存至: {self.output_dir}")


def main():
    """主程式進入點"""
    parser = argparse.ArgumentParser(
        description="獨立的 Django 專案快照生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例：
  # 在當前目錄生成快照
  python standalone_snapshot.py

  # 指定專案目錄
  python standalone_snapshot.py -p /path/to/project

  # 指定輸出目錄
  python standalone_snapshot.py -o /path/to/output

  # 完整參數
  python standalone_snapshot.py -p /path/to/project -o snapshots
        """,
    )

    parser.add_argument(
        "-p",
        "--project",
        type=str,
        default=".",
        help="Django 專案根目錄（預設: 當前目錄）",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="snapshots",
        help="快照輸出目錄（預設: snapshots）",
    )

    parser.add_argument("-v", "--verbose", action="store_true", help="顯示詳細資訊")

    args = parser.parse_args()

    try:
        project_root = Path(args.project).resolve()
        if not project_root.exists():
            print(f"錯誤: 專案目錄不存在: {project_root}", file=sys.stderr)
            sys.exit(1)

        # 檢測是否為 Django 專案
        has_manage_py = (project_root / "manage.py").exists()
        has_src_manage_py = (project_root / "src" / "manage.py").exists()

        if not (has_manage_py or has_src_manage_py):
            print("警告: 未偵測到 manage.py，可能不是 Django 專案")
            print("繼續執行掃描...")

        # 生成快照
        generator = StandaloneSnapshotGenerator(
            project_root=project_root, output_dir=project_root / args.output
        )
        generator.generate()

        sys.exit(0)

    except KeyboardInterrupt:
        print("\n\n中斷執行")
        sys.exit(130)
    except Exception as e:
        print(f"\n錯誤: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
