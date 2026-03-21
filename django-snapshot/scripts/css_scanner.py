"""
CSS Class Scanner for Bootstrap to Tailwind Migration

此模組提供掃描 Django 樣板中 CSS 類別的功能，用於支援 Bootstrap 到 Tailwind CSS 的遷移工作。

主要功能：
- 掃描 HTML 樣板中的 Bootstrap 類別
- 掃描 HTML 樣板中的 Tailwind CSS 類別
- 識別 Bootstrap Icons 使用
- 提取自訂 CSS 類別
- 產生分析報告用於遷移規劃
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Union, Optional


class CSSClassScanner:
    """
    掃描 HTML 樣板中的 CSS 類別。

    此類別負責：
    1. 識別 Bootstrap 類別模式
    2. 識別 Tailwind CSS 類別模式
    3. 偵測 Bootstrap Icons
    4. 提取自訂 CSS 類別
    5. 聚合掃描結果
    """

    # Bootstrap 類別模式字典
    BOOTSTRAP_CLASS_PATTERNS: dict = {
        'layout': [
            r'container(?:-fluid|-sm|-md|-lg|-xl|-xxl)?',
            r'row',
            r'col(?:-\d+)?(?:-(?:sm|md|lg|xl|xxl))?(?:-\d+)?',
            r'g(?:x|y)?-\d+',  # gutters
            r'offset-(?:sm|md|lg|xl|xxl)?-\d+',
        ],
        'spacing': [
            r'[mp][tblrxy]?-(?:auto|\d+)',  # margin, padding
        ],
        'typography': [
            r'text-(?:start|end|center|justify)',
            r'text-(?:lowercase|uppercase|capitalize)',
            r'text-(?:primary|secondary|success|danger|warning|info|light|dark|muted|white)',
            r'fw-(?:light|lighter|normal|bold|bolder)',
            r'fs-\d+',
            r'h[1-6]',
            r'display-[1-6]',
            r'lead',
            r'small',
            r'mark',
        ],
        'components': [
            r'btn(?:-(?:primary|secondary|success|danger|warning|info|light|dark|link|outline-\w+))?',
            r'btn-(?:sm|lg)',
            r'btn-group(?:-vertical)?',
            r'card(?:-(?:body|title|text|header|footer|img|img-top|img-bottom|img-overlay))?',
            r'alert(?:-(?:primary|secondary|success|danger|warning|info|light|dark))?',
            r'badge(?:-(?:primary|secondary|success|danger|warning|info|light|dark))?',
            r'nav(?:-(?:tabs|pills|fill|justified|item|link))?',
            r'navbar(?:-(?:brand|nav|toggler|collapse|expand-\w+|light|dark))?',
            r'dropdown(?:-(?:toggle|menu|item|divider))?',
            r'modal(?:-(?:dialog|content|header|body|footer|title))?',
            r'table(?:-(?:striped|bordered|hover|sm|responsive))?',
            r'form-(?:control|select|check|check-input|check-label|label|text)',
            r'input-group(?:-(?:text|prepend|append))?',
            r'pagination',
            r'page-(?:item|link)',
            r'breadcrumb(?:-item)?',
            r'list-group(?:-item)?(?:-(?:action|primary|secondary|success|danger|warning|info|light|dark))?',
            r'accordion(?:-(?:item|header|body|button|collapse))?',
            r'carousel(?:-(?:inner|item|control-prev|control-next|indicators|caption))?',
            r'progress(?:-bar)?',
            r'spinner-(?:border|grow)',
            r'toast(?:-(?:container|header|body))?',
            r'tooltip',
            r'popover',
        ],
        'utilities': [
            r'd-(?:none|inline|inline-block|block|grid|table|table-row|table-cell|flex|inline-flex)',
            r'd-(?:sm|md|lg|xl|xxl)-(?:none|inline|inline-block|block|grid|table|table-row|table-cell|flex|inline-flex)',
            r'flex-(?:row|column|row-reverse|column-reverse)',
            r'flex-(?:wrap|nowrap|wrap-reverse)',
            r'justify-content-(?:start|end|center|between|around|evenly)',
            r'align-(?:items|self|content)-(?:start|end|center|baseline|stretch)',
            r'float-(?:start|end|none)',
            r'position-(?:static|relative|absolute|fixed|sticky)',
            r'top-\d+',
            r'bottom-\d+',
            r'start-\d+',
            r'end-\d+',
            r'w-(?:\d+|auto)',
            r'h-(?:\d+|auto)',
            r'mw-\d+',
            r'mh-\d+',
            r'vw-\d+',
            r'vh-\d+',
            r'border(?:-(?:top|bottom|start|end))?(?:-\d+)?',
            r'border-(?:primary|secondary|success|danger|warning|info|light|dark|white)',
            r'rounded(?:-(?:top|bottom|start|end|circle|pill))?(?:-\d+)?',
            r'shadow(?:-(?:none|sm|lg))?',
            r'opacity-\d+',
            r'bg-(?:primary|secondary|success|danger|warning|info|light|dark|white|transparent|body)',
            r'visible',
            r'invisible',
            r'overflow-(?:auto|hidden|visible|scroll)',
        ],
        'grid': [
            r'g-\d+',
            r'gx-\d+',
            r'gy-\d+',
        ],
    }

    # Tailwind CSS 類別模式字典
    TAILWIND_CLASS_PATTERNS: dict = {
        'layout': [
            r'container',
            r'box-(?:border|content)',
            r'block',
            r'inline-block',
            r'inline',
            r'flex',
            r'inline-flex',
            r'grid',
            r'inline-grid',
            r'hidden',
            r'flow-root',
            r'contents',
            r'list-(?:item|none)',
        ],
        'flexbox_grid': [
            r'flex-(?:row|row-reverse|col|col-reverse)',
            r'flex-(?:wrap|wrap-reverse|nowrap)',
            r'flex-(?:1|auto|initial|none)',
            r'flex-grow(?:-0)?',
            r'flex-shrink(?:-0)?',
            r'grid-cols-(?:\d+|none)',
            r'grid-rows-(?:\d+|none)',
            r'col-(?:auto|span-\d+|start-\d+|end-\d+)',
            r'row-(?:auto|span-\d+|start-\d+|end-\d+)',
            r'gap-(?:x-|y-)?\d+(?:\.\d+)?',
            r'justify-(?:start|end|center|between|around|evenly)',
            r'justify-items-(?:start|end|center|stretch)',
            r'justify-self-(?:auto|start|end|center|stretch)',
            r'items-(?:start|end|center|baseline|stretch)',
            r'content-(?:start|end|center|between|around|evenly)',
            r'self-(?:auto|start|end|center|stretch|baseline)',
            r'place-(?:content|items|self)-(?:start|end|center|stretch|between|around|evenly)',
        ],
        'spacing': [
            r'[mp][tblrxy]?-(?:auto|px|\d+(?:\.\d+)?)',
            r'space-(?:x|y)-(?:reverse|\d+(?:\.\d+)?)',
        ],
        'sizing': [
            r'w-(?:auto|full|screen|min|max|fit|px|\d+(?:\/\d+)?|\[\d+(?:px|rem|em|%)\])',
            r'h-(?:auto|full|screen|min|max|fit|px|\d+(?:\/\d+)?|\[\d+(?:px|rem|em|%)\])',
            r'min-[wh]-(?:0|full|min|max|fit|px|\d+)',
            r'max-[wh]-(?:none|full|min|max|fit|screen|px|\d+)',
        ],
        'typography': [
            r'text-(?:xs|sm|base|lg|xl|2xl|3xl|4xl|5xl|6xl|7xl|8xl|9xl)',
            r'text-(?:left|center|right|justify|start|end)',
            r'text-(?:inherit|current|transparent|black|white|slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)-(?:\d+)',
            r'font-(?:sans|serif|mono)',
            r'font-(?:thin|extralight|light|normal|medium|semibold|bold|extrabold|black)',
            r'italic',
            r'not-italic',
            r'font-variant-numeric',
            r'leading-(?:none|tight|snug|normal|relaxed|loose|\d+)',
            r'tracking-(?:tighter|tight|normal|wide|wider|widest)',
            r'line-clamp-(?:none|\d+)',
            r'break-(?:normal|words|all)',
            r'truncate',
            r'text-(?:ellipsis|clip)',
            r'uppercase',
            r'lowercase',
            r'capitalize',
            r'normal-case',
            r'underline',
            r'overline',
            r'line-through',
            r'no-underline',
        ],
        'backgrounds': [
            r'bg-(?:inherit|current|transparent|black|white|slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)-(?:\d+)',
            r'bg-(?:none|gradient-to-(?:t|tr|r|br|b|bl|l|tl))',
            r'from-(?:inherit|current|transparent|black|white|slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)-(?:\d+)',
            r'via-(?:inherit|current|transparent|black|white|slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)-(?:\d+)',
            r'to-(?:inherit|current|transparent|black|white|slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)-(?:\d+)',
            r'bg-(?:fixed|local|scroll)',
            r'bg-(?:auto|cover|contain)',
            r'bg-(?:bottom|center|left|left-bottom|left-top|right|right-bottom|right-top|top)',
            r'bg-(?:repeat|no-repeat|repeat-x|repeat-y|repeat-round|repeat-space)',
        ],
        'borders': [
            r'border(?:-(?:[tblrxy]))?(?:-(?:0|2|4|8))?',
            r'border-(?:inherit|current|transparent|black|white|slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)-(?:\d+)',
            r'border-(?:solid|dashed|dotted|double|hidden|none)',
            r'rounded(?:-(?:none|sm|md|lg|xl|2xl|3xl|full))?',
            r'rounded-(?:[tblr]|[tb][lr])-(?:none|sm|md|lg|xl|2xl|3xl|full)',
            r'divide-(?:x|y)(?:-(?:0|2|4|8|reverse))?',
            r'divide-(?:inherit|current|transparent|black|white|slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)-(?:\d+)',
            r'divide-(?:solid|dashed|dotted|double|none)',
            r'outline(?:-(?:0|1|2|4|8))?',
            r'outline-(?:none|inherit|current|transparent|black|white|slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)-(?:\d+)',
            r'outline-(?:solid|dashed|dotted|double)',
            r'ring(?:-(?:0|1|2|4|8|inset))?',
            r'ring-(?:inherit|current|transparent|black|white|slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)-(?:\d+)',
            r'ring-offset-(?:0|1|2|4|8)',
        ],
        'effects': [
            r'shadow(?:-(?:sm|md|lg|xl|2xl|inner|none))?',
            r'opacity-(?:0|5|10|20|25|30|40|50|60|70|75|80|90|95|100)',
            r'mix-blend-(?:normal|multiply|screen|overlay|darken|lighten|color-dodge|color-burn|hard-light|soft-light|difference|exclusion|hue|saturation|color|luminosity)',
            r'bg-blend-(?:normal|multiply|screen|overlay|darken|lighten|color-dodge|color-burn|hard-light|soft-light|difference|exclusion|hue|saturation|color|luminosity)',
        ],
        'transitions': [
            r'transition(?:-(?:none|all|colors|opacity|shadow|transform))?',
            r'duration-(?:75|100|150|200|300|500|700|1000)',
            r'ease-(?:linear|in|out|in-out)',
            r'delay-(?:75|100|150|200|300|500|700|1000)',
            r'animate-(?:none|spin|ping|pulse|bounce)',
        ],
        'transforms': [
            r'transform(?:-(?:none|gpu|cpu))?',
            r'scale-(?:0|50|75|90|95|100|105|110|125|150)',
            r'scale-(?:x|y)-(?:0|50|75|90|95|100|105|110|125|150)',
            r'rotate-(?:0|1|2|3|6|12|45|90|180)',
            r'-?rotate-(?:1|2|3|6|12|45|90|180)',
            r'translate-(?:x|y)-(?:0|px|0\.5|1|1\.5|2|2\.5|3|3\.5|4|5|6|7|8|9|10|11|12|14|16|20|24|28|32|36|40|44|48|52|56|60|64|72|80|96)',
            r'skew-(?:x|y)-(?:0|1|2|3|6|12)',
            r'-?skew-(?:x|y)-(?:1|2|3|6|12)',
            r'origin-(?:center|top|top-right|right|bottom-right|bottom|bottom-left|left|top-left)',
        ],
        'interactivity': [
            r'cursor-(?:auto|default|pointer|wait|text|move|help|not-allowed|none|context-menu|progress|cell|crosshair|vertical-text|alias|copy|no-drop|grab|grabbing|all-scroll|col-resize|row-resize|n-resize|e-resize|s-resize|w-resize|ne-resize|nw-resize|se-resize|sw-resize|ew-resize|ns-resize|nesw-resize|nwse-resize|zoom-in|zoom-out)',
            r'pointer-events-(?:none|auto)',
            r'resize(?:-(?:none|y|x))?',
            r'select-(?:none|text|all|auto)',
            r'scroll-(?:auto|smooth)',
            r'snap-(?:none|x|y|both|mandatory|proximity|start|end|center|align-none)',
            r'touch-(?:auto|none|pan-(?:x|left|right|y|up|down)|pinch-zoom|manipulation)',
        ],
        'positioning': [
            r'(?:static|fixed|absolute|relative|sticky)',
            r'inset-(?:auto|px|0|0\.5|1|1\.5|2|2\.5|3|3\.5|4|5|6|7|8|9|10|11|12|14|16|20|24|28|32|36|40|44|48|52|56|60|64|72|80|96|full)',
            r'(?:top|right|bottom|left)-(?:auto|px|0|0\.5|1|1\.5|2|2\.5|3|3\.5|4|5|6|7|8|9|10|11|12|14|16|20|24|28|32|36|40|44|48|52|56|60|64|72|80|96|full)',
            r'z-(?:0|10|20|30|40|50|auto)',
        ],
        'visibility': [
            r'visible',
            r'invisible',
            r'collapse',
        ],
        'overflow': [
            r'overflow-(?:auto|hidden|clip|visible|scroll|x-auto|x-hidden|x-clip|x-visible|x-scroll|y-auto|y-hidden|y-clip|y-visible|y-scroll)',
            r'overscroll-(?:auto|contain|none|y-auto|y-contain|y-none|x-auto|x-contain|x-none)',
        ],
    }

    # Bootstrap Icons 模式
    BOOTSTRAP_ICON_PATTERN: str = r'bi-[\w-]+'

    # Tailwind 響應式前綴模式
    TAILWIND_RESPONSIVE_PREFIXES: list = [
        r'sm:', r'md:', r'lg:', r'xl:', r'2xl:',
    ]

    # Tailwind 狀態變體前綴模式
    TAILWIND_STATE_PREFIXES: list = [
        r'hover:', r'focus:', r'active:', r'disabled:', r'visited:',
        r'focus-within:', r'focus-visible:', r'target:', r'checked:',
        r'indeterminate:', r'placeholder-shown:', r'autofill:',
        r'read-only:', r'required:', r'valid:', r'invalid:',
        r'in-range:', r'out-of-range:', r'placeholder:',
        r'first:', r'last:', r'only:', r'odd:', r'even:',
        r'first-of-type:', r'last-of-type:', r'only-of-type:',
        r'empty:', r'disabled:', r'enabled:', r'group-hover:',
        r'peer-hover:', r'dark:', r'light:',
    ]

    def __init__(self, snapshot_json_path: Union[str, Path]) -> None:
        """
        初始化 CSS Class Scanner。

        Args:
            snapshot_json_path: snapshot_templates.json 檔案路徑
        """
        self.snapshot_path = Path(snapshot_json_path)
        self.templates_data: dict = {}
        self.scan_results: dict = {
            'bootstrap_classes': defaultdict(lambda: defaultdict(list)),
            'bootstrap_icons': defaultdict(list),
            'tailwind_classes': defaultdict(lambda: defaultdict(list)),
            'custom_classes': defaultdict(list),
            'summary': {}
        }

    def load_snapshot(self) -> None:
        """
        載入 snapshot_templates.json 檔案。

        Raises:
            FileNotFoundError: 如果 snapshot 檔案不存在
            json.JSONDecodeError: 如果 JSON 格式錯誤
        """
        if not self.snapshot_path.exists():
            raise FileNotFoundError(f"Snapshot file not found: {self.snapshot_path}")

        with self.snapshot_path.open('r', encoding='utf-8') as f:
            snapshot = json.load(f)
            # 支援兩種格式:
            # 1. 實際快照檔案: {"template_name": {...}, ...}
            # 2. 測試快照檔案: {"templates_data": {"template_name": {...}, ...}}
            if 'templates_data' in snapshot and isinstance(snapshot['templates_data'], dict):
                self.templates_data = snapshot['templates_data']
            else:
                self.templates_data = snapshot

    def _strip_tailwind_prefixes(self, css_class: str) -> str:
        """
        移除 Tailwind 響應式和狀態變體前綴。

        Args:
            css_class: CSS 類別字串

        Returns:
            str: 移除前綴後的類別
        """
        # 移除所有前綴（可能有多個，如 md:hover:bg-blue-500）
        result = css_class
        while True:
            original = result
            # 移除響應式前綴
            for prefix in self.TAILWIND_RESPONSIVE_PREFIXES:
                if result.startswith(prefix.rstrip(':')):
                    result = result[len(prefix):]
                    break
            # 移除狀態變體前綴
            for prefix in self.TAILWIND_STATE_PREFIXES:
                if result.startswith(prefix.rstrip(':')):
                    result = result[len(prefix):]
                    break
            # 如果沒有更多前綴可移除，退出循環
            if result == original:
                break
        return result

    def detect_bootstrap_classes(self, html_content: str) -> dict[str, list[str]]:
        """
        偵測 HTML 內容中的 Bootstrap 類別。

        Args:
            html_content: HTML 內容字串

        Returns:
            dict: 按類別分類的 Bootstrap 類別
                格式: {'layout': ['container', 'row'], 'components': ['btn', 'card'], ...}
        """
        detected_classes: dict = defaultdict(list)

        # 使用正則表達式提取所有 class 屬性
        class_pattern = r'class\s*=\s*["\']([^"\']+)["\']'
        matches = re.finditer(class_pattern, html_content, re.IGNORECASE)

        for match in matches:
            class_string = match.group(1)
            classes = class_string.split()

            # 對每個類別檢查是否符合 Bootstrap 模式
            for css_class in classes:
                for category, patterns in self.BOOTSTRAP_CLASS_PATTERNS.items():
                    for pattern in patterns:
                        if re.fullmatch(pattern, css_class):
                            if css_class not in detected_classes[category]:
                                detected_classes[category].append(css_class)
                            break

        return dict(detected_classes)

    def detect_tailwind_classes(self, html_content: str) -> dict[str, list[str]]:
        """
        偵測 HTML 內容中的 Tailwind CSS 類別。

        Args:
            html_content: HTML 內容字串

        Returns:
            dict: 按類別分類的 Tailwind 類別
                格式: {'layout': ['container', 'flex'], 'spacing': ['m-4', 'p-2'], ...}
        """
        detected_classes: dict = defaultdict(list)

        # 使用正則表達式提取所有 class 屬性
        class_pattern = r'class\s*=\s*["\']([^"\']+)["\']'
        matches = re.finditer(class_pattern, html_content, re.IGNORECASE)

        for match in matches:
            class_string = match.group(1)
            classes = class_string.split()

            # 對每個類別檢查是否符合 Tailwind 模式
            for css_class in classes:
                # 移除響應式和狀態變體前綴
                base_class = self._strip_tailwind_prefixes(css_class)

                # 檢查基礎類別是否符合 Tailwind 模式
                for category, patterns in self.TAILWIND_CLASS_PATTERNS.items():
                    for pattern in patterns:
                        if re.fullmatch(pattern, base_class):
                            if css_class not in detected_classes[category]:
                                detected_classes[category].append(css_class)
                            break

        return dict(detected_classes)

    def detect_bootstrap_icons(self, html_content: str) -> list[str]:
        """
        偵測 HTML 內容中的 Bootstrap Icons。

        Args:
            html_content: HTML 內容字串

        Returns:
            list: Bootstrap Icons 類別列表 (如 ['bi-heart', 'bi-star'])
        """
        icons = set()

        # 使用正則表達式提取所有 class 屬性
        class_pattern = r'class\s*=\s*["\']([^"\']+)["\']'
        matches = re.finditer(class_pattern, html_content, re.IGNORECASE)

        for match in matches:
            class_string = match.group(1)
            classes = class_string.split()

            # 檢查是否符合 Bootstrap Icons 模式
            for css_class in classes:
                if re.fullmatch(self.BOOTSTRAP_ICON_PATTERN, css_class):
                    icons.add(css_class)

        return sorted(list(icons))

    def extract_custom_classes(self, html_content: str) -> list[str]:
        """
        提取自訂 CSS 類別（非 Bootstrap 和 Tailwind 類別）。

        Args:
            html_content: HTML 內容字串

        Returns:
            list: 自訂 CSS 類別列表
        """
        custom_classes = set()

        # 使用正則表達式提取所有 class 屬性
        class_pattern = r'class\s*=\s*["\']([^"\']+)["\']'
        matches = re.finditer(class_pattern, html_content, re.IGNORECASE)

        for match in matches:
            class_string = match.group(1)
            classes = class_string.split()

            for css_class in classes:
                is_framework_class = False

                # 檢查是否為 Bootstrap 類別
                for patterns in self.BOOTSTRAP_CLASS_PATTERNS.values():
                    for pattern in patterns:
                        if re.fullmatch(pattern, css_class):
                            is_framework_class = True
                            break
                    if is_framework_class:
                        break

                # 檢查是否為 Bootstrap Icons
                if not is_framework_class and re.fullmatch(self.BOOTSTRAP_ICON_PATTERN, css_class):
                    is_framework_class = True

                # 檢查是否為 Tailwind 類別
                if not is_framework_class:
                    base_class = self._strip_tailwind_prefixes(css_class)
                    for patterns in self.TAILWIND_CLASS_PATTERNS.values():
                        for pattern in patterns:
                            if re.fullmatch(pattern, base_class):
                                is_framework_class = True
                                break
                        if is_framework_class:
                            break

                # 如果不是任何框架類別，則為自訂類別
                if not is_framework_class:
                    custom_classes.add(css_class)

        return sorted(list(custom_classes))

    def scan_template(self, template_path: str, html_content: str) -> None:
        """
        掃描單一樣板檔案。

        Args:
            template_path: 樣板檔案路徑
            html_content: HTML 內容
        """
        # 偵測 Bootstrap 類別
        bootstrap_classes = self.detect_bootstrap_classes(html_content)

        # 偵測 Tailwind 類別
        tailwind_classes = self.detect_tailwind_classes(html_content)

        # 偵測 Bootstrap Icons
        bootstrap_icons = self.detect_bootstrap_icons(html_content)

        # 提取自訂類別
        custom_classes = self.extract_custom_classes(html_content)

        # 儲存結果
        self.scan_results['bootstrap_classes'][template_path] = bootstrap_classes
        self.scan_results['tailwind_classes'][template_path] = tailwind_classes
        self.scan_results['bootstrap_icons'][template_path] = bootstrap_icons
        self.scan_results['custom_classes'][template_path] = custom_classes

    def scan_all_templates(self) -> None:
        """
        掃描 snapshot 中的所有樣板。

        此方法會：
        1. 遍歷 templates_data 中的所有樣板
        2. 對每個樣板呼叫 scan_template()
        3. 聚合結果到 scan_results
        """
        # 確保已載入快照資料
        if not self.templates_data:
            raise ValueError("請先執行 load_snapshot() 載入快照資料")

        # 遍歷所有樣板
        for template_path, template_info in self.templates_data.items():
            # 從樣板資訊中取得 HTML 內容
            # 支援兩種格式：
            # 1. html_content 欄位（測試用）
            # 2. file_path 欄位（實際快照）
            html_content = template_info.get('html_content', '')

            # 如果沒有 html_content，嘗試從 file_path 讀取
            if not html_content and 'file_path' in template_info:
                file_path = Path(template_info['file_path'])
                # 如果是相對路徑，從 snapshot 檔案的父目錄開始
                if not file_path.is_absolute():
                    # 嘗試從 src/templates/ 或相對於 snapshot 位置讀取
                    snapshot_parent = self.snapshot_path.parent.parent  # src/
                    file_path = snapshot_parent / template_info['file_path']

                try:
                    if file_path.exists():
                        with file_path.open('r', encoding='utf-8') as f:
                            html_content = f.read()
                except (OSError, UnicodeDecodeError):
                    # 如果無法讀取，跳過該樣板
                    continue

            # 掃描樣板
            if html_content:
                self.scan_template(template_path, html_content)

    def aggregate_results(self) -> dict[str, Any]:
        """
        聚合掃描結果並產生統計摘要。

        Returns:
            dict: 包含統計資訊的掃描結果
                格式: {
                    'bootstrap_classes': {...},
                    'tailwind_classes': {...},
                    'bootstrap_icons': {...},
                    'custom_classes': {...},
                    'summary': {
                        'total_templates': int,
                        'total_bootstrap_classes': int,
                        'total_tailwind_classes': int,
                        'total_icons': int,
                        'total_custom_classes': int,
                        'bootstrap_categories': {...},
                        'tailwind_categories': {...}
                    }
                }
        """
        # 統計樣板數量
        total_templates = len(self.scan_results['bootstrap_classes'])

        # 聚合 Bootstrap 類別（去重）
        all_bootstrap_classes = set()
        for classes_dict in self.scan_results['bootstrap_classes'].values():
            for classes in classes_dict.values():
                all_bootstrap_classes.update(classes)

        # 按類別統計 Bootstrap 類別
        bootstrap_categories = {}
        for category, patterns in self.BOOTSTRAP_CLASS_PATTERNS.items():
            matching_classes = set()
            for pattern_str in patterns:
                pattern = re.compile(pattern_str)
                matching_classes.update(cls for cls in all_bootstrap_classes if pattern.search(cls))
            bootstrap_categories[category] = {
                'count': len(matching_classes),
                'classes': sorted(list(matching_classes))
            }

        # 聚合 Tailwind 類別（去重）
        all_tailwind_classes = set()
        for classes_dict in self.scan_results['tailwind_classes'].values():
            for classes in classes_dict.values():
                all_tailwind_classes.update(classes)

        # 按類別統計 Tailwind 類別
        tailwind_categories = {}
        for category, patterns in self.TAILWIND_CLASS_PATTERNS.items():
            matching_classes = set()
            for pattern_str in patterns:
                pattern = re.compile(pattern_str)
                for cls in all_tailwind_classes:
                    base_cls = self._strip_tailwind_prefixes(cls)
                    if pattern.search(base_cls):
                        matching_classes.add(cls)
            tailwind_categories[category] = {
                'count': len(matching_classes),
                'classes': sorted(list(matching_classes))
            }

        # 聚合 Bootstrap Icons（去重）
        all_icons = set()
        for icons in self.scan_results['bootstrap_icons'].values():
            all_icons.update(icons)

        # 聚合自訂類別（去重）
        all_custom_classes = set()
        for classes in self.scan_results['custom_classes'].values():
            all_custom_classes.update(classes)

        # 建立摘要統計
        self.scan_results['summary'] = {
            'total_templates': total_templates,
            'total_bootstrap_classes': len(all_bootstrap_classes),
            'total_tailwind_classes': len(all_tailwind_classes),
            'total_icons': len(all_icons),
            'total_custom_classes': len(all_custom_classes),
            'bootstrap_categories': bootstrap_categories,
            'tailwind_categories': tailwind_categories,
        }

        return self.scan_results

    def save_results(self, output_path: Union[str, Path]) -> None:
        """
        將掃描結果儲存為 JSON 檔案。

        Args:
            output_path: 輸出檔案路徑（預設: snapshot_css_classes.json）
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open('w', encoding='utf-8') as f:
            json.dump(self.scan_results, f, indent=2, ensure_ascii=False)

    def run(self, output_path: Optional[Union[str, Path]] = None) -> dict:
        """
        執行完整的掃描流程。

        Args:
            output_path: 輸出檔案路徑（可選）

        Returns:
            dict: 掃描結果
        """
        self.load_snapshot()
        self.scan_all_templates()
        results = self.aggregate_results()

        if output_path:
            self.save_results(output_path)

        return results


