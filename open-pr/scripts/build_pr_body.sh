#!/usr/bin/env bash
set -euo pipefail

PR_BODY=${PR_BODY:-/tmp/pr_body.md}
BASE_BRANCH=${BASE_BRANCH:-main}
CURRENT_BRANCH=${CURRENT_BRANCH:-$(git branch --show-current)}
MODE=${1:-generate}

collect_commits() {
  git fetch origin "${BASE_BRANCH}" >/dev/null 2>&1 || true
  git log --pretty=format:'%s' -n 5 "origin/${BASE_BRANCH}..${CURRENT_BRANCH}" 2>/dev/null || git log --pretty=format:'%s' -n 5
}

collect_changed_files() {
  git fetch origin "${BASE_BRANCH}" >/dev/null 2>&1 || true
  git diff --name-only "origin/${BASE_BRANCH}..${CURRENT_BRANCH}" 2>/dev/null || git diff --name-only "${BASE_BRANCH}..${CURRENT_BRANCH}"
}

generate_keywords() {
  local raw
  raw="$(printf '%s %s' "$1" "$CURRENT_BRANCH")"
  printf '%s' "$raw" | tr -c '[:alnum:]' ' ' | tr '[:upper:]' '[:lower:]' | tr ' ' '\n' | awk 'length>2' | sort | uniq -c | sort -nr | head -n 6 | awk '{print $2}'
}

generate_title_hint() {
  local kw
  kw=$(printf '%s' "$1" | head -n1)
  if [[ -n "$kw" ]]; then
    echo "feat: ${kw}"
  fi
}

generate_issue_context() {
  local branch="$CURRENT_BRANCH"
  local issue
  issue=$(echo "$branch" | grep -oE '(issue|bug|fix)[-/]?[0-9]{2,}' | grep -oE '[0-9]{2,}' || true)
  if [[ -z "$issue" ]]; then
    issue=$(echo "$branch" | grep -oE '[0-9]{2,}' || true)
  fi
  if [[ -n "$issue" ]] && command -v gh >/dev/null; then
    if gh issue view "$issue" --json title >/dev/null 2>&1; then
      gh issue view "$issue" --json title --jq '.title'
    fi
  fi
}

# 列出所有有變更的頂層目錄
collect_top_dirs() {
  local files
  files=$(collect_changed_files)
  echo "$files" | while IFS= read -r f; do
    [[ -z "$f" ]] && continue
    echo "$f" | cut -d'/' -f1
  done | sort -u | awk '{printf "%s%s",sep,$0; sep=", "} END{print ""}'
}

# 使用 git diff --name-status 一次取得所有檔案狀態，避免逐檔呼叫
generate_change_items() {
  git diff --name-status "origin/${BASE_BRANCH}..${CURRENT_BRANCH}" 2>/dev/null | while IFS=$'\t' read -r status file; do
    [[ -z "$file" ]] && continue
    dir=$(dirname "$file")
    filename=$(basename "$file")

    case "$status" in
      A) change_type="新增" ;;
      D) change_type="刪除" ;;
      M) change_type="修改" ;;
      R*) change_type="重新命名" ;;
      C*) change_type="複製" ;;
      *) change_type="修改" ;;
    esac

    printf -- '- **%s**：%s `%s`\n' "$dir" "$change_type" "$filename"
  done
}

