---
name: review-pr
description: Read PR review comments, monitor CI with gh pr checks --watch, implement fixes, and push updates.
license: MIT
compatibility: Requires GitHub CLI (gh).
metadata:
  author: local
  version: "1.2"
---

Review a Pull Request, collect actionable review feedback, monitor CI/check status with `gh pr checks --watch`, implement fixes, run `review-fix` validation, then commit and push updates.

**Input**: Optional PR number or URL (e.g., `review-pr 19`).
If omitted, infer from current branch. If ambiguous, show candidate PRs and ask user to choose.

## Steps

1. **Select PR**
   - If input is provided, use it directly.
   - Otherwise infer from branch:
   ```bash
   gh pr view --json number,url,title,headRefName,baseRefName,state
   ```
   - If inference fails, list open PRs and ask user to pick one.

2. **Collect review feedback**
   ```bash
   gh pr view <pr> --json reviews,latestReviews,comments,files,headRefName,baseRefName,url
   ```
   Build an actionable review list:
   - Include concrete requested changes and blocking issues
   - Exclude pure summaries, non-actionable praise, and duplicate threads
   - Keep file/line context when available

3. **Monitor CI status and failures**
   ```bash
   gh pr checks <pr> --watch
   gh run list --limit 10 --json databaseId,headBranch,status,conclusion,workflowName,createdAt
   ```
   - Determine if any required checks are failing/pending.
   - For failed checks, find the latest run and inspect failing job logs:
   ```bash
   gh run view <run_id> --json jobs
   gh run view <run_id> --job <job_id> --log-failed
   ```
   - Convert CI failures into actionable fix items.

4. **Plan and implement fixes**
   Resolve both sources of work:
   - Review comment items
   - CI failure items

   For each actionable item:
   - Edit only necessary files
   - Keep changes minimal and aligned with PR scope
   - Run relevant checks/tests for touched areas

5. **Check for conflicting files before commit/push (mandatory)**
   Run both checks:
   ```bash
   git diff --name-only --diff-filter=U
   rg -n "^(<<<<<<<|=======|>>>>>>>)" .
   ```
   - If either command reports conflicts, stop and resolve all conflicting files first.
   - Do not run commit/push until conflict output is empty.

6. **Run `review-fix` before commit/push (mandatory)**
   - After coding fixes are done, run one `review-fix` pass on the updated workspace.
   - If `review-fix` finds additional issues, implement the required follow-up fixes first.
   - Repeat until there are no unresolved actionable findings from this validation pass.
   - Do not commit or push before this step is complete.

7. **Commit, push, and re-verify PR**
   ```bash
   git add -A
   git commit -m "<clear message for the fixes>"
   git push
   ```
   Then verify:
   ```bash
   gh pr checks <pr> --watch
   gh pr view <pr> --json reviewDecision,mergeStateStatus
   ```
   - If checks fail again, continue log-driven fixes until green or blocked.

8. **Report outcome**
   Summarize:
   - Which review items were fixed
   - Which CI failures were fixed
   - Conflict-file check result
   - `review-fix` validation result and any extra issues it caught
   - Commits added
   - Current checks/review state
   - Remaining blockers (if any)

## Guardrails
- Do not rewrite unrelated code.
- If a review comment is unclear or conflicts with spec/requirements, pause and ask user.
- If there are no actionable review comments, still check CI and fix CI failures if present.
- If review is clean and CI is green, explicitly state no action is needed.
- Conflict-file checks are required before every commit/push in this workflow.
- `review-fix` validation is required before every commit/push in this workflow.
