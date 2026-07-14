## Why

The review-fix skill was self-reviewed and found 10 issues spanning P1 (2), P2 (6), and P3 (3): non-POSIX shell commands, silent error swallowing, untracked-file blind spots, overly broad risk patterns, ambiguous stop-condition placement, missing test-discovery instructions, phase overlap, fragile CWD assumptions, duplicated OpenSpec command blocks in the bootstrap script, and inconsistent severity labeling between SKILL.md and the script.

## What Changes

- Replace `which rg` with `command -v rg` in the bootstrap script for POSIX compliance
- Add `disable-model-invocation: true` to SKILL.md metadata (and document the decision if model-invocation must stay)
- Extend `git ls-files` to include `--others --exclude-standard` for untracked files
- Tighten risk patterns to reduce false positives
- Log stderr from `rg` and propagate errors instead of silently returning 0
- Surface `run()` non-zero exit via logging instead of returning empty string
- Relocate stop-condition rules into Phase 3 main body
- Add test-discovery guidance (read package.json/pyproject.toml/Cargo.toml)
- Consolidate Phase 4 into Phase 3 or link cleanly
- Add `$(dirname ...)` path resolution for bootstrap script invocation
- Deduplicate `commands` blocks in bootstrap script templates
- Normalize severity labels to English-only across SKILL.md and script
- **BREAKING**: None — all changes are internal to the skill definition

## Capabilities

### New Capabilities
- `posix-compliance`: Replace `which` with `command -v` and harden shell patterns
- `robust-error-handling`: Log stderr from subprocess calls; never silently return empty on failure
- `untracked-file-scan`: Extend file scanning to cover untracked as well as tracked files
- `risk-pattern-tuning`: Narrow regexes to reduce false-positive rate in automated scans
- `test-discovery`: Add step to auto-detect test commands from project config files
- `iteration-governance`: Move stop-condition logic into Phase 3 body; consolidate Phase 4 into Phase 3
- `path-resolution`: Resolve bootstrap script path via `codegraph which` or `dirname`
- `template-deduplication`: Extract shared command lists into a constant in bootstrap script
- `severity-normalization`: Unify severity labels to English-only across all artifacts

### Modified Capabilities

None — no existing specs to modify.

## Impact

- `/home/cookeyholder/.agents/skills/review-fix/SKILL.md` — structural edits to metadata, phases 3/4, iteration rules, test-discovery, and bootstrap invocation
- `/home/cookeyholder/.agents/skills/review-fix/scripts/bootstrap_review_fix.py` — `which` → `command -v`, error logging, `git ls-files` flags, risk pattern regexes, template `commands` deduplication
