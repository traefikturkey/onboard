# Workflow Documentation: Automated Instruction Improvements

## Overview

This document explains how to use the automated instruction improvement prompt to systematically enhance GitHub Copilot instructions based on conversation history analysis.

## When to Run

### Trigger Conditions
- **Incremental Analysis**: When significant new conversation history has accumulated since last VERSION timestamp (5+ new conversations)
- **Full Analysis**: When no VERSION file exists (first run) or after major project changes
- Recurring AI/user interaction issues are observed
- After major project changes (new frameworks, tools, patterns)
- Monthly maintenance cycles for incremental improvements
- When instruction quality degradation is noticed

### Prerequisites Check
Before running the prompt:
```bash
# Ensure clean git state
git status

# Verify test suite works
uv run -m pytest

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
Execute this instruction improvement prompt. Analyze conversation history since the last VERSION timestamp, identify patterns, consolidate improvements, and systematically update all instruction files. Follow all verification steps and create a comprehensive git commit.
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

## Expected Outcomes

### Successful Execution
- New analysis directory created in `.devplanning/`
- All instruction files updated with consolidated patterns
- VERSION timestamp updated with current date
- All tests passing
- Clean git commit with detailed changelog
- No import errors or syntax issues

### File Modifications Expected
- `.github/copilot-instructions.md` - Enhanced workflow and Python standards
- `.github/instructions/python.instructions.md` - uv-first tooling, error handling
- `.github/instructions/dockerfile.instructions.md` - Signal handling patterns
- `.github/instructions/testing.instructions.md` - uv test enforcement
- `.github/instructions/makefile.instructions.md` - Flag usage guidance
- `.github/instructions/taming-copilot.instructions.md` - Stronger user compliance
- `.github/VERSION` - New timestamp
- Possible import fixes in application code

## Quality Assurance

### Validation Checklist
- [ ] All tests pass after changes
- [ ] No new linting errors introduced
- [ ] Git commit message is comprehensive
- [ ] VERSION file updated correctly
- [ ] No broken imports or module references
- [ ] Instruction files maintain proper markdown syntax
- [ ] uv commands used throughout Python sections

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
- Tool preferences (replace uv with project standard)
- File structure paths
- Test execution commands
- Git workflow patterns

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
