---
description: 'Guidelines for creating and maintaining GitHub Copilot instruction files and prompt files with current best practices and supported features.'
applyTo: '.github/{instructions/*.instructions.md,prompts/*.prompt.md}'
---

# Copilot Customization Instructions

## Research Requirements

**ALWAYS research current documentation before modifying Copilot instruction or prompt files.**

When working with GitHub Copilot customization files:

1. **Search for Current Documentation**: Use web search to find the latest VS Code Copilot documentation
2. **Verify Frontmatter Fields**: Check supported YAML frontmatter properties and syntax
3. **Review New Features**: Look for recently added capabilities or file format changes
4. **Validate Examples**: Ensure any examples follow current best practices

## Key Research Areas

### Frontmatter Documentation
Search for current information on:
- Supported YAML frontmatter fields in `.instructions.md` files
- Valid properties for `applyTo` patterns
- New metadata fields or configuration options
- Proper syntax and formatting requirements

### Prompt File Format
Research current standards for:
- `.prompt.md` file structure and frontmatter
- Supported `mode` values (agent, chat, etc.)
- Description field requirements and best practices
- Any new prompt customization features

### File Organization
Look for guidance on:
- Recommended directory structure for instruction files
- Naming conventions for instruction and prompt files
- Best practices for organizing multiple instruction files
- Integration with workspace settings

## Search Queries to Use

When researching, use these search terms:
- "VS Code GitHub Copilot instructions.md frontmatter documentation"
- "GitHub Copilot workspace instructions file format 2025"
- "VS Code Copilot prompt.md file syntax"
- "GitHub Copilot applyTo patterns documentation"
- "VS Code Copilot instruction file best practices latest"

## Implementation Guidelines

### Before Creating/Modifying Files
1. Research current documentation using web search
2. Validate frontmatter syntax against official examples
3. Check for any deprecated features or syntax
4. Review new capabilities that might be relevant

### Frontmatter Best Practices
- Use only documented and supported fields
- Keep descriptions clear and concise
- Use specific `applyTo` patterns that match actual file structures
- Follow YAML syntax exactly (proper indentation, quoting)

### Content Guidelines
- Write clear, actionable instructions
- Include specific examples when helpful
- Avoid overly complex or nested logic
- Test instructions with actual use cases

### Validation Steps
1. Check YAML frontmatter syntax
2. Verify `applyTo` patterns match real files
3. Test that instructions are clear and actionable
4. Ensure compliance with current Copilot documentation

## Common Frontmatter Fields

Based on research, commonly supported fields include:
- `description`: Brief description of the instruction file's purpose
- `applyTo`: File patterns where these instructions apply
- `mode`: For prompt files (agent, chat, etc.)

**Note**: Always verify current supported fields through web research before use.

## Error Prevention

### Avoid These Common Issues
- Using unsupported frontmatter fields
- Incorrect YAML syntax in frontmatter
- `applyTo` patterns that don't match actual files
- Overly complex or unclear instructions
- Outdated syntax or deprecated features

### When Errors Occur
1. Research current documentation again
2. Simplify frontmatter to only supported fields
3. Validate YAML syntax
4. Test with minimal examples first

## Maintenance

### Regular Updates
- Review instruction files quarterly for relevance
- Check for new Copilot features that could improve instructions
- Update examples to reflect current project patterns
- Remove deprecated syntax or approaches

### Documentation Tracking
- Keep notes on current Copilot version and features used
- Document any custom patterns or approaches
- Track which instruction files are most effective
- Monitor for breaking changes in Copilot updates

## Integration with Project Standards

### Consistency Requirements
- Follow project's existing instruction file patterns
- Maintain consistent formatting and style
- Use project-specific terminology and examples
- Align with project's development workflow

### Quality Assurance
- Test instruction effectiveness with real development tasks
- Gather feedback on instruction clarity and usefulness
- Refine based on actual usage patterns
- Ensure instructions don't conflict with each other
