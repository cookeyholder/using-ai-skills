## Context

The review-fix skill (`review-fix/SKILL.md` and `review-fix/scripts/bootstrap_review_fix.py`) underwent a self-review that identified 10 issues. All changes are internal to the skill's own definition files — no external APIs or user-facing behavior changes. The fixes span two files: SKILL.md (structural/template docs) and bootstrap_review_fix.py (Python bootstrap utility).

## Goals / Non-Goals

**Goals:**
- Eliminate all P1-HIGH issues (POSIX compliance, metadata documentation)
- Fix all P2-MEDIUM issues (error handling, file coverage, pattern precision, governance, test discovery)
- Resolve P3-LOW structural issues (phase overlap, path resolution, template dedup, severity consistency)

**Non-Goals:**
- No new features or capabilities beyond the existing skill definition
- No changes to external behavior or user-facing contract
- No changes to the subagent orchestration logic or explorer/worker templates
- No changes to the overall review-fix process flow — only targeted fixes to the existing implementation

## Decisions

1. **`command -v` over `shutil.which`**: While Python 3.x provides `shutil.which()`, the script is intentionally dependency-light. `command -v` is POSIX-standard and avoids an import. Decision: use `command -v rg`.

2. **Error logging pattern**: `run()` and `scan_pattern()` will both write to `sys.stderr` using `print(msg, file=sys.stderr)`. This keeps the script dependency-free while providing diagnostic output.

3. **Risk pattern refinement**: Use negative lookbehind `(?<!# )` for `secret\s*[:=]` to exclude comment lines. Add a `--glob '!tests/**'` exclusion for test directory noise. Keep `except Exception` as a signal but add inline documentation about false positives.

4. **Phase restructuring**: Move stop-conditions inline into Phase 3 as new step 10-11. Replace standalone Phase 4 with a short forward-reference paragraph in Phase 3 pointing to the consolidation sub-steps already present.

5. **Path resolution**: The skill path can be resolved via `$(dirname "$(realpath "$0")")` in shell or through `codegraph which`. Use a note explaining both options since not all environments have `codegraph` CLI.

## Risks / Trade-offs

- [Risk] Refined risk patterns may miss some real secrets embedded in test fixtures → Mitigation: note in report that test files are excluded and should be reviewed separately
- [Risk] `command -v` is a shell builtin, so calling it via `subprocess.run(["command", "-v", "rg"])` may behave differently than a shell-invoked `command -v` → Mitigation: use `["sh", "-c", "command -v rg"]` to ensure it runs in a proper shell context
- [Risk] Adding untracked files may slow down the scan on repos with many build artifacts → Mitigation: `--exclude-standard` respects `.gitignore`, so build outputs are excluded
- [Risk] Phase restructuring could confuse users familiar with the old layout → Mitigation: keep the section numbering additive; don't renumber existing steps, just append new ones

## Open Questions

- None — all decisions are scoped to self-contained changes.
