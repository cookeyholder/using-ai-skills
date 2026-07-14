## 1. P1-HIGH: POSIX Compliance & Metadata

- [x] 1.1 Replace `which rg` with `command -v rg` in `rg_exists()` using `["sh", "-c", "command -v rg"]`
- [x] 1.2 Add `disable-model-invocation: true` to SKILL.md metadata with a rationale comment

## 2. P2-MEDIUM: Error Handling Hardening

- [x] 2.1 Make `run()` print stderr to `sys.stderr` on non-zero exit before returning `""`
- [x] 2.2 Make `scan_pattern()` print stderr to `sys.stderr` when `rg` returncode is not 0 or 1

## 3. P2-MEDIUM: File Scan & Risk Pattern Fixes

- [x] 3.1 Extend `git_files()` to merge `git ls-files --others --exclude-standard` output
- [x] 3.2 Refine `secret\s*[:=]` regex with `(?<!# )` negative lookbehind to skip comment placeholders
- [x] 3.3 Add inline comment documenting `except Exception` false-positive category in `RISK_PATTERNS`

## 4. P3-LOW: Structure & Template Cleanup

- [x] 4.1 Extract OpenSpec command list into a module-level constant (e.g. `OPENSPEC_CMDS`) and reference it from both `build_report()` and `build_openspec_plan()`
- [x] 4.2 Normalize severity labels in SKILL.md: replace Chinese translations with English-only `P0_CRITICAL` / `P1_HIGH` / `P2_MEDIUM` / `P3_LOW`

## 5. SKILL.md Phase Restructuring

- [x] 5.1 Move iteration stop-conditions from the "建議" appendix into Phase 3 as new numbered steps (after existing step 9)
- [x] 5.2 Replace standalone Phase 4 section with a forward-reference paragraph in Phase 3; remove duplicated consolidation instructions
- [x] 5.3 Add test-discovery guidance in Phase 3: inspect `package.json`/`pyproject.toml`/`Cargo.toml`/`Makefile` before running tests
- [x] 5.4 Update bootstrap script invocation path in SKILL.md to use `$(dirname "$(realpath "$0")")` pattern instead of relative `review-fix/scripts/`
