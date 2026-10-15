---
name: review-pr-2x
description: Run review-pr twice and monitor PR checks with gh pr checks --watch.
license: MIT
compatibility: Requires GitHub CLI (gh) and the review-pr skill logic.
metadata:
  author: local
  version: "2.0"
---

Run `review-pr` twice, with one 5-minute interval between the two rounds to catch delayed review feedback.

**Input**: Optional PR number or URL (e.g., `review-pr-2x 19`).
If omitted, infer from current branch using the same rule as `review-pr`.

## Execution Plan

1. Resolve target PR (same logic as `review-pr`).
2. Execute 2 rounds of the review/fix/check cycle.
3. Between round 1 and round 2: first wait for CI to finish, then wait 5 minutes for delayed review comments.

## Per Round (i = 1..2)

- Before the round: verify PR state; if the PR is merged or closed, stop and report the final summary.
- Announce: `Round i/2 start`.
- Execute the full `review-pr` workflow for the same PR:
  - collect actionable review comments (including inline file/line comments)
  - monitor CI/check status using `gh pr checks <pr> --watch` and inspect failed logs if needed
  - implement fixes
  - check for conflicting files before commit/push:
    ```bash
    git diff --name-only --diff-filter=U
    rg -n "^(<<<<<<<|=======|>>>>>>>)" .
    ```
    - if conflicts are found, resolve all conflicting files first
  - push changes
  - re-monitor PR status with `gh pr checks <pr> --watch`
- Announce: `Round i/2 done` with concise summary.

## Interval (between round 1 and round 2)

1. First, wait for CI to complete:
   ```bash
   gh pr checks <pr> --watch
   ```
2. Then pause 5 minutes to catch delayed review comments:
   ```bash
   sleep 300
   ```

Report that the workflow is intentionally paused for the polling interval.

## Completion Output

Provide a final summary including:
- total rounds executed (and whether the run stopped early because the PR was merged/closed)
- commits created per round (if any)
- latest review status
- latest CI status
- conflict-file check results by round
- remaining blockers (if any)

## Guardrails
- Use the same PR for all rounds.
- If no actionable feedback and CI is green in a round, still continue to the next scheduled round.
- Conflict-file checks are mandatory before each round's commit/push.
- If hard-blocked (permission/network/tool outage), report immediately and stop.
