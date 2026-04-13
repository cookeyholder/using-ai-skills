---
name: review-pr-3x
description: Run review-pr three times and monitor PR checks with gh pr checks --watch.
license: MIT
compatibility: Requires GitHub CLI (gh) and the review-pr skill logic.
metadata:
  author: local
  version: "1.1"
---

Run `review-pr` three times with 10-minute intervals between runs.

**Input**: Optional PR number or URL (e.g., `review-pr-3x 19`).
If omitted, infer from current branch using the same rule as `review-pr`.

## Execution Plan

1. Resolve target PR (same logic as `review-pr`).
2. Execute 3 rounds of review/fix/check cycle.
3. Wait 10 minutes (`600s`) between rounds 1→2 and 2→3.

## Per Round (i = 1..3)

- Announce: `Round i/3 start`.
- Execute the full `review-pr` workflow for the same PR:
  - collect actionable review comments
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
- Announce: `Round i/3 done` with concise summary.

## Interval

After round 1 and round 2:

```bash
sleep 600
```

During waiting, report that the command is intentionally paused for polling interval.
If checks are still running/pending between rounds, use:

```bash
gh pr checks <pr> --watch
```

to monitor until completion before moving on.

## Completion Output

Provide a final summary including:
- total rounds executed
- commits created per round (if any)
- latest review status
- latest CI status
- conflict-file check results by round
- remaining blockers (if any)

## Guardrails
- Use the same PR for all 3 rounds.
- If no actionable feedback and CI is green in a round, still continue to next scheduled round.
- Conflict-file checks are mandatory before each round's commit/push.
- If hard-blocked (permission/network/tool outage), report immediately and stop.