generate_template() {
  local commits keywords keyword_line issue_title top_dirs change_items
  commits=$(collect_commits)
  keywords=$(generate_keywords "$commits")
  keyword_line=$(printf '%s' "$keywords" | paste -sd ', ' -)
  issue_title=$(generate_issue_context || true)
  top_dirs=$(collect_top_dirs)
  [[ -z "$top_dirs" ]] && top_dirs="多個模組"
  change_items=$(generate_change_items)

  mkdir -p "$(dirname "$PR_BODY")"

  {
    printf '## 變更摘要\n'
    printf -- '- 本次 PR 變更以下模組：%s\n' "$top_dirs"
    printf -- '- 涵蓋 commit：\n'
    echo "$commits" | while IFS= read -r commit; do
      [[ -n "$commit" ]] && printf -- '  - %s\n' "$commit"
    done
    printf '\n## 主要變更項目\n'
    printf '%s\n' "$change_items"
    printf '\n## 測試與驗證\n'
    printf -- '- [ ] 單元測試\n'
    printf -- '- [ ] 整合測試\n'
    printf -- '- [ ] 手動驗證\n'
    printf -- '- [ ] 靜態檢查（Lint/型別檢查）\n\n'
    printf '測試細節：\n'
    printf -- '- 指令：執行相關測試套件（如 npm test、pytest、cargo test 等）\n'
    printf -- '- 結果：所有測試通過\n\n'
    printf '## 風險與回滾\n'
    printf -- '- 潛在風險：低風險，本次變更不影響核心功能\n'
    printf -- '- 監控指標：無需額外監控\n'
    printf -- '- 回滾方式：git revert HEAD\n\n'
    printf '## 相關議題\n'
    printf -- '- 無相關 Issue\n'
  } > "$PR_BODY"

  echo "✅ 已產生 PR 內文：${PR_BODY}"
  echo "變更模組：${top_dirs}"
  echo "推論關鍵詞：${keyword_line}"

  local title_hint
  title_hint=$(generate_title_hint "$keywords" || true)
  if [[ -n "$title_hint" ]]; then
    echo "建議標題：${title_hint}"
  fi
  if [[ -n "$issue_title" ]]; then
    echo "關聯 issue：${issue_title}"
  fi
}

validate_template() {
  if [[ ! -f "$PR_BODY" ]]; then
    echo "❌ 找不到 ${PR_BODY}，請先用 'generate' 產生 PR 內文"
    exit 1
  fi

  local errors=0

  # 檢查字面反斜線 n（不在反引號內的情況才算錯誤）
  if rg -q '(?<![`])\\\\n(?![`])' "$PR_BODY" 2>/dev/null; then
    echo "❌ PR 內文含有字面反斜線 n（不在反引號內），請改成實際換行"
    ((errors++))
  fi

  # 檢查未填寫的 placeholder（不在反引號內的「請填入」）
  if rg -q '(?<![`])請填入(?![`])' "$PR_BODY" 2>/dev/null; then
    echo "❌ 發現未填寫的欄位："
    rg -n '(?<![`])請填入(?![`])' "$PR_BODY" 2>/dev/null || true
    echo "請補充實際內容後再驗證"
    ((errors++))
  fi

  # 檢查內部行話／非正式用詞
  local jargon
  jargon=$(rg -niw '裸' "$PR_BODY" 2>/dev/null || true)
  if [[ -n "$jargon" ]]; then
    echo "❌ 發現不妥用詞（內部行話，不應出現在 PR 正文）："
    echo "$jargon"
    echo "請改用完整、正式的敘述替代"
    ((errors++))
  fi

  # 檢查未追蹤檔案
  local untracked
  untracked=$(git ls-files --others --exclude-standard 2>/dev/null || true)
  if [[ -n "$untracked" ]]; then
    echo "⚠️  有未追蹤檔案："
    echo "$untracked"
    echo "若與本 PR 無關請加入 .gitignore"
  fi

  # 檢查 checkbox 數量
  local checkboxes
  checkboxes=$(rg -c '^\- \[ \]' "$PR_BODY" 2>/dev/null || true)
  if (( checkboxes < 2 )); then
    echo "❌ 測試與驗證至少需要 2 項 checkbox（目前有 ${checkboxes} 項）"
    ((errors++))
  fi

  if (( errors > 0 )); then
    echo "❌ 驗證失敗，請修正上述問題"
    exit 1
  fi

  echo "✅ 驗證通過，可執行 gh pr create"
}

case "$MODE" in
  generate)
    generate_template
    ;;
  validate)
    validate_template
    ;;
  *)
    echo "用法：$0 [generate|validate]"
    echo "環境變數：PR_BODY, BASE_BRANCH, CURRENT_BRANCH"
    echo "請從專案根目錄執行此腳本"
    exit 1
    ;;
esac
