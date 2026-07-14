## ADDED Requirements

### Requirement: git_files() SHALL include untracked files
The `git_files()` function SHALL return both tracked files AND untracked non-ignored files by appending `git ls-files --others --exclude-standard` output to `git ls-files` output.

#### Scenario: Untracked files exist
- **WHEN** the repo has untracked `.py` files that are not gitignored
- **THEN** those files SHALL be included in the returned list

#### Scenario: No untracked files
- **WHEN** all files in the repo are tracked
- **THEN** the function SHALL return the same list as `git ls-files` alone
