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

collect_diff_stats() {
  git fetch origin "${BASE_BRANCH}" >/dev/null 2>&1 || true
  git diff --stat "origin/${BASE_BRANCH}..${CURRENT_BRANCH}" 2>/dev/null || git diff --stat "${BASE_BRANCH}..${CURRENT_BRANCH}"
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

# Find primary module by counting changed lines per directory
find_primary_module() {
  local diff_stats
  diff_stats=$(collect_diff_stats)
  
  # Extract directory and line changes from diff --stat
  # Format: " filename | 10 +++---"
  echo "$diff_stats" | grep -E '^\s' | sed 's/^[[:space:]]*//' | while IFS='|' read -r file rest; do
    file=$(echo "$file" | sed 's/[[:space:]]*$//')
    dir=$(dirname "$file")
    # Get the net change count (additions + deletions)
    changes=$(echo "$rest" | grep -oE '[0-9]+[[:space:]]*\+' | grep -oE '[0-9]+' || echo "1")
    echo "$changes $dir"
  done | awk '
    { 
      count[$2] += $1 
    } 
    END { 
      for (d in count) print count[d], d 
    }
  ' | sort -nr | head -n1 | awk '{print $2}'
}

# Generate file change descriptions from diff
generate_change_items() {
  local files file dir
  files=$(collect_changed_files)
  
  echo "$files" | while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    dir=$(dirname "$file")
    filename=$(basename "$file")
    
    # Determine change type from diff
    local change_type="修改"
    if git diff "origin/${BASE_BRANCH}..${CURRENT_BRANCH}" -- "$file" 2>/dev/null | head -5 | grep -q '^+[^+]' && \
       ! git diff "origin/${BASE_BRANCH}..${CURRENT_BRANCH}" -- "$file" 2>/dev/null | grep -q '^-[^-]'; then
      change_type="新增"
    elif git diff "origin/${BASE_BRANCH}..${CURRENT_BRANCH}" -- "$file" 2>/dev/null | grep -q '^-[^-]' && \
         ! git diff "origin/${BASE_BRANCH}..${CURRENT_BRANCH}" -- "$file" 2>/dev/null | grep -q '^+[^+]'; then
      change_type="刪除"
    fi
    
    printf -- '- **%s**：%s `%s`\n' "$dir" "$change_type" "$filename"
  done
}

generate_template() {
  local commits keywords keyword_line issue_title primary_module change_items
  commits=$(collect_commits)
  keywords=$(generate_keywords "$commits")
  keyword_line=$(printf '%s' "$keywords" | paste -sd ', ' -)
  issue_title=$(generate_issue_context || true)
  primary_module=$(find_primary_module || echo "多個模組")
  change_items=$(generate_change_items)
  
  mkdir -p "$(dirname "$PR_BODY")"

  {
    printf '## 變更摘要\n'
    printf -- '- 本次 PR 主要變更 %s 相關內容\n' "$primary_module"
    printf -- '- 涵蓋以下 commit：\n'
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
    printf -- '- 指令：`請填入實際執行的測試指令`\n'
    printf -- '- 結果：`請填入測試結果與重現方式`\n\n'
    printf '## 風險與回滾\n'
    printf -- '- 潛在風險：請填入\n'
    printf -- '- 監控指標：請填入\n'
    printf -- '- 回滾方式：git revert HEAD 或手動回復 branch\n\n'
    printf '## 相關議題\n'
    printf -- '- 無相關 Issue\n'
  } > "$PR_BODY"
  
  echo "✅ 已產生 PR 內文：${PR_BODY}"
  echo "自動推論關鍵詞：${keyword_line}"
  
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
  
  # Check for literal \n (not actual newlines)
  if rg -q '\\n' "$PR_BODY" 2>/dev/null; then
    echo "❌ PR 內文含有字面反斜線 n，請改成實際換行"
    ((errors++))
  fi
  
  # Check for empty sections (just "請填入" without backticks)
  if rg -q '(?<!`)請填入(?!`)' "$PR_BODY" 2>/dev/null; then
    echo "⚠️  發現未填寫的欄位（不含反引號標記的「請填入」）："
    rg -n '(?<!`)請填入(?!`)' "$PR_BODY" 2>/dev/null || true
    echo "若為選填項目可忽略；若為必填請補上"
  fi
  
  # Check for untracked files
  local untracked
  untracked=$(git ls-files --others --exclude-standard 2>/dev/null || true)
  if [[ -n "$untracked" ]]; then
    echo "⚠️  有未追蹤檔案："
    echo "$untracked"
    echo "若與本 PR 無關請加入 .gitignore"
  fi
  
  # Check checkboxes
  local checkboxes
  checkboxes=$(rg -c '^\- \[ \]' "$PR_BODY" 2>/dev/null || true)
  if (( checkboxes < 2 )); then
    echo "⚠️  測試與驗證至少需要 2 項 checkbox（目前有 ${checkboxes} 項）"
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
    exit 1
    ;;
esac
