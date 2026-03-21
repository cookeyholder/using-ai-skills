---
name: file-organizer
description: Intelligently organizes your files and folders across your computer by understanding context, finding duplicates, suggesting better structures, and automating cleanup tasks. Reduces cognitive load and keeps your digital workspace tidy without manual effort.
---

# File Organizer

This skill acts as your personal organization assistant, helping you maintain a clean, logical file structure across your computer without the mental overhead of constant manual organization.

## When to Use This Skill

- Your Downloads folder is a chaotic mess
- You can't find files because they're scattered everywhere
- You have duplicate files taking up space
- Your folder structure doesn't make sense anymore
- You want to establish better organization habits
- You're starting a new project and need a good structure
- You're cleaning up before archiving old projects
- **AI agents have created scattered report files across your project root** (散落的 agent 報告文件)
- You need to consolidate useful information from temporary reports

## What This Skill Does

1. **Analyzes Current Structure**: Reviews your folders and files to understand what you have
2. **Finds Duplicates**: Identifies duplicate files across your system
3. **Suggests Organization**: Proposes logical folder structures based on your content
4. **Automates Cleanup**: Moves, renames, and organizes files with your approval
5. **Maintains Context**: Makes smart decisions based on file types, dates, and content
6. **Reduces Clutter**: Identifies old files you probably don't need anymore
7. **Consolidates Agent Reports**: Identifies scattered AI-generated report files, extracts useful content, merges into existing documentation, and removes redundant files

## How to Use

### From Your Home Directory

```
cd ~
```

Then run Claude Code and ask for help:

```
Help me organize my Downloads folder
```

```
Find duplicate files in my Documents folder
```

```
Review my project directories and suggest improvements
```

### Specific Organization Tasks

```
Organize these downloads into proper folders based on what they are
```

```
Find duplicate files and help me decide which to keep
```

```
Clean up old files I haven't touched in 6+ months
```

```
Create a better folder structure for my [work/projects/photos/etc]
```

```
Find and consolidate scattered agent report files in my project root
```

```
Clean up AI-generated reports and merge useful info into existing docs
```

## Instructions

When a user requests file organization help:

1. **Understand the Scope**
   
   Ask clarifying questions:
   - Which directory needs organization? (Downloads, Documents, entire home folder?)
   - What's the main problem? (Can't find things, duplicates, too messy, no structure?)
   - Any files or folders to avoid? (Current projects, sensitive data?)
   - How aggressively to organize? (Conservative vs. comprehensive cleanup)

2. **Analyze Current State**
   
   Review the target directory:
   ```bash
   # Get overview of current structure
   ls -la [target_directory]
   
   # Check file types and sizes
   find [target_directory] -type f -exec file {} \; | head -20
   
   # Identify largest files
   du -sh [target_directory]/* | sort -rh | head -20
   
   # Count file types
   find [target_directory] -type f | sed 's/.*\.//' | sort | uniq -c | sort -rn
   ```
   
   Summarize findings:
   - Total files and folders
   - File type breakdown
   - Size distribution
   - Date ranges
   - Obvious organization issues

3. **Identify Organization Patterns**
   
   Based on the files, determine logical groupings:
   
   **By Type**:
   - Documents (PDFs, DOCX, TXT)
   - Images (JPG, PNG, SVG)
   - Videos (MP4, MOV)
   - Archives (ZIP, TAR, DMG)
   - Code/Projects (directories with code)
   - Spreadsheets (XLSX, CSV)
   - Presentations (PPTX, KEY)
   
   **By Purpose**:
   - Work vs. Personal
   - Active vs. Archive
   - Project-specific
   - Reference materials
   - Temporary/scratch files
   
   **By Date**:
   - Current year/month
   - Previous years
   - Very old (archive candidates)

4. **Find Duplicates**
   
   When requested, search for duplicates:
   ```bash
   # Find exact duplicates by hash
   find [directory] -type f -exec md5 {} \; | sort | uniq -d
   
   # Find files with same name
   find [directory] -type f -printf '%f\n' | sort | uniq -d
   
   # Find similar-sized files
   find [directory] -type f -printf '%s %p\n' | sort -n
   ```
   
   For each set of duplicates:
   - Show all file paths
   - Display sizes and modification dates
   - Recommend which to keep (usually newest or best-named)
   - **Important**: Always ask for confirmation before deleting

