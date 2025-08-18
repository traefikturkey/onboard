---
mode: agent
description: This prompt analyzes conversation history to systematically improve GitHub Copilot instruction files based on identified interaction patterns and issues.
---

# Automated Instruction Improvement Prompt

## Mini/Haiku Model Guidelines

**For smaller models, follow these principles:**
- BE CONCRETE: Use exact file paths and commands. Avoid abstract concepts.
- BE SEQUENTIAL: Complete each step fully before moving to next.
- BE SPECIFIC: Replace placeholders with actual project commands.

**Simple workflow summary:**
1. Find conversation files newer than VERSION 
2. Read each file and note problems
3. Update instruction files with fixes
4. Test and commit changes

## Overview

This prompt replicates a proven workflow that:
1. Analyzes conversation history for AI/user interaction issues
2. Identifies common patterns and consolidates improvements
3. Systematically updates instruction files with project-appropriate tools
4. Verifies changes through testing and git operations
5. Creates version tracking for future analysis

## Simple Execution Checklist

For mini/Haiku models, follow this simplified checklist:

**Step 1: Get File List**
```bash
# Run this command and copy the output
if [ -f ".github/VERSION" ]; then
    find .specstory/history -name "*.md" -newer .github/VERSION
else
    find .specstory/history -name "*.md"
fi
```

**Step 2: Analyze Files**
- Read each file from Step 1
- Note AI/user problems
- Look for patterns

**Step 3: Update Instructions**
- Edit `.github/copilot-instructions.md`
- Edit files in `.github/instructions/`
- Add specific improvements found

**Step 4: Test and Commit**
```bash
[project test command]
echo "$(date)" > .github/VERSION
git add -A
git commit -m "Update instructions based on conversation analysis"
```

## Detailed Instructions

### Prerequisites

- Conversation history files in `.specstory/history/*.md`
- Existing instruction files in `.github/instructions/` and `.github/copilot-instructions.md`
- Git repository with clean working directory

## Execution Instructions

### Phase 1: Historical Analysis

1. **Check Analysis Starting Point and Get File List**
   
   This step determines which conversation history files need to be analyzed and outputs the complete list for use in subsequent steps.
   
   ```bash
   # Determine the analysis timeframe and get list of files to analyze
   if [ -f ".github/VERSION" ]; then
       VERSION_DATE=$(cat .github/VERSION)
       echo "Previous analysis timestamp: $VERSION_DATE"
       echo "Files to analyze (newer than VERSION timestamp):"
       # Find and list history files newer than VERSION timestamp
       find .specstory/history -name "*.md" -newer .github/VERSION | while IFS= read -r file; do
           echo "  $file"
       done
   else
       echo "No previous VERSION file exists - analyzing all available history"
       echo "Files to analyze (all available history):"
       # List all available history files
       find .specstory/history -name "*.md" 2>/dev/null | while IFS= read -r file; do
           echo "  $file"
       done
   fi
   ```
   
   **Output Usage**: Copy the list of files shown above for processing in step 3. This handles both incremental analysis (files newer than VERSION) and full analysis (all files) automatically.

2. **Create Analysis Directory**
   ```bash
   mkdir -p .devplanning/prompt-improvements-$(date +%Y-%m-%d)
   cd .devplanning/prompt-improvements-$(date +%Y-%m-%d)
   ```

3. **Analyze Conversation History**
   
   Create `interaction-issues.md` and analyze the conversation files listed in step 1:
   
   **Process each file individually:**
   For each file identified in step 1, add to `interaction-issues.md`:
   - Create header section using the filename (e.g., `## 2025-07-24_14-56-0400-improving-docker-build-times-for-a-container.md`)
   - Provide very brief and concise summary of the file's content
   - Note any issues that occurred between the user and the AI
   - Note any problems that the AI encountered solving the user's request
   - Document patterns like tool usage errors, repeated failures, user corrections
   
   **Complete each file analysis before moving to the next file.** The file list from step 1 already handles the VERSION timestamp logic, so simply process all files shown in that output one by one.

