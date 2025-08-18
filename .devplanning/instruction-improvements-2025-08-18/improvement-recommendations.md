# Instruction Improvement Recommendations
*Generated: August 18, 2025*

## Analysis Summary

**Historical Issue Analyzed**: Docker build time optimization query from 2025-07-24

**Key Findings**: The user received comprehensive Docker build optimization advice, but our existing `dockerfile.instructions.md` could be enhanced to proactively address these common performance concerns.

## Specific Improvements Needed

### 1. dockerfile.instructions.md Enhancements

**Current State**: Good foundation with security and basic optimization practices
**Gap Identified**: Missing specific build performance optimization guidance

**Recommended Addition**:
```markdown
### Build Performance Optimization
- Order COPY operations from least to most frequently changing
- Copy dependency files (requirements.txt, pyproject.toml, package.json) before source code
- Use cache mounts for package managers: `--mount=type=cache,target=/root/.cache/pip`
- Implement multi-stage builds with dedicated dependency stages
- Pin base image versions to exact patches for consistent caching
- Use BuildKit cache exports for CI/CD: `--cache-to=type=registry` and `--cache-from=type=registry`
- Keep .dockerignore comprehensive to minimize build context

#### Example Cache-Optimized Pattern
```dockerfile
# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# Copy source code last to avoid cache invalidation
COPY . .
```

### 2. .dockerignore Pattern Enhancement

**Current State**: Not explicitly covered in instructions
**Recommendation**: Add section to dockerfile.instructions.md

```markdown
### Build Context Optimization
- Maintain comprehensive .dockerignore files
- Exclude: tests/, .git/, __pycache__/, *.pyc, .coverage/, notebooks/, .devplanning/
- Include only necessary files in build context
- Regularly audit .dockerignore for new directories
```

## Implementation Priority

1. **High Priority**: Add build performance section to dockerfile.instructions.md
2. **Medium Priority**: Add .dockerignore guidance 
3. **Low Priority**: Consider creating a dedicated performance optimization prompt file

## Validation Criteria

- [ ] Instructions cover dependency layer caching strategies
- [ ] Cache mount examples provided for common package managers
- [ ] BuildKit cache export/import documented for CI/CD
- [ ] .dockerignore best practices included
- [ ] Real-world performance optimization examples included

## Files to Update

1. `.github/instructions/dockerfile.instructions.md` - Add performance optimization section
2. Consider adding `.github/prompts/docker-optimization.prompt.md` for common performance queries
