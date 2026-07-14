## ADDED Requirements

### Requirement: Risk patterns SHALL exclude obvious non-secrets
Regex patterns in `RISK_PATTERNS` SHALL be scoped to reduce false positives on comment placeholders and test fixtures.

#### Scenario: Comment placeholder not flagged
- **WHEN** a file contains `# secret: this is a placeholder` in a comment
- **THEN** the `secret\s*[:=]` pattern SHALL NOT match (consider negative lookbehind for `# ` prefix)

#### Scenario: Test fixture API key not flagged
- **WHEN** a test fixture contains `api_key = "test123"` or `api_key=test`
- **THEN** the pattern SHOULD either exclude test directories or be refined to reduce noise

### Requirement: except Exception pattern SHALL exclude re-raise patterns
The `except\s+Exception\b` pattern SHALL be prefixed with a comment noting that `except Exception as e: ...; raise` is intentionally excluded.

#### Scenario: Valid re-raise not counted
- **WHEN** a file has `except Exception as e: log.error(...); raise`
- **THEN** the automated report SHALL document this as a known false-positive category