4. **Create Comprehensive Analysis Document**
   
   Create `determined-issues.md` with:
   
   **Current Copilot Documentation section:**
   - Search the web for latest VS Code GitHub Copilot instruction file documentation
   - Look for current frontmatter syntax, supported fields, and new features
   - Search terms to use: "VS Code GitHub Copilot instructions.md documentation", "GitHub Copilot workspace instructions file format", "VS Code Copilot prompt.md syntax"
   - Document any new capabilities or changes in instruction file format
   - Note supported `applyTo` patterns and frontmatter fields
   - Include links to current official documentation
   
   **Existing Instructions Summary section:**
   - Review `.github/copilot-instructions.md`
   - Review each file in `.github/instructions/*.instructions.md`
   - For each file document in format:
     ```
     ## filename.instructions.md
     applyTo: `pattern from frontmatter`
     Purpose: Brief description of what the file covers and its focus areas.
     ```
   
   **Common Interaction Issues section:**
   - Review the `interaction-issues.md` file created in step 3 looking for common problems
   - Create numbered sections (1, 2, 3...) for each common problem with:
     - **Issue Title** (concise problem description)
     - **Description**: Detailed explanation of the problem pattern
     - **Key Pattern**: Specific examples from conversations (if applicable)
     - **Suggested Instruction**: Exact text to add to instruction files
     - **Placement**: Which specific instruction file(s) should be updated (the .github/**/*.md file that makes the most sense based on file types involved in the problem)
   - Focus on actionable, specific problems rather than general improvements
   
   **Implementation Notes section:**
   - List concrete next steps for updating instruction files
   - Include any VERSION file update requirements
   - Note any cross-file consistency requirements

### Phase 2: Pattern Consolidation

5. **Consolidate Improvement Patterns**
   
   Based on historical analysis, identify and consolidate common improvement patterns. Look for recurring themes such as:

   **Task Completion and Verification:**
   - Always verify before claiming completion (run tests, builds, lints as appropriate for the project)
   - Keep explanations brief, make smallest possible changes first
   - After repeated failures: stop, analyze root cause, apply comprehensive solution once

   **User Directive Compliance:**
   - User requests always take priority over best practices
   - If user says delete/remove something, do it immediately without suggesting alternatives
   - Respect user's technology choices and constraints

   **Tool and Technology Consistency:**
   - Identify the project's preferred tools and enforce their usage consistently
   - Document tool-specific patterns (e.g., package managers, test runners, build tools)
   - Avoid mixing different approaches for the same task

   **File and Code Management:**
   - Follow established patterns for file operations in the project
   - Maintain import/dependency management consistency
   - Verify file operations completed successfully

   **Communication Standards:**
   - Be brief, don't ask permission for obvious next steps
   - Only implement what was requested
   - Provide clear progress reporting and error messages

   **Project-Specific Patterns:**
   - Identify and document any unique patterns from the conversation analysis
   - Note recurring debugging approaches or common failure modes
   - Document any framework-specific or domain-specific guidance discovered

### Phase 3: Systematic Implementation

6. **Update Core Copilot Instructions**
   
   Update `.github/copilot-instructions.md` (or main instruction file):
   - Add project-specific tool standards identified in analysis
   - Strengthen verification requirements based on project needs
   - Add failure recovery guidance based on observed patterns
   - Ensure examples use project's preferred tools and approaches

7. **Update Technology-Specific Instructions**
   
   For each technology used in the project, update relevant instruction files in `.github/instructions/`:
   - Add comprehensive tooling guidance based on project preferences
   - Enhance error handling with project-specific patterns
   - Add framework/technology-specific debugging guidance
   - Strengthen file management patterns observed in conversations
   - Add cleanup procedures for common operations

8. **Update Build and Deployment Instructions**
   
   Update build/deployment related instruction files:
   - Add technology-specific best practices discovered in analysis
   - Include production deployment patterns if applicable
   - Document environment-specific configuration needs
   - Add troubleshooting for common build/deployment issues

9. **Update Testing Instructions**
   
   Update testing-related instruction files:
   - Mandate project's preferred test execution approach
   - Add guidance based on testing patterns observed
   - Strengthen dependency management over workarounds
   - Add project-specific testing standards