5. **Propose Organization Plan**
   
   Present a clear plan before making changes:
   
   ```markdown
   # Organization Plan for [Directory]
   
   ## Current State
   - X files across Y folders
   - [Size] total
   - File types: [breakdown]
   - Issues: [list problems]
   
   ## Proposed Structure
   
   ```
   [Directory]/
   ├── Work/
   │   ├── Projects/
   │   ├── Documents/
   │   └── Archive/
   ├── Personal/
   │   ├── Photos/
   │   ├── Documents/
   │   └── Media/
   └── Downloads/
       ├── To-Sort/
       └── Archive/
   ```
   
   ## Changes I'll Make
   
   1. **Create new folders**: [list]
   2. **Move files**:
      - X PDFs → Work/Documents/
      - Y images → Personal/Photos/
      - Z old files → Archive/
   3. **Rename files**: [any renaming patterns]
   4. **Delete**: [duplicates or trash files]
   
   ## Files Needing Your Decision
   
   - [List any files you're unsure about]
   
   Ready to proceed? (yes/no/modify)
   ```

6. **Execute Organization**
   
   After approval, organize systematically:
   
   ```bash
   # Create folder structure
   mkdir -p "path/to/new/folders"
   
   # Move files with clear logging
   mv "old/path/file.pdf" "new/path/file.pdf"
   
   # Rename files with consistent patterns
   # Example: "YYYY-MM-DD - Description.ext"
   ```
   
   **Important Rules**:
   - Always confirm before deleting anything
   - Log all moves for potential undo
   - Preserve original modification dates
   - Handle filename conflicts gracefully
   - Stop and ask if you encounter unexpected situations

7. **Provide Summary and Maintenance Tips**
   
   After organizing:
   
   ```markdown
   # Organization Complete! ✨
   
   ## What Changed
   
   - Created [X] new folders
   - Organized [Y] files
   - Freed [Z] GB by removing duplicates
   - Archived [W] old files
   
   ## New Structure
   
   [Show the new folder tree]
   
   ## Maintenance Tips
   
   To keep this organized:
   
   1. **Weekly**: Sort new downloads
   2. **Monthly**: Review and archive completed projects
   3. **Quarterly**: Check for new duplicates
   4. **Yearly**: Archive old files
   
   ## Quick Commands for You
   
   ```bash
   # Find files modified this week
   find . -type f -mtime -7
   
   # Sort downloads by type
   [custom command for their setup]
   
   # Find duplicates
   [custom command]
   ```
   
   Want to organize another folder?
   ```

