## ADDED Requirements

### Requirement: run() SHALL log stderr on non-zero exit
The `run()` function in `bootstrap_review_fix.py` SHALL print stderr to `sys.stderr` when a subprocess returns a non-zero exit code, instead of silently returning an empty string.

#### Scenario: Command not found
- **WHEN** a git command fails because git is not in PATH
- **THEN** the script SHALL write the stderr to `sys.stderr` and return empty string

#### Scenario: Command succeeds
- **WHEN** a command exits with code 0
- **THEN** the function SHALL behave identically to current behavior (return stdout)

### Requirement: scan_pattern() SHALL log rg errors instead of silently returning zero
When `rg` exits with a return code outside {0, 1} (e.g., out-of-memory, regex syntax error), the `scan_pattern()` function SHALL log the stderr content before returning `(0, [])`.

#### Scenario: rg crashes
- **WHEN** `rg` exits with code 2 due to a regex error or memory exhaustion
- **THEN** the function SHALL write the stderr to `sys.stderr` and return `(0, [])`
