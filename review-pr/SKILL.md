---
name: review-pr
description: Read PR review comments, monitor CI with gh pr checks --watch, implement fixes, and push updates.
license: MIT
compatibility: Requires GitHub CLI (gh).
metadata:
  author: local
  version: "1.6"
---

Review a Pull Request, collect actionable review feedback, monitor CI/check status with `gh pr checks --watch`, implement fixes, run lightweight `review-fix` validation, then commit and push updates.

**Input**: Optional PR number or URL (e.g., `review-pr 19`).
If omitted, infer from current branch. If ambiguous, show candidate PRs and ask user to choose.

## Pre-checks

1. **Auth check**: Verify GitHub CLI is authenticated
   ```bash
   gh auth status
   ```

## Steps

1. **Select PR**
   - If input is provided, use it directly.
   - Otherwise infer from branch:
   ```bash
   gh pr view --json number,url,title,headRefName,baseRefName,state
   ```
   - If inference fails, list open PRs and ask user to pick one.
   - **After selection**: verify PR is still open
     ```bash
     gh pr view <pr> --json state --jq .state
     ```
     If state is not `OPEN`, stop and report.
   - **Normalize to a numeric PR number** for later REST API calls (`pull_number` must be an integer, URLs are not accepted):
     ```bash
     gh pr view <pr> --json number --jq .number
     ```
     Use this value as `<pr_number>` in all `gh api` calls below. `gh pr`/`gh run` commands still accept the original input.

2. **Collect review feedback**
   ```bash
   gh pr view <pr> --json reviews,latestReviews,comments,files,headRefName,baseRefName,url
   gh api "repos/{owner}/{repo}/pulls/<pr_number>/comments" --paginate
   gh api graphql -F owner="{owner}" -F repo="{repo}" -F pr=<pr_number> -f query='
     query($owner:String!,$repo:String!,$pr:Int!) {
       repository(owner:$owner,name:$repo){ pullRequest(number:$pr){
         reviewThreads(first:100){ nodes { isResolved isOutdated
           comments(first:1){ nodes { path line body } } } } } }
     }' --jq '.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved==false and .isOutdated==false)'
   ```
   - `gh pr view --json comments` only returns general PR comments; the `gh api .../pulls/<pr_number>/comments` call captures inline (file/line) comments, but the REST endpoint does not expose thread resolution state — use the GraphQL `reviewThreads` query to exclude resolved/outdated threads before creating work items.
   Build an actionable review list:
   - Include concrete requested changes and blocking issues
   - Include inline review comments with their file/line context (from the calls above)
   - Exclude pure summaries, non-actionable praise, resolved/outdated threads, and duplicates

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

6. **Run lightweight `review-fix` validation before commit/push (mandatory)**
   - After coding fixes are done, run the `review-fix` skill in its **lightweight validation mode** (see `review-fix` 附錄 B): it reviews only the PR's changed files and runs affected tests/lint.
   - Do NOT trigger the full review-fix pipeline here: no branch creation, no OpenSpec change, no full P0-P3 report, no doc consolidation, no PR prompt.
   - If it reports actionable findings, implement the required follow-up fixes and repeat until none remain.
   - Do not commit or push before this step is complete.

7. **Commit, push, and re-verify PR**
   ```bash
   git status --porcelain
   git add <files changed by the fixes>
   git commit -m "<clear message for the fixes>"
   git push
   ```
   - Stage only the files created or modified for the actionable items; do not use `git add -A`/`git add .` (avoids committing unrelated or sensitive local changes).
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
   - Lightweight `review-fix` validation result and any extra issues it caught
   - Commits added
   - Current checks/review state
   - Remaining blockers (if any)

## Guardrails
- Do not rewrite unrelated code.
- If a review comment is unclear or conflicts with spec/requirements, pause and ask user.
- If there are no actionable review comments, still check CI and fix CI failures if present.
- If review is clean and CI is green, explicitly state no action is needed.
- Conflict-file checks are required before every commit/push in this workflow.
- Lightweight `review-fix` validation (changed-files review + affected tests/lint) is required before every commit/push in this workflow.
