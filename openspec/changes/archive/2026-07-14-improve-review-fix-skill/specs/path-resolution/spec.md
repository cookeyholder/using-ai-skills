## ADDED Requirements

### Requirement: Bootstrap invocation SHALL resolve its own path
The bootstrap script invocation in SKILL.md SHALL use `$(codegraph which review-fix)` or `$(dirname "$(realpath "$0")")` to resolve its own directory instead of assuming `review-fix/scripts/` is relative to CWD.

#### Scenario: Run from subdirectory
- **WHEN** the user runs the bootstrap command from `repo/src/`
- **THEN** the script path SHALL resolve correctly to `<skill_root>/scripts/bootstrap_review_fix.py`
