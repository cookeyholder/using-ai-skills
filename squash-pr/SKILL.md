---
name: squash-pr
description: Check PR has no new review feedback, squash merge to the PR's target branch, then update that local branch.
license: MIT
compatibility: Requires GitHub CLI (gh) and git.
metadata:
  author: local
  version: "1.0"
---

Use this skill when the user wants to finalize a PR by squashing into the PR's target branch after confirming there are no new review comments, then sync the local target branch.

## Input
- Optional PR number/URL (e.g., `17` or full PR URL)
- If omitted, infer from current branch with `gh pr view`

## Workflow

1. **Resolve target PR**

```bash
gh pr view <pr> --json number,url,state,isDraft,headRefName,baseRefName,mergeStateStatus,reviews,comments,latestReviews
```

Rules:
- PR must be `OPEN`
- PR must not be draft
- save `baseRefName` as `<target-branch>`; it may be any branch

2. **Check for new review feedback**

- Inspect newest reviews/comments and identify whether there are actionable items not yet addressed.
- If any new actionable feedback exists, stop and report them.
- If there is no new actionable feedback, continue.

3. **Check merge readiness / CI**

```bash
gh pr checks <pr>
gh pr view <pr> --json mergeStateStatus,reviewDecision
```

Rules:
- Required checks should be passing.
- `mergeStateStatus` should allow merge (`CLEAN`/mergeable equivalent).
- If checks are pending/failing, stop and report.

4. **Squash merge to the target branch**

```bash
gh pr merge <pr> --squash --delete-branch
```

- If merge fails, report the exact blocker.

5. **Update local target branch**

```bash
git fetch origin --prune
git checkout <target-branch>
git pull --ff-only origin <target-branch>
```

6. **Report completion**

Return:
- PR number and URL
- merge commit SHA
- local target branch head commit
- whether branch deletion succeeded

## Guardrails
- Never merge if new actionable review feedback exists.
- Never merge if required checks are failing/pending.
- Do not use force push or destructive git commands.
- If local workspace has conflicting uncommitted changes preventing checkout to the target branch, stop and report.
