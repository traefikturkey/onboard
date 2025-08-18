# Existing Instructions Summary

## .github/copilot-instructions.md
applyTo: (implicit global via orchestration)
Purpose: Defines autonomous agent workflow, mandates tool usage for research, planning rigor, verbose planning while asking for concision; sets lifecycle (fetch, investigate, plan, implement, test) and todo list protocol.

## copilot_customization.instructions.md
applyTo: (instructions file creation and maintenance)
Purpose: Guidelines for creating and maintaining GitHub Copilot instruction files with current best practices and supported features.

## dockerfile.instructions.md
applyTo: `**/Dockerfile*`
Purpose: Dockerfile standards—base image choice, multi-stage separation, security, layer and package ordering, caching, health checks, build performance optimization.

## ignore-files.instructions.md
applyTo: `**/.{gitignore,dockerignore}`
Purpose: Synchronization and ordering rules for ignore files; defines shared vs file-specific entries, ordering conventions.

## makefile.instructions.md
applyTo: `**/Makefile`
Purpose: Makefile structure, variable management, semantic version bumping, background process guidance, devcontainer integration.

## python.instructions.md
applyTo: `**/*.py`
Purpose: Python style, typing, naming, documentation, error handling, configuration, Flask patterns, testing expectations, tooling.

## self-explanatory-code-commenting.instructions.md
applyTo: `**`
Purpose: Promote minimal commenting focused on WHY; enumerates good vs bad comment patterns and annotation tags.

## taming-copilot.instructions.md
applyTo: `**`
Purpose: Governance/constraint overlay—priority of user directives, minimalism, concise answers, code only on request, minimal diffs.

## testing.instructions.md
applyTo: `**/tests/**/*.py`
Purpose: Testing layout, naming, fixtures, coverage goals, integration guidance, sample patterns.

# Common Interaction Issues

## 1. Docker Build Performance Optimization
Description: User requests for improving Docker build times, specifically focused on caching strategies, layer optimization, and BuildKit features.
Key Pattern: The analyzed conversation showed comprehensive Docker optimization advice covering dependency layer caching, remote BuildKit cache, and file operation ordering.
Suggested Instruction: "Order COPY operations from least to most frequently changing. Copy dependency files before source code. Use cache mounts for package managers. Implement BuildKit cache exports for CI/CD. Keep .dockerignore comprehensive to minimize build context."
Placement: dockerfile.instructions.md (Build Performance Optimization section)

## 2. Build Context and File Management
Description: Missing guidance on .dockerignore optimization and build context minimization for container performance.
Key Pattern: User received advice about excluding tests/, .git/, __pycache__, and other development artifacts to improve build performance.
Suggested Instruction: "Maintain comprehensive .dockerignore files. Exclude: tests/, .git/, __pycache__/, *.pyc, .coverage/, notebooks/, .devplanning/. Include only necessary files in build context. Regularly audit .dockerignore for new directories."
Placement: dockerfile.instructions.md (Build Context Optimization section)

# Implementation Notes

**IMPORTANT:** The Docker performance improvements identified have been successfully implemented in `dockerfile.instructions.md` with new sections for Build Performance Optimization and Build Context Optimization.

Required updates completed:
1. ✅ **Build Performance section** - Added cache mount examples, layer optimization guidance, and CI/CD integration patterns
2. ✅ **Build Context section** - Added comprehensive .dockerignore patterns and build context optimization guidance  
3. ✅ **VERSION file** - Updated timestamp to `Mon Aug 18 05:27:40 PM EDT 2025` to track completion

**Future Analysis**: Next incremental run will analyze conversations newer than the current VERSION timestamp. The enhanced Docker instructions should reduce future queries about container build optimization.
