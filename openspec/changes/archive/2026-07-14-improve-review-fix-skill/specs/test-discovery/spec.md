## ADDED Requirements

### Requirement: Review-fix SHALL auto-discover test commands
Before running tests, the skill SHALL inspect `package.json`, `pyproject.toml`, `Cargo.toml`, and `Makefile` at the project root to determine the correct test command.

#### Scenario: npm project
- **WHEN** the project contains `package.json` with a `"test"` script
- **THEN** `npm test` SHALL be used as the test command

#### Scenario: Python project
- **WHEN** the project contains `pyproject.toml` with `[tool.pytest]`
- **THEN** `pytest` SHALL be used as the test command

#### Scenario: Rust project
- **WHEN** the project contains `Cargo.toml`
- **THEN** `cargo test` SHALL be used as the test command

#### Scenario: Makefile
- **WHEN** the project contains `Makefile` with a `test` target
- **THEN** `make test` SHALL be used as the test command
