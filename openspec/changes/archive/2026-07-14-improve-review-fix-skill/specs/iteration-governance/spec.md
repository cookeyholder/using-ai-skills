## ADDED Requirements

### Requirement: Stop-condition rules SHALL be part of Phase 3 main body
The iteration stop-condition (maximum 3 rounds, stop after 2 consecutive rounds with no new P0/P1) SHALL be moved from the "建議 (suggestion)" appendix into Phase 3 core logic as a numbered step.

#### Scenario: Rules integrated
- **WHEN** a maintainer reads the Phase 3 section
- **THEN** stop-conditions SHALL appear as explicit numbered steps within Phase 3

### Requirement: Phase 4 SHALL be merged into Phase 3 or replaced by a forward reference
The documentation consolidation instructions in Phase 4 duplicate Phase 3 step 8-9. The duplication SHALL be resolved either by inlining Phase 4 as sub-steps of Phase 3, or by replacing Phase 4 with a clear forward reference.

#### Scenario: Phase 4 inlined
- **WHEN** a maintainer reads the skill
- **THEN** there SHALL be exactly one canonical location for file-consolidation instructions
