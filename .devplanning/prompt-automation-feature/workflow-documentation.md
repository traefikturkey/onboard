# Workflow Documentation: Automated Instruction Improvements

## Overview

This document explains how to use the automated instruction improvement prompt to systematically enhance GitHub Copilot instructions based on conversation history analysis. The prompt is designed to work across any technology stack including Python, JavaScript, Go, Rust, Docker, and more.

## When to Run

### Trigger Conditions
- **Incremental Analysis**: When significant new conversation history has accumulated since last VERSION timestamp (5+ new conversations)
- **Full Analysis**: When no VERSION file exists (first run) or after major project changes
- Recurring AI/user interaction issues are observed
- After adopting new technologies or changing toolchains
- Monthly maintenance cycles for incremental improvements
- When instruction quality degradation is noticed across any technology stack

### Prerequisites Check
Before running the prompt:
```bash
# Ensure clean git state
git status

# Verify project's test/build system works
# Examples: npm test, uv run -m pytest, cargo test, make test, etc.
[project-specific verification command]

# Check conversation history availability
ls -la .specstory/history/

# Review current VERSION timestamp if exists
if [ -f ".github/VERSION" ]; then
    echo "Last analysis: $(cat .github/VERSION)"
    echo "Will analyze conversations since this timestamp"
else
    echo "No previous analysis - will scan all available history"
fi
```

## Execution Process

### Step 1: Environment Preparation
```bash
# Navigate to project root
cd /path/to/project

# Ensure clean working directory
git stash push -m "WIP before instruction improvements"

# Verify dependencies
uv sync
```

### Step 2: Run the Prompt
Copy the entire content of `.github/prompts/update-instructions.prompt.md` and provide it to GitHub Copilot with this instruction:

```
Execute this instruction improvement prompt. Analyze conversation history since the last VERSION timestamp, identify patterns, consolidate improvements, and systematically update all instruction files using project-appropriate tools and verification methods. Follow all verification steps and create a comprehensive git commit.
```

### Step 3: Monitor Execution
Watch for:
- Analysis progress through conversation history
- Pattern identification and consolidation
- File update operations
- Test execution results
- Git commit creation

### Step 4: Post-Execution Verification
```bash
# Verify tests still pass
uv run -m pytest

# Check git log
git log --oneline -1

# Review VERSION timestamp
cat .github/VERSION

# Check instruction file changes
git show --name-only HEAD
```

## Expected Outputs

### Intermediate Analysis File: `interaction-issues.md`
- File-by-file analysis of conversation history
- Each file gets its own header section with filename
- Very brief content summary for each conversation
- Documentation of AI/user interaction issues
- Problems encountered during request resolution
- Clear separation before pattern consolidation

### Primary Analysis File: `determined-issues.md`

**Current Copilot Documentation section:**
- Research findings on latest VS Code GitHub Copilot features
- Documentation links and capability summaries
- New frontmatter syntax and supported features

**Existing Instructions Summary section:**
```markdown
## filename.instructions.md
applyTo: `pattern from frontmatter`
Purpose: Brief description of what the file covers and its focus areas.
```

**Common Interaction Issues section:**
- Numbered issues (1, 2, 3...) derived from interaction-issues.md analysis
- Each issue includes:
  - **Description**: Detailed problem pattern explanation
  - **Key Pattern**: Specific conversation examples
  - **Suggested Instruction**: Exact text for instruction files
  - **Placement**: Target instruction file(s) for updates based on file types involved

**Implementation Notes section:**
- Concrete next steps for instruction file updates
- VERSION file update requirements
- Cross-file consistency needs

### File Modifications Expected
- `.github/copilot-instructions.md` - Enhanced workflow and project-specific standards
- `.github/instructions/[technology].instructions.md` - Technology-specific tooling and patterns
- `.github/instructions/testing.instructions.md` - Project-appropriate test enforcement
- `.github/instructions/build.instructions.md` - Build system and deployment patterns (if applicable)
- `.github/instructions/behavioral.instructions.md` - User compliance and communication patterns
- `.github/VERSION` - New timestamp
- Possible fixes in application code for import/reference issues

## Quality Assurance

### Validation Checklist
- [ ] All tests pass after changes (using project's test commands)
- [ ] No new compilation/build errors introduced
- [ ] Git commit message is comprehensive
- [ ] VERSION file updated correctly
- [ ] No broken imports or module references (for compiled languages)
- [ ] Instruction files maintain proper markdown syntax
- [ ] Project-preferred tools used throughout relevant sections
- [ ] Technology-specific patterns properly documented

### Common Issues and Solutions

**Issue**: Import errors after instruction updates
**Solution**: Check if any files were deleted/moved during analysis, update import statements

**Issue**: Test failures after changes
**Solution**: Review instruction changes for tool command modifications, ensure uv usage

**Issue**: Git commit fails
**Solution**: Check for untracked files, resolve any merge conflicts, verify file permissions

**Issue**: Pattern recognition misses obvious issues
**Solution**: Manually add specific patterns to determined-issues.md before implementation

## Maintenance and Evolution

### Extending the Prompt
To add new improvement patterns:
1. Add pattern to Phase 2 consolidation section
2. Include specific implementation steps in Phase 3
3. Update verification criteria in Phase 4
4. Test with trial run

### Customizing for Different Projects
Modify these sections for project-specific needs:
- Tool preferences (replace with project's standard toolchain)
- File structure paths (adjust for project organization)
- Test/build execution commands (use project's preferred approach)
- Technology-specific patterns (adapt to project's stack)
- Quality verification steps (use project's linting/formatting tools)

### Tracking Improvements
- VERSION file enables incremental analysis
- Git history shows evolution of instruction quality
- Test coverage trends indicate instruction effectiveness
- User feedback reveals remaining gaps

## Troubleshooting

### Debug Mode
For detailed execution tracking:
```bash
# Enable verbose git operations
git config --local core.verbose true

# Run tests with detailed output
uv run -m pytest -v

# Check file modification timestamps
find .github/instructions -name "*.md" -exec ls -la {} \;
```

### Recovery Procedures
If execution fails midway:
```bash
# Check current state
git status

# Review partial changes
git diff

# Reset if needed
git reset --hard HEAD

# Restore stashed work
git stash pop

# Re-run from clean state
```

### Performance Optimization
For large conversation histories:
- Consider analyzing in smaller time windows
- Focus on recent conversations (last 30 days)
- Pre-filter history files by relevance
- Use parallel processing for analysis steps

## Success Metrics

### Quantitative Measures
- Test pass rate maintained (>95%)
- Instruction file coverage (all files updated)
- Pattern implementation rate (all identified patterns addressed)
- Git commit cleanliness (no follow-up fixes needed)

### Qualitative Indicators
- Reduced recurring issues in future conversations
- Improved AI task completion rates
- Better user directive compliance
- More consistent tool usage patterns

## Future Enhancements

### Planned Improvements
- Automated pattern priority scoring
- Integration with CI/CD pipelines
- Pattern effectiveness tracking
- Cross-project instruction sharing

### Integration Opportunities
- GitHub Actions automation
- Conversation quality metrics
- Pattern library development
- Team instruction standards
