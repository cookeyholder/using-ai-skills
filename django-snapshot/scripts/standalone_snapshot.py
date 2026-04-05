#!/usr/bin/env python3
"""
增強版獨立 Django 專案快照生成器（v2.1）

不依賴 Django 管理命令或 Django runtime，可以直接執行。
功能與 django-vibe-snapshot 套件的 SnapshotGenerator 完全對等：
- Models（AST 欄位詳情：type/null/blank/related_model/upload_to）
- Views（AST：bases/mixins/decorators/permissions/class attributes）
- URLs（AST 靜態解析 urls.py）
- Templates（url_tags/extends/includes/blocks/title）
- Forms（AST：Meta class/fields）
- Imports（per-module import 追蹤）
- Static Assets（{% static %} 分類統計）
- Cross-references（URL→View、Template→URL、Model references）
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class StandaloneSnapshotGenerator:
    """增強版獨立 Django 專案快照生成器 v2.1

    功能與 django-vibe-snapshot.SnapshotGenerator 完全對等，
    但完全不依賴 Django runtime，改用 Python AST 靜態解析。
    """

    def __init__(self, project_root: Path, output_dir: Path):
        self.project_root = Path(project_root).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 支援 src/ 子目錄結構
        self.src_dir = self.project_root / "src"
        if not self.src_dir.exists():
            self.src_dir = self.project_root

        # 儲存各類資料
        self.templates_data: dict[str, Any] = {}
        self.models_data: dict[str, Any] = {}
        self.views_data: dict[str, Any] = {}
        self.urls_data: dict[str, Any] = {}
        self.forms_data: dict[str, Any] = {}
        self.imports_data: dict[str, Any] = {}
        self.static_assets_data: dict[str, Any] = {}
        self.cross_references: dict[str, Any] = {}
        self.apps_data: dict[str, Any] = {}

    # ===== 工具方法 =====

    def _get_app_dirs(self) -> list[Path]:
        """找出所有 Django app 目錄（包含 apps.py 且有 __init__.py）"""
        app_dirs = []
        for apps_py in self.src_dir.rglob("apps.py"):
            parts = apps_py.parts
            if any(p in parts for p in (".venv", "__pycache__", "migrations", "node_modules")):
                continue
            app_dir = apps_py.parent
            if (app_dir / "__init__.py").exists():
                app_dirs.append(app_dir)
        return sorted(set(app_dirs))

    def _get_app_name(self, path: Path) -> str:
        """取得 path 相對於 src_dir 的 app 名稱"""
        try:
            rel = path.relative_to(self.src_dir)
            return str(rel.parts[0]) if rel.parts else path.name
        except ValueError:
            return path.name

    def _write_snapshot(self, name: str, data: dict) -> None:
        """寫入單一 snapshot JSON 檔案"""
        output_file = self.output_dir / f"snapshot_{name}.json"
        output_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  ✓ snapshot_{name}.json")

    # ===== Apps 掃描 =====

    def _scan_apps(self) -> None:
        """掃描 Django Apps"""
        print("掃描 Apps...")
        for app_dir in self._get_app_dirs():
            app_name = self._get_app_name(app_dir)
            try:
                rel = str(app_dir.relative_to(self.project_root))
            except ValueError:
                rel = str(app_dir)

            self.apps_data[app_name] = {
                "name": app_name,
                "path": str(app_dir),
                "relative_path": rel,
                "has_models": (app_dir / "models.py").exists(),
                "has_views": (app_dir / "views.py").exists() or bool(list(app_dir.glob("*_views.py"))),
                "has_urls": (app_dir / "urls.py").exists(),
                "has_forms": (app_dir / "forms.py").exists(),
                "has_templates": (app_dir / "templates").exists(),
            }
        print(f"  ✓ 找到 {len(self.apps_data)} 個 Apps")

    # ===== Models 掃描（AST）=====

    def _scan_models(self) -> None:
        """掃描所有 Django Models（使用 AST 提取欄位詳情）"""
        print("掃描 Models...")
        for app_dir in self._get_app_dirs():
            app_name = self._get_app_name(app_dir)
            model_file = app_dir / "models.py"
            if not model_file.exists():
                continue
            app_models = self._extract_models_from_file(model_file, app_name)
            if app_models:
                self.models_data[app_name] = app_models

        count = sum(len(m) for m in self.models_data.values())
        print(f"  ✓ 找到 {count} 個 Models")

    def _extract_models_from_file(self, file_path: Path, app_name: str) -> dict:
        """從 models.py 使用 AST 提取 Model 定義（欄位類型、null、blank、related_model）"""
        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(file_path))
        except Exception as e:
            print(f"  警告: 無法解析 {file_path}: {e}")
            return {}

        models = {}
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            base_names = self._extract_base_names(node.bases)
            if not any("Model" in b for b in base_names):
                continue

            fields_info: dict[str, Any] = {}
            methods: list[str] = []
            verbose_name = ""

            for child in node.body:
                # 欄位定義：field = models.CharField(...)
                if isinstance(child, ast.Assign):
                    for target in child.targets:
                        if not isinstance(target, ast.Name):
                            continue
                        field_name = target.id
                        if field_name.startswith("_") or field_name in ("Meta", "objects"):
                            continue
                        field_info = self._extract_field_info(child.value)
                        if field_info:
                            fields_info[field_name] = field_info
                # 方法
                elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not child.name.startswith("_") or child.name in ("__str__", "__repr__"):
                        methods.append(child.name)
                # Meta class
                elif isinstance(child, ast.ClassDef) and child.name == "Meta":
                    for meta_item in child.body:
                        if isinstance(meta_item, ast.Assign):
                            for t in meta_item.targets:
                                if isinstance(t, ast.Name) and t.id == "verbose_name":
                                    if isinstance(meta_item.value, ast.Constant):
                                        verbose_name = str(meta_item.value.value)

            try:
                file_rel = str(file_path.relative_to(self.project_root))
            except ValueError:
                file_rel = str(file_path)

            models[node.name] = {
                "app": app_name,
                "file": file_rel,
                "verbose_name": verbose_name,
                "fields": fields_info,
                "methods": methods[:20],
                "doc": ast.get_docstring(node) or "",
            }

        return models

    def _extract_field_info(self, value_node: ast.expr) -> dict | None:
        """從 AST Call 節點提取 Django 欄位資訊"""
        if not isinstance(value_node, ast.Call):
            return None

        func = value_node.func
        if isinstance(func, ast.Attribute):
            field_type = func.attr
        elif isinstance(func, ast.Name):
            field_type = func.id
        else:
            return None

        # 只處理已知的 Django 欄位類型
        django_fields = {
            "CharField", "TextField", "IntegerField", "FloatField", "BooleanField",
            "DateField", "DateTimeField", "EmailField", "URLField", "FileField",
            "ImageField", "ForeignKey", "OneToOneField", "ManyToManyField",
            "AutoField", "BigAutoField", "PositiveIntegerField", "SlugField",
            "JSONField", "UUIDField", "DecimalField", "TimeField", "SmallIntegerField",
            "BigIntegerField", "BinaryField", "GenericIPAddressField",
            "PositiveSmallIntegerField", "DurationField",
        }
        if field_type not in django_fields:
            return None

        info: dict[str, Any] = {"type": field_type}

        # 提取關鍵字引數
        for kw in value_node.keywords:
            if kw.arg in ("null", "blank", "max_length", "upload_to", "to", "on_delete"):
                if isinstance(kw.value, ast.Constant):
                    info[kw.arg] = kw.value.value
                elif isinstance(kw.value, ast.Name):
                    info[kw.arg] = kw.value.id
                elif isinstance(kw.value, ast.Attribute):
                    info[kw.arg] = ast.unparse(kw.value)

        # FK/OneToOne/M2M 的第一個位置引數是 to（related_model）
        if field_type in ("ForeignKey", "OneToOneField", "ManyToManyField"):
            if value_node.args:
                first_arg = value_node.args[0]
                if isinstance(first_arg, ast.Constant):
                    info["related_model"] = first_arg.value
                elif isinstance(first_arg, ast.Name):
                    info["related_model"] = first_arg.id
                elif isinstance(first_arg, ast.Attribute):
                    info["related_model"] = ast.unparse(first_arg)
            elif "to" in info:
                info["related_model"] = info.pop("to")

        return info

    # ===== Views 掃描（AST）=====

    def _scan_views(self) -> None:
        """掃描所有 Views（AST 提取 bases/mixins/decorators/permissions/class attributes）"""
        print("掃描 Views...")
        for app_dir in self._get_app_dirs():
            app_name = self._get_app_name(app_dir)
            view_files = [app_dir / "views.py"] + list(app_dir.glob("*_views.py"))
            app_views: dict[str, Any] = {}
            for vf in view_files:
                if vf.exists():
                    views_info = self._extract_views_from_file(vf)
                    if views_info:
                        app_views[vf.stem] = views_info
            if app_views:
                self.views_data[app_name] = app_views

        count = sum(
            len(v) for app_v in self.views_data.values() for v in app_v.values()
        )
        print(f"  ✓ 找到 {count} 個 Views")

    def _extract_views_from_file(self, file_path: Path) -> dict:
        """從 views 檔案使用 AST 提取視圖（類別/函式）詳情"""
        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(file_path))
        except Exception as e:
            print(f"  警告: 無法解析 {file_path}: {e}")
            return {}

        views: dict[str, Any] = {}
        view_kw = ["View", "Mixin", "Create", "Update", "Delete", "List", "Detail", "Form"]

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                base_names = self._extract_base_names(node.bases)
                if not any(any(kw in b for kw in view_kw) for b in base_names if b):
                    continue

                class_attrs = self._extract_class_attributes(node)
                decorators = self._extract_decorators(node.decorator_list)
                permissions = self._infer_permissions(base_names, decorators)
                methods = [
                    n.name for n in node.body
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]

                view_info: dict[str, Any] = {
                    "type": "class",
                    "bases": base_names,
                    "mixins": [b for b in base_names if "Mixin" in b],
                    "methods": methods,
                    "decorators": decorators,
                    "doc": ast.get_docstring(node) or "",
                }

                # 加入存在的類別屬性
                for attr in (
                    "template_name", "model", "queryset", "form_class",
                    "success_url", "context_object_name", "fields",
                    "pk_url_kwarg", "slug_url_kwarg", "paginate_by",
                ):
                    if class_attrs.get(attr) is not None:
                        view_info[attr] = class_attrs[attr]

                if permissions:
                    view_info["permissions"] = permissions

                views[node.name] = view_info

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = [arg.arg for arg in node.args.args]
                if "request" not in args:
                    continue
                decorators = self._extract_decorators(node.decorator_list)
                permissions = self._infer_permissions([], decorators)
                view_info = {
                    "type": "function",
                    "args": args,
                    "decorators": decorators,
                    "doc": ast.get_docstring(node) or "",
                }
                if permissions:
                    view_info["permissions"] = permissions
                views[node.name] = view_info

        return views

    def _extract_base_names(self, bases: list) -> list[str]:
        """提取完整基礎類別名稱（支援 a.B 格式）"""
        names = []
        for base in bases:
            if isinstance(base, ast.Name):
                names.append(base.id)
            elif isinstance(base, ast.Attribute):
                names.append(ast.unparse(base))
            elif isinstance(base, ast.Subscript):
                names.append(ast.unparse(base))
        return names

    def _extract_decorators(self, decorator_list: list) -> list[str]:
        """提取 decorators（包含帶參數的，如 @login_required(login_url=...)）"""
        decorators = []
        for d in decorator_list:
            if isinstance(d, ast.Name):
                decorators.append(d.id)
            elif isinstance(d, ast.Call):
                if isinstance(d.func, ast.Name):
                    decorators.append(d.func.id)
                elif isinstance(d.func, ast.Attribute):
                    decorators.append(ast.unparse(d.func))
            elif isinstance(d, ast.Attribute):
                decorators.append(ast.unparse(d))
        return decorators

    def _extract_class_attributes(self, class_node: ast.ClassDef) -> dict:
        """提取類別屬性（template_name, model, queryset, fields 等）"""
        attrs: dict[str, Any] = {}
        target_attrs = [
            "template_name", "model", "queryset", "form_class",
            "success_url", "context_object_name", "fields",
            "pk_url_kwarg", "slug_url_kwarg", "paginate_by",
        ]
        for node in class_node.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in target_attrs:
                        try:
                            if isinstance(node.value, ast.Constant):
                                attrs[target.id] = node.value.value
                            elif isinstance(node.value, ast.Name):
                                attrs[target.id] = node.value.id
                            elif isinstance(node.value, ast.Attribute):
                                attrs[target.id] = ast.unparse(node.value)
                            elif isinstance(node.value, ast.List):
                                attrs[target.id] = [
                                    elt.value if isinstance(elt, ast.Constant) else ast.unparse(elt)
                                    for elt in node.value.elts
                                ]
                            else:
                                attrs[target.id] = ast.unparse(node.value)
                        except Exception:
                            attrs[target.id] = "<complex>"
        return attrs

    def _infer_permissions(self, base_names: list[str], decorators: list[str]) -> list[str]:
        """根據 Mixin 名稱和 decorators 推斷權限設定"""
        permissions: list[str] = []
        mixin_map = {
            "LoginRequiredMixin": "login_required",
            "PermissionRequiredMixin": "permission_required",
            "UserPassesTestMixin": "user_passes_test",
            "StaffRequiredMixin": "staff_required",
            "SuperuserRequiredMixin": "superuser_required",
        }
        for base in base_names:
            for mixin, perm in mixin_map.items():
                if mixin in base:
                    permissions.append(perm)
        perm_decs = ["login_required", "permission_required", "user_passes_test", "staff_member_required"]
        for dec in decorators:
            for pd in perm_decs:
                if pd in dec:
                    permissions.append(pd)
        return list(set(permissions))

    # ===== URLs 掃描（AST 靜態解析）=====

    def _scan_urls(self) -> None:
        """掃描 URL 路由（AST 靜態解析 urls.py，無需 Django resolver）"""
        print("掃描 URLs...")
        # 先掃描 config/urls.py（主路由）
        for candidate in [
            self.src_dir / "config" / "urls.py",
            self.src_dir / "urls.py",
            self.project_root / "config" / "urls.py",
        ]:
            if candidate.exists():
                self.urls_data.update(self._parse_urls_file(candidate, namespace=""))
                break

        # 掃描各 app 的 urls.py
        for app_dir in self._get_app_dirs():
            app_urls = app_dir / "urls.py"
            if not app_urls.exists():
                continue
            app_name = self._get_app_name(app_dir)
            app_url_data = self._parse_urls_file(app_urls, namespace=app_name)
            for k, v in app_url_data.items():
                if k not in self.urls_data:
                    self.urls_data[k] = v

        print(f"  ✓ 找到 {len(self.urls_data)} 個 URL patterns")

    def _parse_urls_file(self, file_path: Path, namespace: str = "") -> dict:
        """解析 urls.py，提取 path()/re_path() 定義"""
        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(file_path))
        except Exception:
            return {}

        patterns: dict[str, Any] = {}
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "urlpatterns":
                        if isinstance(node.value, ast.List):
                            for elt in node.value.elts:
                                result = self._extract_url_pattern(elt, namespace)
                                if result:
                                    patterns.update(result)
        return patterns

    def _extract_url_pattern(self, node: ast.expr, namespace: str) -> dict | None:
        """從 path() 或 re_path() AST 節點提取路由資訊"""
        if not isinstance(node, ast.Call):
            return None
        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        if func_name not in ("path", "re_path", "url"):
            return None
        if len(node.args) < 2:
            return None

        route = ""
        if isinstance(node.args[0], ast.Constant):
            route = str(node.args[0].value)
        else:
            route = ast.unparse(node.args[0])

        view_node = node.args[1]

        # 取得 URL name
        url_name = None
        for kw in node.keywords:
            if kw.arg == "name" and isinstance(kw.value, ast.Constant):
                url_name = kw.value.value

        key = (f"{namespace}:{url_name}" if namespace else url_name) if url_name else route

        # 取得 view 資訊
        view_info: dict[str, Any] = {"route": route}
        if isinstance(view_node, ast.Attribute):
            view_info["view_name"] = view_node.attr
        elif isinstance(view_node, ast.Name):
            view_info["view_name"] = view_node.id
        elif isinstance(view_node, ast.Call):
            # .as_view() 呼叫
            if (
                isinstance(view_node.func, ast.Attribute)
                and view_node.func.attr == "as_view"
                and isinstance(view_node.func.value, ast.Name)
            ):
                view_info["view_name"] = view_node.func.value.id
                view_info["view_type"] = "class"

        return {key: view_info}

    # ===== Templates 掃描 =====

    def _scan_templates(self) -> None:
        """掃描所有 Templates（url_tags/extends/includes/blocks/title）"""
        print("掃描 Templates...")
        template_dirs: list[Path] = []

        # 全域 templates/
        for td in [self.src_dir / "templates", self.project_root / "templates"]:
            if td.exists():
                template_dirs.append(td)

        # App templates/
        for app_dir in self._get_app_dirs():
            app_templates = app_dir / "templates"
            if app_templates.exists():
                template_dirs.append(app_templates)

        seen: set[Path] = set()
        for template_dir in template_dirs:
            for html_file in template_dir.rglob("*.html"):
                if html_file in seen:
                    continue
                seen.add(html_file)
                try:
                    rel_path = str(html_file.relative_to(template_dir))
                except ValueError:
                    rel_path = html_file.name
                self._scan_single_template(html_file, rel_path)

        print(f"  ✓ 找到 {len(self.templates_data)} 個模板")

    def _scan_single_template(self, file_path: Path, template_name: str) -> None:
        """掃描單一模板，提取 title/url_tags/extends/includes/blocks"""
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            return

        # 提取標題（移除 Django 模板標籤）
        title_match = re.search(r"<title>(.*?)</title>", content, re.DOTALL)
        title = title_match.group(1).strip() if title_match else ""
        title = re.sub(r"{[{%].*?[}%]}", "", title, flags=re.DOTALL).strip()

        url_tags = list(set(re.findall(r"{%\s*url\s+['\"]([^'\"]+)['\"]", content)))
        extends = re.findall(r"{%\s*extends\s+['\"]([^'\"]+)['\"]", content)
        includes = re.findall(r"{%\s*include\s+['\"]([^'\"]+)['\"]", content)
        blocks = list(set(re.findall(r"{%\s*block\s+(\w+)", content)))

        try:
            file_rel = str(file_path.relative_to(self.project_root))
        except ValueError:
            file_rel = str(file_path)

        self.templates_data[template_name] = {
            "title": title,
            "url_tags": url_tags,
            "extends": extends,
            "includes": includes,
            "blocks": blocks,
            "file_path": file_rel,
            "lines": len(content.splitlines()),
        }

    # ===== Forms 掃描（AST）=====

    def _scan_forms(self) -> None:
        """掃描所有 Forms（AST 提取 Meta class 資訊）"""
        print("掃描 Forms...")
        for app_dir in self._get_app_dirs():
            app_name = self._get_app_name(app_dir)
            forms_file = app_dir / "forms.py"
            if not forms_file.exists():
                continue
            try:
                source = forms_file.read_text(encoding="utf-8")
                tree = ast.parse(source)
            except Exception:
                continue

            app_forms: dict[str, Any] = {}
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                base_names = [
                    b.id if isinstance(b, ast.Name) else ast.unparse(b) if isinstance(b, ast.Attribute) else None
                    for b in node.bases
                ]
                if not any(b and "Form" in b for b in base_names if b):
                    continue

                meta_info: dict[str, Any] = {}
                fields_list: list[str] = []
                for child in node.body:
                    if isinstance(child, ast.ClassDef) and child.name == "Meta":
                        for item in child.body:
                            if isinstance(item, ast.Assign):
                                t = item.targets[0]
                                if isinstance(t, ast.Name):
                                    meta_info[t.id] = ast.unparse(item.value)
                    elif isinstance(child, ast.Assign):
                        for t in child.targets:
                            if isinstance(t, ast.Name) and isinstance(child.value, ast.Call):
                                field_type = ""
                                if isinstance(child.value.func, ast.Attribute):
                                    field_type = child.value.func.attr
                                elif isinstance(child.value.func, ast.Name):
                                    field_type = child.value.func.id
                                if "Field" in field_type or "Choice" in field_type:
                                    fields_list.append(t.id)

                app_forms[node.name] = {
                    "bases": [b for b in base_names if b],
                    "meta": meta_info,
                    "explicit_fields": fields_list,
                    "doc": ast.get_docstring(node) or "",
                }

            if app_forms:
                self.forms_data[app_name] = app_forms

        count = sum(len(f) for f in self.forms_data.values())
        print(f"  ✓ 找到 {count} 個 Forms")

    # ===== Imports 掃描（AST）=====

    def _scan_imports(self) -> None:
        """掃描所有 Python 檔案的 import 關係（per-module 追蹤）"""
        print("掃描 Imports...")
        for app_dir in self._get_app_dirs():
            app_name = self._get_app_name(app_dir)
            app_imports: dict[str, Any] = {}
            for py_file in app_dir.rglob("*.py"):
                if any(p in py_file.parts for p in ("migrations", "__pycache__")):
                    continue
                if "test" in py_file.name:
                    continue
                try:
                    source = py_file.read_text(encoding="utf-8")
                    tree = ast.parse(source)
                except Exception:
                    continue

                imports: list[str] = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        module = node.module or ""
                        for alias in node.names:
                            imports.append(f"{module}.{alias.name}" if module else alias.name)

                if imports:
                    rel = str(py_file.relative_to(app_dir)).replace("/", ".").replace(".py", "")
                    app_imports[rel] = {
                        "imports": sorted(set(imports)),
                        "count": len(set(imports)),
                    }

            if app_imports:
                self.imports_data[app_name] = app_imports

        count = sum(len(m) for m in self.imports_data.values())
        print(f"  ✓ 掃描 {count} 個模組")

    # ===== Static Assets 掃描 =====

    def _scan_static_assets(self) -> None:
        """掃描模板中的靜態資源引用（{% static %} 分類統計）"""
        print("掃描靜態資源...")
        assets: dict[str, dict[str, Any]] = {
            "css": {}, "js": {}, "images": {}, "fonts": {}, "other": {},
        }
        static_pattern = re.compile(r"{%\s*static\s+['\"]([^'\"]+)['\"]\s*%}")

        for template_name, template_info in self.templates_data.items():
            file_path = self.project_root / template_info.get("file_path", "")
            if not file_path.exists():
                continue
            try:
                content = file_path.read_text(encoding="utf-8")
            except Exception:
                continue

            for asset_path in static_pattern.findall(content):
                ext = Path(asset_path).suffix.lower()
                if ext in (".css", ".scss", ".sass", ".less"):
                    cat = "css"
                elif ext in (".js", ".mjs", ".ts"):
                    cat = "js"
                elif ext in (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico"):
                    cat = "images"
                elif ext in (".woff", ".woff2", ".ttf", ".eot", ".otf"):
                    cat = "fonts"
                else:
                    cat = "other"

                if asset_path not in assets[cat]:
                    assets[cat][asset_path] = {"count": 0, "used_by": []}
                assets[cat][asset_path]["count"] += 1
                if template_name not in assets[cat][asset_path]["used_by"]:
                    assets[cat][asset_path]["used_by"].append(template_name)

        total = sum(len(v) for v in assets.values())
        self.static_assets_data = {
            "assets": assets,
            "summary": {
                "total_assets": total,
                "by_category": {k: len(v) for k, v in assets.items()},
            },
        }
        print(f"  ✓ 找到 {total} 個靜態資源引用")

    # ===== Cross-references 建立 =====

    def _build_cross_references(self) -> None:
        """建立跨檔案引用關係（URL→View、Template→URL、Model references）"""
        print("建立跨檔案引用...")

        # URL → View
        url_to_view = {
            name: {"view": info.get("view_name", ""), "route": info.get("route", "")}
            for name, info in self.urls_data.items()
            if info.get("view_name")
        }

        # Template → URL（使用的 {% url '...' %}）
        template_to_url = {
            name: info["url_tags"]
            for name, info in self.templates_data.items()
            if info.get("url_tags")
        }

        # Model 被引用關係（FK/OneToOne/M2M 指向哪個 Model）
        model_references: dict[str, list[dict]] = {}
        for app_name, app_models in self.models_data.items():
            for model_name in app_models:
                full_name = f"{app_name}.{model_name}"
                refs: list[dict] = []
                for other_app, other_models in self.models_data.items():
                    for other_model, other_info in other_models.items():
                        for field_name, field_info in other_info.get("fields", {}).items():
                            related = field_info.get("related_model", "")
                            if related and (
                                model_name == related
                                or full_name == related
                                or related.endswith(f".{model_name}")
                            ):
                                refs.append({
                                    "model": f"{other_app}.{other_model}",
                                    "field": field_name,
                                })
                if refs:
                    model_references[full_name] = refs

        self.cross_references = {
            "url_to_view": url_to_view,
            "template_to_url": template_to_url,
            "model_references": model_references,
        }

    # ===== 生成入口 =====

    def generate(self) -> None:
        """生成所有快照（與 django-vibe-snapshot.SnapshotGenerator.generate() 對等）"""
        print("開始生成 Snapshot v2.1（增強獨立版）...")
        print(f"專案根目錄: {self.project_root}")
        print(f"輸出目錄:   {self.output_dir}\n")

        # 掃描各類資料
        self._scan_apps()
        self._scan_models()
        self._scan_views()
        self._scan_urls()
        self._scan_templates()
        self._scan_forms()
        self._scan_imports()
        self._scan_static_assets()
        self._build_cross_references()

        # 儲存各 snapshot 檔案
        print("\n儲存快照檔案...")
        self._write_snapshot("apps", self.apps_data)
        self._write_snapshot("models", self.models_data)
        self._write_snapshot("views", self.views_data)
        self._write_snapshot("urls", self.urls_data)
        self._write_snapshot("templates", self.templates_data)
        self._write_snapshot("forms", self.forms_data)
        self._write_snapshot("imports", self.imports_data)
        self._write_snapshot("static_assets", self.static_assets_data)
        self._write_snapshot("cross_references", self.cross_references)

        # 生成索引
        self._generate_index()
        self._print_summary()

        print(f"\n✓ Snapshot 已生成至: {self.output_dir}")

    def _generate_index(self) -> None:
        """生成 snapshot_index.json（版本、統計、apps 清單）"""
        models_count = sum(len(m) for m in self.models_data.values())
        views_count = sum(
            len(v) for app_v in self.views_data.values() for v in app_v.values()
        )
        forms_count = sum(len(f) for f in self.forms_data.values())
        imports_count = sum(len(m) for m in self.imports_data.values())
        static_count = self.static_assets_data.get("summary", {}).get("total_assets", 0)
        cross_count = sum(len(v) for v in self.cross_references.values())

        index = {
            "version": "2.1",
            "description": "Vibe Coding Snapshot for Django Project",
            "generator": "StandaloneSnapshotGenerator v2.1",
            "generated_at": datetime.now().isoformat(),
            "snapshots": {
                "apps":             {"file": "snapshot_apps.json",             "description": "Django Apps 設定",            "count": len(self.apps_data)},
                "models":           {"file": "snapshot_models.json",           "description": "Django Models 資料模型",       "count": models_count},
                "views":            {"file": "snapshot_views.json",            "description": "Django Views 視圖函式",        "count": views_count},
                "urls":             {"file": "snapshot_urls.json",             "description": "Django URLs 路由配置",         "count": len(self.urls_data)},
                "templates":        {"file": "snapshot_templates.json",        "description": "Django Templates 模板檔案",    "count": len(self.templates_data)},
                "forms":            {"file": "snapshot_forms.json",            "description": "Django Forms 表單",            "count": forms_count},
                "imports":          {"file": "snapshot_imports.json",          "description": "Python Import 依賴關係",       "count": imports_count},
                "static_assets":    {"file": "snapshot_static_assets.json",   "description": "靜態資源使用情況",              "count": static_count},
                "cross_references": {"file": "snapshot_cross_references.json","description": "跨檔案引用關係",               "count": cross_count},
            },
            "apps": list(self.apps_data.keys()),
        }

        index_file = self.output_dir / "snapshot_index.json"
        index_file.write_text(
            json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print("  ✓ snapshot_index.json")

    def _print_summary(self) -> None:
        """列印快照摘要"""
        models_count = sum(len(m) for m in self.models_data.values())
        views_count = sum(
            len(v) for app_v in self.views_data.values() for v in app_v.values()
        )
        forms_count = sum(len(f) for f in self.forms_data.values())
        static_count = self.static_assets_data.get("summary", {}).get("total_assets", 0)

        print("\n" + "=" * 60)
        print("📊 Snapshot 摘要")
        print("=" * 60)
        print(f"Apps:         {len(self.apps_data)} 個")
        print(f"Models:       {models_count} 個")
        print(f"Views:        {views_count} 個")
        print(f"URLs:         {len(self.urls_data)} 個")
        print(f"Templates:    {len(self.templates_data)} 個")
        print(f"Forms:        {forms_count} 個")
        print(f"Imports:      {sum(len(m) for m in self.imports_data.values())} 個模組")
        print(f"Static:       {static_count} 個資源")
        print("=" * 60)

    # ===== 向下相容的公開方法（保留舊介面）=====

    def find_template_files(self) -> list[Path]:
        """搜尋所有 HTML 模板檔案（向下相容）"""
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
        """掃描單一模板（向下相容，委派給 _scan_single_template）"""
        try:
            template_path.relative_to(self.project_root)
        except ValueError:
            pass
        self._scan_single_template(template_path, str(template_path.name))
        return self.templates_data.get(str(template_path.name), {})

    def scan_templates(self) -> None:
        """掃描所有模板（向下相容）"""
        self._scan_templates()

    def scan_models(self) -> None:
        """掃描 Django Models（向下相容）"""
        self._scan_models()

    def scan_views(self) -> None:
        """掃描 Django Views（向下相容）"""
        self._scan_views()

    def scan_apps(self) -> None:
        """掃描 Django Apps（向下相容）"""
        self._scan_apps()

    def save_json(self, data: dict[str, Any], filename: str) -> None:
        """儲存 JSON 檔案（向下相容）"""
        output_path = self.output_dir / filename
        output_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"  ✓ {filename}")

    def find_python_files(self, pattern: str = "*.py") -> list[Path]:
        """搜尋 Python 檔案（向下相容）"""
        python_files = []
        for py_file in self.src_dir.rglob(pattern):
            parts = py_file.parts
            if any(p in parts for p in (".venv", "__pycache__", "migrations", "node_modules")):
                continue
            python_files.append(py_file)
        return sorted(set(python_files))


def main() -> None:
    """主程式進入點"""
    parser = argparse.ArgumentParser(
        description="增強版獨立 Django 專案快照生成器 v2.1",
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

        # 偵測是否為 Django 專案
        has_manage_py = (project_root / "manage.py").exists()
        has_src_manage_py = (project_root / "src" / "manage.py").exists()
        if not (has_manage_py or has_src_manage_py):
            print("警告: 未偵測到 manage.py，可能不是 Django 專案，繼續執行掃描...")

        generator = StandaloneSnapshotGenerator(
            project_root=project_root,
            output_dir=project_root / args.output,
        )
        generator.generate()
        sys.exit(0)

    except KeyboardInterrupt:
        print("\n\n中斷執行")
        sys.exit(1)
    except Exception as e:
        print(f"錯誤: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
