## ADDED Requirements

### Requirement: Severity labels SHALL be English-only in SKILL.md
The severity level names in SKILL.md (currently a mix of English `P0_CRITICAL`/`P1_HIGH` etc. and Chinese translations) SHALL be unified to English-only labels in the canonical format. Chinese translations MAY appear in parentheses for readability.

#### Scenario: Labels consistent
- **WHEN** a maintainer reads the severity definitions in SKILL.md
- **THEN** the primary label SHALL match the format used by `build_report()` (`P0_CRITICAL`, `P1_HIGH`, `P2_MEDIUM`, `P3_LOW`)