8. **Consolidate Agent Reports** (整併 Agent 報告)
   
   When user requests cleanup of AI-generated reports:
   
   **Step 1: Identify Report Files**
   
   ```bash
   # Search for common agent report patterns in project root
   ls -la *.md | grep -E '(REPORT|REVIEW|SUMMARY|ANALYSIS|AUDIT|GUIDE|_TEST)'
   
   # Look for specific patterns:
   # - All caps with underscores: CODE_REVIEW_REPORT.md
   # - Descriptive suffixes: SECURITY_AUDIT_REPORT.md
   # - Test/guide suffixes: GOACCESS_TEST.md
   ```
   
   Common patterns for agent-generated reports:
   - `*_REPORT.md`, `*_REVIEW.md`, `*_SUMMARY.md`
   - `*_AUDIT*.md`, `*_ANALYSIS.md`, `*_GUIDE.md`
   - `*_TEST.md`, `*_IMPLEMENTATION*.md`
   - Uppercase filenames with underscores
   - Files with timestamps in names
   
   **Step 2: Analyze Each Report**
   
   For each identified report:
   ```bash
   # Read the report
   cat REPORT_NAME.md
   
   # Check file metadata
   stat REPORT_NAME.md
   ```
   
   Determine:
   - **Purpose**: What was this report documenting?
   - **Useful content**: Are there findings, decisions, or configurations worth keeping?
   - **Redundancy**: Does this overlap with existing documentation?
   - **Merge target**: Where should useful content go? (`docs/`, `README.md`, `CHANGELOG.md`, etc.)
   
   **Step 3: Present Consolidation Plan**
   
   ```markdown
   # 🗂️ Agent Report Consolidation Plan
   
   ## Found Reports (在專案根目錄找到的報告)
   
   1. `CODE_REVIEW_REPORT.md` (45 KB, 2025-12-15)
      - **Purpose**: Security and code quality review
      - **Useful content**: 12 security findings, 8 code quality issues
      - **Action**: Extract findings → merge into `docs/security/audit-log.md`
      - **Then**: Delete original
   
   2. `DESIGN_SYSTEM_COMPLIANCE_REPORT.md` (23 KB, 2025-11-20)
      - **Purpose**: Design system audit
      - **Useful content**: Component compliance checklist
      - **Action**: Extract checklist → merge into `docs/design-system/compliance.md`
      - **Then**: Delete original
   
   3. `GOACCESS_TEST.md` (8 KB, 2025-10-05)
      - **Purpose**: Testing notes for GoAccess setup
      - **Useful content**: Configuration examples
      - **Action**: Merge into `docs/goaccess-setup-guide.md`
      - **Then**: Delete original
   
   4. `SECURITY_AUDIT_REVIEW.md` (67 KB, 2025-12-01)
      - **Purpose**: Detailed security audit
      - **Useful content**: Remediation plan, OWASP findings
      - **Action**: Keep important sections → move to `docs/security/`
      - **Then**: Delete original from root
   
   5. `OPENOBSERVE_INTEGRATION_SUMMARY.md` (12 KB, 2025-11-15)
      - **Useful content**: Integration steps, configuration
      - **Action**: Merge into `docs/monitoring-implementation-summary.md`
      - **Then**: Delete original
   
   ## Files to Delete (Redundant/Outdated)
   
   - `SECURITY_IMPLEMENTATION_REVIEW.md` - Duplicates info in security docs
   - `test_hours_cleanup.py` - One-time script, no longer needed
   
   ## Summary
   
   - **Total reports found**: 5
   - **Will consolidate**: 5 files
   - **Will move to docs/**: 1 file
   - **Will delete**: 6 files
   - **Estimated cleanup**: ~180 KB freed in root directory
   
   Ready to proceed? (yes/no/modify)
   ```
   
   **Step 4: Execute Consolidation**
   
   After approval:
   
   ```bash
   # Example: Extract useful content from report
   # Read and identify sections to keep
   
   # Append to target document
   echo "\n## Findings from $(date '+%Y-%m-%d') Audit\n" >> docs/security/audit-log.md
   sed -n '/## Security Findings/,/## End/p' CODE_REVIEW_REPORT.md >> docs/security/audit-log.md
   
   # Move file to archive if needed
   mkdir -p docs/archive/agent-reports/
   mv REPORT_NAME.md docs/archive/agent-reports/
   
   # Or delete after confirmation
   rm REPORT_NAME.md
   ```
   
   **Important Rules**:
   - **Always show what content will be extracted** before merging
   - **Never delete reports without showing the consolidation plan**
   - **Preserve timestamps** in merged content (add "From report dated YYYY-MM-DD")
   - **Create target documents** if they don't exist
   - **Keep a backup** in `docs/archive/agent-reports/` if user is unsure
   - **Update CHANGELOG.md** with consolidation actions
   
   **Step 5: Verification and Summary**
   
   ```markdown
   # ✅ Agent Reports Consolidated
   
   ## Actions Completed
   
   1. ✓ Merged security findings from `CODE_REVIEW_REPORT.md` → `docs/security/audit-log.md`
   2. ✓ Integrated design compliance → `docs/design-system/compliance.md`
   3. ✓ Consolidated GoAccess notes → `docs/goaccess-setup-guide.md`
   4. ✓ Moved security audit → `docs/security/security-audit-2025-12.md`
   5. ✓ Merged monitoring summary → `docs/monitoring-implementation-summary.md`
   6. ✓ Deleted 6 redundant files from root
   
   ## Project Root Now Cleaner
   
   Before: 15 markdown files in root (many reports)
   After: 9 markdown files in root (only essential)
   
   ## Where to Find Information Now
   
   - Security findings: `docs/security/`
   - Design system: `docs/design-system/`
   - Monitoring setup: `docs/monitoring-*.md`
   - Archived reports: `docs/archive/agent-reports/` (if kept)
   
   ## Maintenance
   
   To prevent future clutter:
   - Ask agents to save reports in `docs/` or subdirectories
   - Review root directory monthly
   - Move completed reports to `docs/archive/`
   
   Want to set up a cleanup automation? I can help create a script.
   ```

