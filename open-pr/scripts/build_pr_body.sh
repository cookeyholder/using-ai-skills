#!/usr/bin/env bash
set -euo pipefail

PR_BODY=${PR_BODY:-/tmp/pr_body.md}
BASE_BRANCH=${BASE_BRANCH:-main}
CURRENT_BRANCH=${CURRENT_BRANCH:-$(git branch --show-current)}
MODE=${1:-generate}

collect_commits() {
  git fetch origin "${BASE_BRANCH}" >/dev/null 2>&1 || true
  git log --pretty=format:'%s' -n 3 "origin/${BASE_BRANCH}..${CURRENT_BRANCH}" 2>/dev/null || git log --pretty=format:'%s' -n 3
}

collect_diff_dirs() {
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
  issue=$(echo "$branch" | grep -oE '[0-9]{2,}' || true)
  if [[ -n "$issue" ]] && command -v gh >/dev/null; then
    if gh issue view "$issue" --json title >/dev/null 2>&1; then
      gh issue view "$issue" --json title --jq '.title'
    fi
  fi
}

generate_template() {
  local commits diff_dirs keywords keyword_line issue_title
  commits=$(collect_commits)
  diff_dirs=$(collect_diff_dirs)
  keywords=$(generate_keywords "$commits")
  keyword_line=$(printf '%s' "$keywords" | paste -sd ', ' -)
  issue_title=$(generate_issue_context || true)
  mkdir -p "$(dirname "$PR_BODY")"
  local primary_dir="${diff_dirs%%$'\n'*}"
  [[ -z "${primary_dir// }" ]] && primary_dir="多個模組"
  {
    printf '## 自動產生 - 變更摘要\n'
    printf -- '- 本次 PR 參考 commit: %s\n' "${commits:-還未紀錄}"
    printf -- '- 主要變更聚焦在 %s 等模組（請依實際內容調整）\n\n' "$primary_dir"
    printf '## 自動產生 - 主要變更項目\n'
    printf -- '- Example 1：說明修改的檔案或資料流\n'
    printf -- '- Example 2：說明風險控管或邏輯調整\n'
    printf -- '- Example 3：補充文件/設定/腳本更新\n\n'
    printf '## 測試與驗證\n'
    printf -- '- [ ] 單元測試\n'
    printf -- '- [ ] 整合測試\n'
    printf -- '- [ ] 手動驗證\n'
    printf -- '- [ ] 靜態檢查（Lint/型別檢查）\n\n'
    printf '測試細節：\n'
    printf -- '- 指令：`<請填入實際執行的測試指令>`\n'
    printf -- '- 結果：`<請填入測試結果與重現方式>`\n\n'
    printf '## 風險與回滾\n'
    printf -- '- 潛在風險：<請填入>\n'
    printf -- '- 監控指標：<請填入>\n'
    printf -- '- 回滾方式：<請填入>\n\n'
    printf '## 相關議題\n'
    printf -- '- Closes #<issue-number>\n'
    printf -- '- Ref: #<issue-number>\n'
  } > "$PR_BODY"
  echo "自動推論關鍵詞：${keyword_line}"
  local title_hint
  title_hint=$(generate_title_hint "$keywords" || true)
  if [[ -n "$title_hint" ]]; then
    echo "建議標題提示：${title_hint}"
  fi
  if [[ -n "$issue_title" ]]; then
    echo "自動補充 issue 標題：${issue_title}"
  fi
}

validate_template() {
  if [[ ! -f "$PR_BODY" ]]; then
    echo "[open-pr] 找不到 ${PR_BODY}，請先用 'generate' 產生 PR 內文後再執行驗證。"
    exit 1
  fi
  local placeholders
  placeholders=$(rg -n '<請填入' "$PR_BODY" || true)
  if [[ -n "$placeholders" ]]; then
    echo "[open-pr] 發現未填寫的 placeholder："
    echo "$placeholders"
    exit 1
  fi
  if ! rg -q '指令：`[^`]+`' "$PR_BODY" || ! rg -q '結果：`[^`]+`' "$PR_BODY"; then
    echo "[open-pr] 測試細節中的指令與結果請填入完整內容。"
    exit 1
  fi
  if rg -q '\\n' "$PR_BODY" || rg -q '\\n\\n' "$PR_BODY"; then
    echo "[open-pr] PR 內文還含有字面 '\\n'，請改成實際段落。"
    exit 1
  fi
  local keywords match=false
  keywords=$(generate_keywords "$(collect_commits)")
  for kw in $keywords; do
    if rg -qi "\b$kw\b" "$PR_BODY"; then
      match=true
      break
    fi
  done
  if [[ "$match" != true ]]; then
    echo "[open-pr] 自動推論關鍵詞：$keywords"
    echo "請確認 PR 標題或摘要提到其中一個。"
    exit 1
  fi
  local untracked
  untracked=$(git ls-files --others --exclude-standard)
  if [[ -n "$untracked" ]]; then
    echo "[open-pr] 有未追蹤檔案，請納入版本控制或忽略後再發 PR。"
    echo "$untracked"
    exit 1
  fi
  local issue
  issue=$(echo "$CURRENT_BRANCH" | grep -oE '[0-9]{2,}' || true)
  if [[ -n "$issue" ]] && command -v gh >/dev/null; then
    if ! gh issue view "$issue" >/dev/null 2>&1; then
      echo "[open-pr] 未找到 issue #${issue}，請確認 branch 名稱或相關議題設定。"
      exit 1
    fi
  fi
  local checkboxes
  checkboxes=$(rg -c '^\- \[ \]' "$PR_BODY" || true)
  if (( checkboxes < 2 )); then
    echo "[open-pr] 測試與驗證至少要準備 2 項 checkbox，請補齊。"
    exit 1
  fi
  echo "[open-pr] 驗證通過：PR 內文符合規範，可繼續執行 gh pr create。"
}

case "$MODE" in
  generate)
    generate_template
    ;;
  validate)
    validate_template
    ;;
  *)
    echo "Usage: $0 [generate|validate]"
    exit 1
    ;;
esac
