# Automated Instruction Improvement Prompt

This prompt analyzes conversation history to systematically improve GitHub Copilot instruction files based on identified interaction patterns and issues.

## Overview

This prompt replicates a proven workflow that:
1. Analyzes conversation history for AI/user interaction issues
2. Identifies common patterns and consolidates improvements
3. Systematically updates instruction files with uv-first approach
4. Verifies changes through testing and git operations
5. Creates version tracking for future analysis

## Prerequisites

- Conversation history files in `.specstory/history/*.md`
- Existing instruction files in `.github/instructions/`
- Working test suite accessible via `uv run -m pytest`
- Git repository with clean working directory

## Execution Instructions

### Phase 1: Historical Analysis

1. **Check Analysis Starting Point**
   ```bash
   # Determine the analysis timeframe
   if [ -f ".github/VERSION" ]; then
       VERSION_DATE=$(cat .github/VERSION)
       echo "Previous analysis timestamp: $VERSION_DATE"
       echo "Analyzing conversations since this date"
       # Filter history files by modification date newer than VERSION timestamp
   else
       echo "No previous VERSION file exists - analyzing all available history"
       echo "This appears to be the first instruction improvement run"
   fi
   ```

2. **Create Analysis Directory**
   ```bash
   mkdir -p .devplanning/prompt-improvements-$(date +%Y-%m-%d)
   cd .devplanning/prompt-improvements-$(date +%Y-%m-%d)
   ```

3. **Analyze Conversation History**
   
   Create `interaction-issues.md` and analyze conversation files based on VERSION timestamp:
   
   **If VERSION file exists:**
   - Only analyze `.specstory/history/*.md` files modified after the VERSION timestamp
   - Focus on new conversations since last improvement cycle
   - Compare file modification dates with VERSION timestamp to filter relevant files
   
   **If no VERSION file exists:**
   - Analyze all available files in `.specstory/history/*.md`
   - This represents the first comprehensive instruction improvement run
   - Scan entire conversation history for patterns
   
   For each relevant history file:
   - Create header section using filename
   - Provide brief content summary
   - Note issues between user and AI
   - Note problems AI encountered solving requests
   - Document patterns like tool usage errors, repeated failures, user corrections

4. **Create Comprehensive Analysis Document**
   
   Create `determined-issues.md` with:
   
   **Existing Instructions Summary section:**
   - Review `.github/copilot-instructions.md`
   - Review each file in `.github/instructions/*.instructions.md`
   - For each file document:
     - File types from `applyTo` header
     - Brief description of purpose and content
   
   **Common Interaction Issues section:**
   - Review `interaction-issues.md` for patterns
   - Create sections for each common problem with:
     - Brief description of the problem
     - Suggested instruction improvements
     - Target `.github/**/*.md` file for the improvement

### File Selection Logic

**For Incremental Analysis (VERSION file exists):**
```bash
# Get VERSION timestamp
VERSION_DATE=$(cat .github/VERSION)
VERSION_EPOCH=$(date -d "$VERSION_DATE" +%s)

# Find history files newer than VERSION timestamp
find .specstory/history -name "*.md" -newer .github/VERSION

# Alternative approach using modification time comparison
for file in .specstory/history/*.md; do
    FILE_EPOCH=$(stat -c %Y "$file")
    if [ $FILE_EPOCH -gt $VERSION_EPOCH ]; then
        echo "Analyzing: $file (modified after $VERSION_DATE)"
        # Process this file
    else
        echo "Skipping: $file (older than $VERSION_DATE)"
    fi
done
```

**For Full Analysis (no VERSION file):**
```bash
# Process all available history files
for file in .specstory/history/*.md; do
    echo "Analyzing: $file"
    # Process this file
done
```

5. **Consolidate Improvement Patterns**
   
   Based on historical analysis, implement these proven improvement patterns:

   **Task Completion Standards:**
   - Always verify before claiming completion with build/lint/test
   - Keep explanations brief, make smallest possible changes first
   - After 2 failures: stop, analyze root cause, apply full solution once

   **User Directive Compliance:**
   - User requests always win over best practices
   - If user says delete/remove something, do it immediately without alternatives
   - Never remove public methods/properties to fix lints - add type hints instead

   **Python Tool Standardization:**
   - Always use uv commands: `uv run -m pytest`, `uv add <library>`, `uv run`
   - Never use pytest or python directly
   - Use `uv add --dev` for development dependencies
   - Use `uv add --group notebook` for notebook-specific dependencies

   **File and Import Management:**
   - Fix imports by checking __init__.py files first
   - When moving files: create new, update imports, delete old, commit together
   - Always verify file operations worked

   **Docker Signal Handling:**
   - Use gosu with exec in production entrypoint scripts
   - Ensure proper signal forwarding with direct command execution
   - Fix docker.sock permissions in entrypoint when needed

   **Communication Standards:**
   - Be brief, don't ask permission for obvious next steps
   - Only implement what was requested
   - Run tests after changes and report pass/fail