## Examples

### Example 1: Organizing Downloads (From Justin Dielmann)

**User**: "My Downloads folder is a mess with 500+ files. Help me organize it."

**Process**:
1. Analyzes Downloads folder
2. Finds patterns: work docs, personal photos, installers, random PDFs
3. Proposes structure:
   - Downloads/
     - Work/
     - Personal/
     - Installers/ (DMG, PKG files)
     - Archive/
     - ToSort/ (things needing decisions)
4. Asks for confirmation
5. Moves files intelligently based on content and names
6. Results: 500 files → 5 organized folders

### Example 2: Finding and Removing Duplicates

**User**: "Find duplicate files in my Documents and help me decide which to keep."

**Output**:
```markdown
# Found 23 Sets of Duplicates (156 MB total)

## Duplicate Set 1: "proposal.pdf"
- `/Documents/proposal.pdf` (2.3 MB, modified: 2024-03-15)
- `/Documents/old/proposal.pdf` (2.3 MB, modified: 2024-03-15)
- `/Desktop/proposal.pdf` (2.3 MB, modified: 2024-03-10)

**Recommendation**: Keep `/Documents/proposal.pdf` (most recent in correct location)
Delete the other 2 copies?

[Continue for all duplicates...]
```

### Example 3: Restructuring Projects Folder

**User**: "Review my ~/Projects directory and suggest improvements."

**Output**:
```markdown
# Analysis of ~/Projects

## Current Structure Issues
- Mix of active and archived projects (3+ years old)
- No consistent naming convention
- Some projects at root, others in random subfolders
- Duplicate folders (project-name, project-name-old, project-name-v2)

## Proposed Structure

```
Projects/
├── Active/
│   ├── client-work/
│   ├── side-projects/
│   └── learning/
├── Archive/
│   ├── 2022/
│   ├── 2023/
│   └── 2024/
└── Templates/
```

## Specific Changes
1. Move 12 projects not touched since 2022 → Archive/
2. Consolidate 4 duplicate project folders
3. Rename projects to consistent format: "client-name-project-name"
4. Create Archive for old work

Want me to implement this?
```

### Example 4: Organizing Photos by Date

**User**: "Organize my photo folders by year and month."

**Output**: Creates structure like:
```
Photos/
├── 2023/
│   ├── 01-January/
│   ├── 02-February/
│   └── ...
├── 2024/
│   ├── 01-January/
│   └── ...
└── Unsorted/
```

Then moves photos based on EXIF data or file modification dates.

### Example 5: Consolidating Agent Reports (整併 Agent 報告)

**User**: "我的專案根目錄有很多 agent 留下的報告文件很混亂，幫我整理一下。"

