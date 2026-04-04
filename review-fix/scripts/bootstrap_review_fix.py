#!/usr/bin/env python3
"""Bootstrap a review-fix run by generating report and OpenSpec plan templates.

This script is intentionally lightweight so it can run in most repos without
extra dependencies. It collects repository context and quick risk signals.
"""

from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import subprocess
import sys
from collections import Counter
from typing import Iterable, List, Tuple

RISK_PATTERNS = [
    (
        "疑似硬編碼機密字串",
        r"(AKIA[0-9A-Z]{16}|api[_-]?key\s*[:=]|secret\s*[:=]|password\s*[:=])",
    ),
    ("可能的 SQL 字串插值風險", r"SELECT\s+.+\{.+\}|f\"SELECT\s"),
    ("JS eval / Function 建構子風險", r"\beval\s*\(|new\s+Function\s*\("),
    ("Python subprocess 使用 shell=True", r"subprocess\.(run|Popen)\(.+shell\s*=\s*True"),
    (
        "過於寬鬆的例外處理",
        r"except\s+Exception\b|catch\s*\(\s*e\s*\)\s*\{",
    ),
]


def run(cmd: List[str], cwd: pathlib.Path) -> str:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def git_files(repo: pathlib.Path) -> List[pathlib.Path]:
    out = run(["git", "ls-files"], repo)
    if not out:
        return []
    return [repo / line for line in out.splitlines() if line.strip()]


def count_extensions(files: Iterable[pathlib.Path]) -> List[Tuple[str, int]]:
    counter: Counter[str] = Counter()
    for f in files:
        suffix = f.suffix.lower() or "<no_ext>"
        counter[suffix] += 1
    return sorted(counter.items(), key=lambda x: (-x[1], x[0]))[:15]


def rg_exists() -> bool:
    return (
        subprocess.run(["which", "rg"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
        == 0
    )


def scan_pattern(repo: pathlib.Path, pattern: str) -> Tuple[int, List[str]]:
    if not rg_exists():
        return 0, []
    proc = subprocess.run(
        [
            "rg",
            "-n",
            "-S",
            "--hidden",
            "--glob",
            "!.git",
            "--max-count",
            "20",
            pattern,
            ".",
        ],
        cwd=str(repo),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if proc.returncode not in (0, 1):
        return 0, []
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    return len(lines), lines[:5]


def build_report(
    repo: pathlib.Path,
    branch: str,
    head: str,
    ext_counts: List[Tuple[str, int]],
    risk_findings: List[Tuple[str, int, List[str]]],
    change_name: str,
) -> str:
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    ext_lines = "\n".join([f"- `{ext}`: {count}" for ext, count in ext_counts]) or "- (No tracked files found)"

    risk_table = [
        "| 風險訊號 | 命中數 | 範例 |",
        "|---|---:|---|",
    ]
    for signal, count, samples in risk_findings:
        sample = "<br>".join(s.replace("|", "\\|") for s in samples) if samples else "-"
        risk_table.append(f"| {signal} | {count} | {sample} |")

    openspec_cmds = [
        f"openspec new change \"{change_name}\"",
        f"openspec instructions proposal --change \"{change_name}\"",
        f"openspec instructions design --change \"{change_name}\"",
        f"openspec instructions tasks --change \"{change_name}\"",
    ]

    return f"""# 程式碼審查報告

> 語言規範：本報告必須使用「臺灣慣用語」的繁體中文撰寫（避免簡體中文與中國慣用詞）。

## 基本資訊
- 產生時間：{now}
- 專案路徑：`{repo}`
- 分支：`{branch or 'unknown'}`
- 版本：`{head or 'unknown'}`
- 建議的 OpenSpec change：`{change_name}`

## 範圍快照
### 主要副檔名分布
{ext_lines}

### 自動化風險訊號（快速掃描）
{'\n'.join(risk_table)}

## 審查發現

### P0_CRITICAL
- （填入致命等級問題）

### P1_HIGH
- （填入高優先問題）

### P2_MEDIUM
- （填入中優先問題）

### P3_LOW
- （填入低優先問題）

## 修復規劃
- （將每個問題對應到具體檔案或模組）
- （定義驗收標準與測試範圍）

## 待確認事項
- （列出需要進一步確認的假設與不確定點）

## OpenSpec 指令清單
```bash
{"\n".join(openspec_cmds)}
```
"""


def build_openspec_plan(change_name: str) -> str:
    return f"""# OpenSpec Review-Fix Plan

## Change
- Name: `{change_name}`

## Commands
```bash
openspec new change \"{change_name}\"
openspec instructions proposal --change \"{change_name}\"
openspec instructions design --change \"{change_name}\"
openspec instructions tasks --change \"{change_name}\"
```

## Completion Gate
- [ ] `docs/CODE_REVIEW_REPORT.md` has prioritized P0-P3 findings.
- [ ] Tasks include tests for every behavior change.
- [ ] Proposed risk mitigations are explicitly mapped to findings.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap review-fix artifacts")
    parser.add_argument("--repo", default=".", help="Path to target repository")
    parser.add_argument(
        "--report-out",
        default="docs/CODE_REVIEW_REPORT.md",
        help="Where to write the review report template",
    )
    parser.add_argument(
        "--plan-out",
        default="docs/OPENSPEC_REVIEW_FIX_PLAN.md",
        help="Where to write the OpenSpec helper plan",
    )
    parser.add_argument(
        "--change-name",
        default="comprehensive-code-review-fixes",
        help="OpenSpec change name suggestion",
    )
    parser.add_argument(
        "--print-only",
        action="store_true",
        help="Print report content to stdout without writing files",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = pathlib.Path(args.repo).resolve()

    if not (repo / ".git").exists():
        print(f"[error] {repo} is not a git repository", file=sys.stderr)
        return 2

    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo)
    head = run(["git", "rev-parse", "--short", "HEAD"], repo)

    files = git_files(repo)
    ext_counts = count_extensions(files)

    risk_findings = []
    for signal, pattern in RISK_PATTERNS:
        count, samples = scan_pattern(repo, pattern)
        risk_findings.append((signal, count, samples))

    report = build_report(repo, branch, head, ext_counts, risk_findings, args.change_name)
    plan = build_openspec_plan(args.change_name)

    if args.print_only:
        print(report)
        return 0

    report_out = repo / args.report_out
    plan_out = repo / args.plan_out
    report_out.parent.mkdir(parents=True, exist_ok=True)
    plan_out.parent.mkdir(parents=True, exist_ok=True)

    report_out.write_text(report, encoding="utf-8")
    plan_out.write_text(plan, encoding="utf-8")

    print(f"[ok] Wrote report template: {report_out}")
    print(f"[ok] Wrote OpenSpec plan: {plan_out}")
    print("[next] Fill findings, then run OpenSpec commands from the generated checklist.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
