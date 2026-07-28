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

# 解析 git diff 產出語意化的變更描述
# 支援 Markdown 章節標題、Shell 函式名稱、一般 hunk context
generate_change_items() {
  git diff --no-renames --name-status "origin/${BASE_BRANCH}..${CURRENT_BRANCH}" 2>/dev/null | while IFS=$'\t' read -r status file; do
    [[ -z "$file" ]] && continue

    local add_lines=0 del_lines=0

    case "$status" in
      A)
        add_lines=$(wc -l < "$file" 2>/dev/null | tr -d ' ' || echo 0)
        printf -- '- **%s**：新增檔案（%d 行）\n' "$file" "$add_lines"
        continue
        ;;
      D)
        printf -- '- **%s**：刪除檔案\n' "$file"
        continue
        ;;
    esac

    [[ "$status" != "M" ]] && continue

    # 取得 diff 內容並計算增刪行數
    local diff_output
    diff_output=$(git diff "origin/${BASE_BRANCH}..${CURRENT_BRANCH}" -- "$file" 2>/dev/null || true)
    add_lines=$(echo "$diff_output" | grep '^+' | grep -v '^+++' | wc -l | tr -d ' ')
    del_lines=$(echo "$diff_output" | grep '^-' | grep -v '^---' | wc -l | tr -d ' ')

    # 依檔案類型產出語意化描述
    local desc="" ext="${file##*.}"

    case "$ext" in
      md|MD)
        local added removed parts_add parts_del
        added=$(echo "$diff_output" | grep '^+##' | sed 's/^+##*\s*//' | head -3 || true)
        removed=$(echo "$diff_output" | grep '^-##' | sed 's/^-##*\s*//' | head -3 || true)
        parts_del=(); parts_add=()
        while IFS= read -r s; do [[ -n "$s" ]] && parts_del+=("移除「$s」"); done <<< "$removed"
        while IFS= read -r s; do [[ -n "$s" ]] && parts_add+=("新增「$s」"); done <<< "$added"
        if [[ ${#parts_del[@]} -gt 0 || ${#parts_add[@]} -gt 0 ]]; then
          local all_parts=("${parts_del[@]}" "${parts_add[@]}")
          local IFS='、'
          desc="${all_parts[*]}"
        fi
        ;;
      sh)
        local funcs
        funcs=$(echo "$diff_output" | grep '^+' | grep -oE '\b[a-zA-Z_][a-zA-Z0-9_]*\s*\(\)' | sed 's/\s*()//' | head -3 || true)
        if [[ -n "$funcs" ]]; then
          local IFS='、'
          # shellcheck disable=SC2089
          desc="函式 $(echo "$funcs" | paste -sd '、') 調整"
        fi
        ;;
      py)
        local funcs
        funcs=$(echo "$diff_output" | grep '^+' | grep -oE '^\+[[:space:]]*(async\s+)?def\s+[a-zA-Z_][a-zA-Z0-9_]*' | sed 's/^+//' | sed 's/async //' | sed 's/def //' | head -3 || true)
        if [[ -n "$funcs" ]]; then
          desc="函式 $(echo "$funcs" | paste -sd '、') 調整"
        fi
        ;;
      ts|tsx|js|jsx)
        local funcs
        funcs=$(echo "$diff_output" | grep '^+' | grep -oE '(export\s+)?(async\s+)?(function|const)\s+[a-zA-Z_][a-zA-Z0-9_]*' | sed 's/^+//' | grep -oE '[a-zA-Z_][a-zA-Z0-9_]*$' | head -3 || true)
        if [[ -n "$funcs" ]]; then
          desc="函式 $(echo "$funcs" | paste -sd '、') 調整"
        fi
        ;;
    esac

    # 無特定語意時，回退到 diff hunk context
    if [[ -z "$desc" ]]; then
      local ctx
      ctx=$(echo "$diff_output" | grep '^@@' | sed 's/^@@[^@]*@@\s*//' | head -1 | grep -v '^$' || true)
      if [[ -n "$ctx" ]]; then
        desc=$(echo "$ctx" | sed 's/^\.//' | sed 's/[[:space:]]*$//' | head -c 80)
      fi
    fi

    [[ -z "$desc" ]] && desc="內容調整"
    printf -- '- **%s**：%s（+%d/-%d 行）\n' "$file" "$desc" "$add_lines" "$del_lines"
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