10. **Update Project Management Instructions**
    
    Update workflow and project management instruction files:
    - Add guidance for project-specific tools and processes
    - Document appropriate use of flags, options, and configurations
    - Reference project compatibility requirements

11. **Update Behavioral Instructions**
    
    Update general behavioral instruction files:
    - Strengthen user directive compliance based on observed issues
    - Add project-specific requirements discovered in analysis
    - Enhance communication and progress reporting standards
    - Add project context-specific guidance

### Phase 4: Verification and Tracking

12. **Create Version Timestamp**
    ```bash
    echo "$(date)" > .github/VERSION
    ```

13. **Run Comprehensive Tests**
    ```bash
    # Use the project's preferred test command
    # Examples: npm test, make test, pytest, cargo test, etc.
    [project-specific test command]
    ```
    
    Verify:
    - All tests pass
    - No import/compilation errors
    - No syntax issues
    - Quality metrics remain acceptable (coverage, linting, etc.)

14. **Check for Linting Issues**
    ```bash
    # Check for any obvious syntax problems
    find .github/instructions -name "*.md" -exec echo "Checking: {}" \;
    ```

15. **Commit All Changes**
    ```bash
    git add .devplanning/prompt-improvements-$(date +%Y-%m-%d)/
    git add .github/VERSION
    git add .github/copilot-instructions.md
    git add .github/instructions/
    git add [any project files that needed fixes]  # If any import/reference fixes were needed
    
    git commit -m "Implement comprehensive instruction improvements

- Updated all instruction files based on conversation analysis
- Added consolidated improvement patterns from historical review
- Enhanced [technology]-specific instruction files
- Added [project-specific patterns] based on observed issues
- Created .github/VERSION timestamp for future analysis tracking
- Fixed any [language/framework]-specific errors found during analysis
- All tests passing with maintained quality metrics"
    ```

## Key Implementation Patterns

### Project Tool Standardization
Identify and enforce the project's preferred tools:
- Package management: Document the preferred approach for dependency management
- Testing: Standardize on the project's test execution method
- Building: Use the project's established build process
- Code quality: Apply the project's linting and formatting standards

### Technology-Specific Examples
Create examples appropriate for the project's technology stack:
- Use the project's actual tools and frameworks in instruction examples
- Reference real project files and patterns where possible
- Ensure code examples follow project conventions

### File Operation Patterns
Based on project structure and observed patterns:
1. Follow project's file organization conventions
2. Use project's import/dependency management approach
3. Maintain consistency with existing patterns
4. Verify operations completed successfully
5. Follow project's git workflow practices

### Verification Commands
Use project-appropriate verification:
```bash
# Examples of common project test commands:
# npm test (JavaScript/Node.js)
# uv run -m pytest (Python with uv)
# cargo test (Rust)
# go test ./... (Go)
# make test (Make-based projects)

# Pick the right one for your project
[project-specific test command]
```

## Error Recovery

If implementation fails:
1. Check git status: `git status`
2. Review error messages in terminal output
3. Verify files exist: `ls .github/instructions/`
4. Check project commands work: `[run project's test command]`
5. Read test output for specific errors

## Success Criteria

✅ All instruction files updated with consolidated patterns from analysis
✅ Project-specific tool preferences implemented consistently throughout
✅ VERSION timestamp created for future incremental analysis
✅ Full test suite passes (or appropriate quality checks for the project)
✅ Clean git commit with comprehensive changelog
✅ No compilation/import/syntax errors specific to the project's technology stack
✅ Instruction improvements address the specific issues identified in conversation history

## Future Usage

This prompt can be run periodically to:
- **Incremental Analysis**: Analyze new conversation history since last VERSION timestamp for targeted improvements
- **Full Analysis**: If no VERSION exists, scan all available history for comprehensive improvement identification
- Incorporate newly identified patterns into existing instruction ecosystem
- Maintain instruction file quality through systematic updates
- Ensure consistency across the instruction ecosystem

**Recommended Usage Pattern:**
- Monthly runs for incremental improvements based on new conversations
- Full runs after major project changes or when starting instruction improvement program
- Emergency runs when significant instruction quality issues are observed

Run again when significant conversation history has accumulated or when instruction quality issues are observed.