**Analysis Output**:
```markdown
# 發現 7 個 Agent 產生的報告檔案

## 在根目錄的報告:

1. `CODE_REVIEW_REPORT.md` (45 KB)
   - 內容: 安全性和程式碼品質審查
   - 有用資訊: 12 個安全問題、8 個品質改進建議
   - 建議: 整併到 `docs/security/audit-log.md`

2. `SECURITY_AUDIT_REPORT.md` (67 KB)
   - 內容: OWASP 安全稽核
   - 有用資訊: 風險評估、修復計畫
   - 建議: 移至 `docs/security/` 並重命名為 `security-audit-2025-12.md`

3. `GOACCESS_TEST.md` (8 KB)
   - 內容: GoAccess 測試筆記
   - 有用資訊: 設定範例
   - 建議: 整併到 `docs/goaccess-setup-guide.md`

4. `OPENOBSERVE_INTEGRATION_SUMMARY.md` (12 KB)
   - 內容: 監控系統整合筆記
   - 有用資訊: 整合步驟
   - 建議: 整併到 `docs/monitoring-implementation-summary.md`

5. `DESIGN_SYSTEM_COMPLIANCE_REPORT.md` (23 KB)
   - 內容: 設計系統合規檢查
   - 有用資訊: 元件檢查清單
   - 建議: 整併到 `docs/design-system/compliance.md`

6. `SECURITY_IMPLEMENTATION_REVIEW.md` (34 KB)
   - 內容: 安全實作審查
   - 狀態: 與其他安全文件重複
   - 建議: 刪除（已有更新版本）

7. `test_hours_cleanup.py` (2 KB)
   - 內容: 一次性清理腳本
   - 建議: 移至 `scripts/archive/` 或刪除

## 整併計畫

**將執行:**
- 提取 5 份報告中的有用內容
- 整併到 docs/ 中的對應文件
- 移動 1 份完整報告到 docs/security/
- 刪除 2 份冗餘檔案
- 清理根目錄，只保留必要的專案文件

**預期結果:**
- 根目錄減少 7 個檔案
- 資訊整併到適當位置
- 釋放約 191 KB 空間
- 專案結構更清晰

是否繼續？(yes/no)
```

**After Execution**:
```markdown
✅ 整併完成！

已完成:
- ✓ 安全審查結果 → docs/security/audit-log.md
- ✓ GoAccess 設定 → docs/goaccess-setup-guide.md  
- ✓ 監控整合筆記 → docs/monitoring-implementation-summary.md
- ✓ 設計合規檢查 → docs/design-system/compliance.md
- ✓ 完整安全稽核 → docs/security/security-audit-2025-12.md
- ✓ 刪除 2 個冗餘檔案

專案根目錄現在更整潔了！
所有重要資訊都已妥善保存在 docs/ 中。
```

## Common Organization Tasks

### Downloads Cleanup
```
Organize my Downloads folder - move documents to Documents, 
images to Pictures, keep installers separate, and archive files 
older than 3 months.
```

### Project Organization
```
Review my Projects folder structure and help me separate active 
projects from old ones I should archive.
```

### Duplicate Removal
```
Find all duplicate files in my Documents folder and help me 
decide which ones to keep.
```

### Desktop Cleanup
```
My Desktop is covered in files. Help me organize everything into 
my Documents folder properly.
```

### Photo Organization
```
Organize all photos in this folder by date (year/month) based 
on when they were taken.
```

### Work/Personal Separation
```
Help me separate my work files from personal files across my 
Documents folder.
```

### Agent Report Consolidation (整併 Agent 報告)
```
Find scattered AI-generated report files in my project root and 
consolidate useful information into proper documentation.
```

```
Clean up agent reports - merge important findings into existing 
docs and remove redundant files.
```

```
我的專案根目錄有很多 agent 報告很亂，幫我整理並整併有用的內容。
```

## Pro Tips

1. **Start Small**: Begin with one messy folder (like Downloads) to build trust
2. **Regular Maintenance**: Run weekly cleanup on Downloads
3. **Consistent Naming**: Use "YYYY-MM-DD - Description" format for important files
4. **Archive Aggressively**: Move old projects to Archive instead of deleting
5. **Keep Active Separate**: Maintain clear boundaries between active and archived work
6. **Trust the Process**: Let Claude handle the cognitive load of where things go

## Best Practices

### Folder Naming
- Use clear, descriptive names
- Avoid spaces (use hyphens or underscores)
- Be specific: "client-proposals" not "docs"
- Use prefixes for ordering: "01-current", "02-archive"

### File Naming
- Include dates: "2024-10-17-meeting-notes.md"
- Be descriptive: "q3-financial-report.xlsx"
- Avoid version numbers in names (use version control instead)
- Remove download artifacts: "document-final-v2 (1).pdf" → "document.pdf"

### When to Archive
- Projects not touched in 6+ months
- Completed work that might be referenced later
- Old versions after migration to new systems
- Files you're hesitant to delete (archive first)

## Related Use Cases

- Setting up organization for a new computer
- Preparing files for backup/archiving
- Cleaning up before storage cleanup
- Organizing shared team folders
- Structuring new project directories