### Phase 3: Systematic Implementation

6. **Update Core Copilot Instructions**
   
   Update `.github/copilot-instructions.md`:
   - Add Python Project Standards section mandating uv usage
   - Strengthen verification requirements in workflow
   - Add failure recovery guidance (2-failure rule)
   - Ensure all Python examples use uv commands

7. **Update Python Instructions**
   
   Update `.github/instructions/python.instructions.md`:
   - Add comprehensive Project Tooling section mandating uv
   - Enhance Error Handling with API preservation rules
   - Add Web Framework Integration debugging guidance
   - Strengthen file management patterns
   - Add module deletion cleanup procedures

8. **Update Docker Instructions**
   
   Update `.github/instructions/dockerfile.instructions.md`:
   - Add complete Signal Handling section
   - Include production entrypoint script example with gosu/exec
   - Document docker.sock permission fixing
   - Add CMD best practices for signal forwarding

9. **Update Testing Instructions**
   
   Update `.github/instructions/testing.instructions.md`:
   - Mandate uv test execution: `uv run -m pytest`
   - Add guidance against testing private methods
   - Strengthen dependency installation over test skipping
   - Add user deletion compliance

10. **Update Makefile Instructions**
    
    Update `.github/instructions/makefile.instructions.md`:
    - Add guidance against unnecessary flags (-s, -j1)
    - Document when flags are appropriate
    - Reference build system compatibility

11. **Update Taming Copilot Instructions**
    
    Update `.github/instructions/taming-copilot.instructions.md`:
    - Strengthen Primacy of User Directives section
    - Add API preservation requirements
    - Enhance minimal change requirements
    - Add brief communication mandates

### Phase 4: Verification and Tracking

12. **Create Version Timestamp**
    ```bash
    echo "$(date)" > .github/VERSION
    ```

13. **Run Comprehensive Tests**
    ```bash
    uv run -m pytest
    ```
    
    Verify:
    - All tests pass
    - No import errors
    - No syntax issues
    - Coverage remains acceptable

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
    git add app/  # If any import fixes were needed
    
    git commit -m "Implement comprehensive instruction improvements

- Updated all instruction files to use uv-first approach
- Added consolidated improvement patterns from conversation analysis
- Enhanced Python, Docker, Make, and Testing instruction files
- Added signal handling examples and uv usage patterns
- Created .github/VERSION timestamp for future analysis tracking
- Fixed any import errors found during analysis
- All tests passing with maintained coverage"
    ```

## Key Implementation Patterns

### uv-First Approach
Replace all Python tooling references:
- `pytest` → `uv run -m pytest`
- `python` → `uv run`
- `pip install` → `uv add`
- Direct package installs → `uv add [--dev|--group notebook]`

### Signal Handling Example (Docker)
```bash
#!/bin/bash
set -e

# Fix docker socket permissions if mounted
chown ${USER}:${USER} /var/run/docker.sock >/dev/null 2>&1 || true

# Drop privileges and exec (for signal forwarding)
exec gosu ${USER} "$@"
```

### File Operation Pattern
1. Create new file
2. Update imports
3. Delete old file
4. Commit all together
5. Verify operations worked

### Verification Commands
```bash
# Always run after changes
uv run -m pytest
echo "Tests completed with exit code: $?"

# Check git status
git status --porcelain
```

## Error Recovery

If implementation fails:
1. Check git status for uncommitted changes
2. Review error messages for missing dependencies
3. Verify file paths exist before modification attempts
4. Ensure uv commands work in current environment
5. Run tests to identify import or syntax issues

## Success Criteria

✅ All instruction files updated with consolidated patterns
✅ uv-first approach implemented throughout
✅ VERSION timestamp created for future analysis
✅ Full test suite passes
✅ Clean git commit with comprehensive changelog
✅ No import errors or syntax issues

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
