# 2026-04-11 refactor-django Skill Refinement Design

## 1. Goal Description
Refactor and simplify the `refactor-django/SKILL.md` file to improve readability and maintainability. The current file is too long (26KB+). The goal is to condense the core workflow while enriching it with expert-level tactical guidance on complex dependency decoupling, safe database migrations, and rollback SOPs.

## 2. Approach: Core + Expert Guide
We will reorganize the single `SKILL.md` file into two major logical sections:
1.  **Core Refactor Pipeline**: A high-density, action-oriented workflow condensed into 4 Waves.
2.  **Expert Tactical Guide**: A reference section for deep technical challenges (Dependencies, Migrations, Rollbacks).

## 3. Detailed Architecture

### 3.1 File Structure Overhaul
The file will be structured as follows:
- **Navigation Table**: Quick links to all sections.
- **Core Workflow (The "Pipeline")**: 
    - Wave 1: Analysis & Safety Net (Snapshot + Unit Tests).
    - Wave 2: Service Extraction & Model Cleanup (Implementation & Review-Fix).
    - Wave 3: Toolchain & Type Hints (Mypy + Ruff + Celery).
    - Wave 4: Consolidation & Archive (Final PRs).
- **Expert Tactical Guide**:
    - **T1: Dependency Decoupling**: Signal decoupling and circular import breakpoints.
    - **T2: Zero-Downtime Migrations**: Expand/Migrate/Contract pattern.
    - **T3: Rollback & Troubleshooting**: SOPs for deployment failure.
- **Cheat Sheet & Templates**: Concise code snippets for common tasks.

### 3.2 Simplification Strategy
- Avoid long prose; use bullet points and checklist format (`- [ ]`).
- Use Mermaid diagrams for workflow visualization.
- Move redundant explanation of Wave implementation into a unified checklist.

### 3.3 New Tactical Content
- **Migrations**: Introduce the "Expand/Migrate/Contract" pattern for model refactoring.
- **Dependencies**: Explicitly define using `services` as the only bridge between apps to avoid circular imports.
- **Rollback**: Define "Data Compensation" commands vs "Git Revert" scenarios.

## 4. Success Criteria
- File size reduced significantly (target < 15KB).
- Core workflow (Pipeline) can be read in under 2 minutes.
- Inclusion of the three new Expert Tactical topics.
- All Factory templates fixed (Indentation verified).

## 5. Verification Plan
- Manual audit of Markdown structure and internal links.
- Verify readability and actionability of the 4 Waves.
- Verify the technical correctness of the new Expert sections.
