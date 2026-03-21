"""
遷移進度追蹤系統 - 用於 Bootstrap 到 Tailwind 的遷移工作管理

主要功能：
1. 追蹤每個模板的遷移狀態
2. 評估遷移複雜度
3. 分析模板依賴關係
4. 檢測 Bootstrap 和 Tailwind 的衝突
5. 生成進度報告和統計
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from collections import defaultdict


class MigrationStatusTracker:
    """追蹤並管理 Bootstrap 到 Tailwind 的遷移進度"""

    # 遷移狀態定義
    STATUS_NOT_STARTED = "not_started"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_COMPLETED = "completed"

    # 複雜度級別
    COMPLEXITY_LEVELS = {
        "trivial": (1, 2),      # 非常簡單
        "simple": (3, 4),       # 簡單
        "moderate": (5, 6),     # 中等
        "complex": (7, 8),      # 複雜
        "very_complex": (9, 10)  # 非常複雜
    }

    def __init__(self, css_snapshot_path: Path, templates_snapshot_path: Path):
        """
        初始化遷移追蹤器。

        Args:
            css_snapshot_path: snapshot_css_classes.json 路徑
            templates_snapshot_path: snapshot_templates.json 路徑
        """
        self.css_snapshot_path = Path(css_snapshot_path)
        self.templates_snapshot_path = Path(templates_snapshot_path)

        # 加載快照數據
        self.css_data = self._load_json(self.css_snapshot_path)
        self.templates_data = self._load_json(self.templates_snapshot_path)

        # 初始化數據結構
        self.migration_status: Dict[str, Dict[str, Any]] = {}
        self.dependency_graph: Dict[str, List[str]] = {}
        self.complexity_scores: Dict[str, int] = {}
        self.conflicts: Dict[str, List[Dict[str, Any]]] = {}

    def _load_json(self, file_path: Path) -> Dict[str, Any]:
        """載入 JSON 快照檔案"""
        if not file_path.exists():
            raise FileNotFoundError(f"找不到快照檔案: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def calculate_complexity_score(
        self,
        template_name: str,
        css_data: Dict[str, Any]
    ) -> int:
        """
        計算模板的遷移複雜度評分（1-10）。

        評分因素：
        - Bootstrap 類名數量 (0-3 分)
        - 自訂類名數量 (0-2 分)
        - Bootstrap Icons 數量 (0-2 分)
        - 依賴深度 (0-3 分)

        Args:
            template_name: 模板名稱
            css_data: CSS 類名掃描數據

        Returns:
            int: 1-10 的複雜度評分
        """
        # 查找此模板的 CSS 數據
        bootstrap_templates = css_data.get('bootstrap_classes', {})
        custom_templates = css_data.get('custom_classes', {})
        icon_templates = css_data.get('bootstrap_icons', {})

        # 計算 Bootstrap 類名分數 (0-3)
        bootstrap_count = 0
        for category_data in bootstrap_templates.values():
            if isinstance(category_data, dict):
                for templates_list in category_data.values():
                    if isinstance(templates_list, list) and template_name in templates_list:
                        bootstrap_count += 1

        bootstrap_score = min(3, bootstrap_count // 5 + 1) if bootstrap_count > 0 else 0

        # 計算自訂類名分數 (0-2)
        custom_count = 0
        if template_name in custom_templates:
            custom_count = len(custom_templates.get(template_name, []))
        custom_score = min(2, custom_count // 50 + 1) if custom_count > 0 else 0

        # 計算 Icons 分數 (0-2)
        icon_count = 0
        for icons_list in icon_templates.values():
            if isinstance(icons_list, list) and template_name in icons_list:
                icon_count += 1
        icon_score = min(2, icon_count // 20 + 1) if icon_count > 0 else 0

        # 計算依賴深度分數 (0-3)
        dependency_score = min(3, len(self.dependency_graph.get(template_name, [])) // 3)

        score = min(10, 1 + bootstrap_score + custom_score + icon_score + dependency_score)
        return max(1, score)

    def build_dependency_graph(self) -> None:
        """
        建立模板依賴圖。

        分析 snapshot_templates.json 中的 extends 和 includes 關係，
        建立完整的依賴圖。
        """
        self.dependency_graph = defaultdict(list)

        for template_name, template_info in self.templates_data.items():
            # 處理 extends 關係
            extends = template_info.get('extends', [])
            for parent in extends:
                if parent not in self.dependency_graph[template_name]:
                    self.dependency_graph[template_name].append(parent)

            # 處理 includes 關係
            includes = template_info.get('includes', [])
            for included in includes:
                if included not in self.dependency_graph[template_name]:
                    self.dependency_graph[template_name].append(included)

    def get_dependency_depth(self, template_name: str, visited: Optional[Set[str]] = None) -> int:
        """
        計算模板的依賴深度（遞迴）。

        Args:
            template_name: 模板名稱
            visited: 已訪問的模板集合（用於避免循環）

        Returns:
            int: 依賴深度
        """
        if visited is None:
            visited = set()

        if template_name in visited:
            return 0  # 避免循環依賴

        visited.add(template_name)
        dependencies = self.dependency_graph.get(template_name, [])

        if not dependencies:
            return 0

        max_depth = 0
        for dep in dependencies:
            depth = 1 + self.get_dependency_depth(dep, visited.copy())
            max_depth = max(max_depth, depth)

        return max_depth

    def detect_conflicts(self) -> None:
        """
        檢測 Bootstrap 和 Tailwind 的衝突。

        在此階段，我們標記同時使用 Bootstrap 類名的模板，
        稍後在實際遷移時可用於檢查衝突。
        """
        self.conflicts = {}

        bootstrap_templates = self.css_data.get('bootstrap_classes', {})

        for template_name in self.templates_data.keys():
            template_conflicts = []

            # 檢查 Bootstrap 類名
            for category, category_data in bootstrap_templates.items():
                if isinstance(category_data, dict):
                    for class_name, templates_list in category_data.items():
                        if isinstance(templates_list, list) and template_name in templates_list:
                            template_conflicts.append({
                                "type": "bootstrap_class",
                                "category": category,
                                "class": class_name
                            })

            if template_conflicts:
                self.conflicts[template_name] = template_conflicts

    def initialize_migration_status(self) -> None:
        """
        初始化所有模板的遷移狀態。

        為每個模板建立遷移記錄，包括狀態、複雜度、依賴關係等。
        """
        self.migration_status = {}

        for template_name in self.templates_data.keys():
            # 計算複雜度
            complexity = self.calculate_complexity_score(template_name, self.css_data)

            self.migration_status[template_name] = {
                "template_name": template_name,
                "status": self.STATUS_NOT_STARTED,
                "complexity_score": complexity,
                "dependencies": self.dependency_graph.get(template_name, []),
                "dependency_depth": self.get_dependency_depth(template_name),
                "conflicts": self.conflicts.get(template_name, []),
                "started_at": None,
                "completed_at": None,
                "notes": "",
                "last_updated": datetime.now().isoformat()
            }

    def update_status(
        self,
        template_name: str,
        status: str,
        notes: str = "",
        user: str = "system"
    ) -> bool:
        """
        更新模板的遷移狀態。

        Args:
            template_name: 模板名稱
            status: 新狀態（not_started, in_progress, completed）
            notes: 備註
            user: 操作者

        Returns:
            bool: 更新是否成功
        """
        if template_name not in self.migration_status:
            return False

        if status not in [self.STATUS_NOT_STARTED, self.STATUS_IN_PROGRESS, self.STATUS_COMPLETED]:
            return False

        record = self.migration_status[template_name]
        record["status"] = status
        record["last_updated"] = datetime.now().isoformat()
        record["notes"] = notes

        if status == self.STATUS_IN_PROGRESS and not record["started_at"]:
            record["started_at"] = datetime.now().isoformat()

        if status == self.STATUS_COMPLETED and not record["completed_at"]:
            record["completed_at"] = datetime.now().isoformat()

        return True

    def get_statistics(self) -> Dict[str, Any]:
        """
        計算遷移進度統計。

        Returns:
            dict: 包含各種統計資訊
        """
        if not self.migration_status:
            return {}

        total = len(self.migration_status)
        not_started = sum(1 for r in self.migration_status.values() if r["status"] == self.STATUS_NOT_STARTED)
        in_progress = sum(1 for r in self.migration_status.values() if r["status"] == self.STATUS_IN_PROGRESS)
        completed = sum(1 for r in self.migration_status.values() if r["status"] == self.STATUS_COMPLETED)

        # 按複雜度統計
        complexity_stats = defaultdict(lambda: {"total": 0, "completed": 0})
        for record in self.migration_status.values():
            score = record["complexity_score"]
            level = self._score_to_level(score)
            complexity_stats[level]["total"] += 1
            if record["status"] == self.STATUS_COMPLETED:
                complexity_stats[level]["completed"] += 1

        # 計算平均複雜度
        avg_complexity = (
            sum(r["complexity_score"] for r in self.migration_status.values()) / total
            if total > 0
            else 0
        )

        return {
            "total_templates": total,
            "not_started": not_started,
            "in_progress": in_progress,
            "completed": completed,
            "completion_percentage": (completed / total * 100) if total > 0 else 0,
            "average_complexity": round(avg_complexity, 2),
            "complexity_distribution": dict(complexity_stats),
            "total_conflicts": len(self.conflicts),
            "templates_with_conflicts": sum(1 for r in self.migration_status.values() if r["conflicts"])
        }

    def get_migration_plan(self) -> List[Dict[str, Any]]:
        """
        根據依賴關係和複雜度生成遷移計畫。

        優先級規則：
        1. 先遷移無依賴的模板（base.html）
        2. 按複雜度升序（簡單先遷）
        3. 優先遷移被其他模板依賴的模板

        Returns:
            list: 建議的遷移順序
        """
        plan = []

        # 找出無依賴的模板（優先級最高）
        no_deps = []
        has_deps = []

        for template_name, record in self.migration_status.items():
            if not record["dependencies"]:
                no_deps.append(template_name)
            else:
                has_deps.append(template_name)

        # 對無依賴的模板按複雜度排序
        no_deps.sort(key=lambda t: self.migration_status[t]["complexity_score"])

        # 對有依賴的模板按複雜度排序
        has_deps.sort(key=lambda t: self.migration_status[t]["complexity_score"])

        # 組合結果
        for template_name in no_deps + has_deps:
            record = self.migration_status[template_name]
            plan.append({
                "template": template_name,
                "complexity": record["complexity_score"],
                "dependencies": record["dependencies"],
                "conflicts_count": len(record["conflicts"])
            })

        return plan

    def save_to_file(self, output_path: Path) -> None:
        """
        將遷移狀態保存到 JSON 檔案。

        Args:
            output_path: 輸出檔案路徑
        """
        output_data = {
            "generated_at": datetime.now().isoformat(),
            "migration_status": self.migration_status,
            "statistics": self.get_statistics(),
            "migration_plan": self.get_migration_plan(),
            "dependency_graph": dict(self.dependency_graph),
            "conflicts": self.conflicts
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def _score_to_level(score: int) -> str:
        """將複雜度分數轉換為級別"""
        if 1 <= score <= 2:
            return "trivial"
        elif 3 <= score <= 4:
            return "simple"
        elif 5 <= score <= 6:
            return "moderate"
        elif 7 <= score <= 8:
            return "complex"
        else:
            return "very_complex"

    def load_from_file(self, file_path: Path) -> None:
        """
        從 JSON 檔案加載遷移狀態。

        Args:
            file_path: 輸入檔案路徑
        """
        if not file_path.exists():
            raise FileNotFoundError(f"找不到狀態檔案: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.migration_status = data.get("migration_status", {})
            self.dependency_graph = data.get("dependency_graph", {})
            self.conflicts = data.get("conflicts", {})
