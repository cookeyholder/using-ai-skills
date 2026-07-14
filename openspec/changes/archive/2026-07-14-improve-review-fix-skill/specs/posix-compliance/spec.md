## ADDED Requirements

### Requirement: Bootstrap script MUST use POSIX-compatible command detection
The `rg_exists()` function in `bootstrap_review_fix.py` SHALL use `command -v rg` instead of `which rg` for cross-platform compatibility.

#### Scenario: Detect ripgrep on Alpine
- **WHEN** the script runs on an Alpine Linux container without `/usr/bin/which`
- **THEN** `command -v rg` SHALL correctly return the path to rg

#### Scenario: Detect ripgrep on standard Linux
- **WHEN** the script runs on a standard Linux distribution
- **THEN** `command -v rg` SHALL correctly return the path to rg

#### Scenario: Graceful absence
- **WHEN** ripgrep is not installed on the system
- **THEN** `command -v rg` SHALL return non-zero, and the script SHALL skip `rg`-dependent scans

### Requirement: SKILL.md metadata SHALL document disable-model-invocation decision
The SKILL.md frontmatter SHALL include explicit documentation about whether `disable-model-invocation: true` is set and why.

#### Scenario: Decision documented
- **WHEN** a maintainer reads the SKILL.md metadata
- **THEN** the metadata SHALL state whether `disable-model-invocation` is enabled and the rationale