def main() -> None:
    """CLI 主程式進入點。"""
    import argparse

    parser = argparse.ArgumentParser(
        description='掃描 Django Vibe Snapshot 中的 CSS 類別使用情況（支援 Bootstrap 和 Tailwind CSS）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例：
  # 使用預設路徑掃描並輸出結果
  python css_scanner.py

  # 指定快照檔案和輸出路徑
  python css_scanner.py -s /path/to/snapshot.json -o results.json

  # 只顯示結果不儲存
  python css_scanner.py --no-save
        """
    )

    parser.add_argument(
        '-s', '--snapshot',
        type=str,
        default='snapshot.json',
        help='快照檔案路徑（預設: snapshot.json）'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        default='snapshot_css_classes.json',
        help='輸出檔案路徑（預設: snapshot_css_classes.json）'
    )

    parser.add_argument(
        '--no-save',
        action='store_true',
        help='只顯示結果，不儲存到檔案'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='顯示詳細資訊'
    )

    args = parser.parse_args()

    try:
        # 建立掃描器實例
        scanner = CSSClassScanner(snapshot_json_path=args.snapshot)

        # 執行掃描
        print(f"正在掃描快照檔案: {args.snapshot}")
        output_path = None if args.no_save else args.output
        results = scanner.run(output_path=output_path)

        # 顯示摘要
        summary = results.get('summary', {})
        print("\n" + "=" * 80)
        print("掃描結果摘要")
        print("=" * 80)
        print(f"掃描樣板數量:          {summary.get('total_templates', 0)}")
        print(f"Bootstrap 類別總數:    {summary.get('total_bootstrap_classes', 0)}")
        print(f"Tailwind CSS 類別總數: {summary.get('total_tailwind_classes', 0)}")
        print(f"Bootstrap Icons 總數:  {summary.get('total_icons', 0)}")
        print(f"自訂類別總數:          {summary.get('total_custom_classes', 0)}")

        # 顯示 Bootstrap 類別分類統計
        bootstrap_categories = summary.get('bootstrap_categories', {})
        if bootstrap_categories:
            print("\n" + "-" * 80)
            print("Bootstrap 類別分類統計:")
            print("-" * 80)
            for category, data in sorted(bootstrap_categories.items()):
                count = data.get('count', 0)
                print(f"  {category:20s} {count:4d} 個類別")

        # 顯示 Tailwind 類別分類統計
        tailwind_categories = summary.get('tailwind_categories', {})
        if tailwind_categories:
            print("\n" + "-" * 80)
            print("Tailwind CSS 類別分類統計:")
            print("-" * 80)
            for category, data in sorted(tailwind_categories.items()):
                count = data.get('count', 0)
                print(f"  {category:20s} {count:4d} 個類別")

        # 詳細資訊
        if args.verbose:
            print("\n" + "=" * 80)
            print("詳細資訊")
            print("=" * 80)

            # Bootstrap 詳細資訊
            if bootstrap_categories:
                print("\nBootstrap 類別:")
                for category, data in sorted(bootstrap_categories.items()):
                    classes = data.get('classes', [])
                    if classes:
                        print(f"\n  {category}:")
                        for cls in classes[:10]:  # 只顯示前 10 個
                            print(f"    - {cls}")
                        if len(classes) > 10:
                            print(f"    ... 還有 {len(classes) - 10} 個")

            # Tailwind 詳細資訊
            if tailwind_categories:
                print("\nTailwind CSS 類別:")
                for category, data in sorted(tailwind_categories.items()):
                    classes = data.get('classes', [])
                    if classes:
                        print(f"\n  {category}:")
                        for cls in classes[:10]:  # 只顯示前 10 個
                            print(f"    - {cls}")
                        if len(classes) > 10:
                            print(f"    ... 還有 {len(classes) - 10} 個")

        # 儲存提示
        print("\n" + "=" * 80)
        if not args.no_save:
            print(f"結果已儲存到: {args.output}")
        else:
            print("（未儲存結果到檔案）")
        print("=" * 80)

    except FileNotFoundError as e:
        print(f"錯誤: 找不到檔案 - {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"錯誤: JSON 格式錯誤 - {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"錯誤: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
