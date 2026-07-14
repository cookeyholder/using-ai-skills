## ADDED Requirements

### Requirement: OpenSpec command list SHALL be defined once
The `openspec new change ...` / `openspec instructions ...` command block SHALL be defined as a single constant in `bootstrap_review_fix.py` and referenced by both `build_report()` and `build_openspec_plan()`.

#### Scenario: Command list changes
- **WHEN** a new OpenSpec command is added to the workflow
- **THEN** the maintainer SHALL edit exactly one location
