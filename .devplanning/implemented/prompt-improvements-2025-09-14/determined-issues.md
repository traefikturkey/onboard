# Existing Instructions Summary

## .github/copilot-instructions.md
applyTo: (implicit global via orchestration)
Purpose: Defines autonomous agent workflow, mandates tool usage for research, planning rigor, verbose planning while asking for concision; sets lifecycle (fetch, investigate, plan, implement, test) and todo list protocol.

## devcontainer.instructions.md
applyTo: `**/.devcontainer/**`
Purpose: Best practices for devcontainer config—multi-stage, non-root user, env loading, volumes, post-create commands, tooling.

## dockerfile.instructions.md
applyTo: `**/Dockerfile*`
Purpose: Dockerfile standards—base image choice, multi-stage separation, security, layer and package ordering, caching, health checks, example pattern.

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

## 1. Task Completion and Verification Standards
Description: AI states tasks complete without verification, uses excessive verbosity, or makes large rewrites instead of minimal fixes.
Suggested Instruction: "Always verify before claiming completion: run build/lint/test and report results. Keep explanations brief. Make smallest possible changes first."
Placement: `.github/copilot-instructions.md` (workflow enforcement) and `taming-copilot.instructions.md`.

## 2. User Directive Compliance
Description: Ignoring explicit user constraints (e.g., don't recreate deleted files) or overriding requests with best practices.
Suggested Instruction: "User requests always win over best practices. If user says delete/remove something, do it immediately without suggesting alternatives."
Placement: `taming-copilot.instructions.md` (strengthen Primacy of User Directives).

## 3. Iterative Problem-Solving and Failure Recovery
Description: Trial-and-error loops without analysis, redundant rebuilds, or sequential failed patches without fallback plans.
Suggested Instruction: "After 2 failures: stop and analyze the root cause completely. Draft the full solution, then apply once."
Placement: `.github/copilot-instructions.md` (Debugging section) and `dockerfile.instructions.md`.

## 4. Environment and Tool Context Awareness
Description: Missing environment verification, wrong tool usage (system vs project), or not using established patterns.
Suggested Instruction: "Always use uv commands for Python projects: `uv run -m pytest`, `uv add <library>`, `uv run`. Never use pytest or python directly. Verify files exist before suggesting fixes."
Placement: `python.instructions.md`, `devcontainer.instructions.md`, and `.github/copilot-instructions.md`.

## 5. Code Quality and API Preservation
Description: Removing functionality to satisfy linter, altering public APIs, or making behavioral changes without flagging risks.
Suggested Instruction: "Never remove public methods/properties to fix lints. Add type hints instead. Always mention if behavior might change."
Placement: `python.instructions.md` (Error Handling / Style) and `taming-copilot.instructions.md`.

## 6. Testing Strategy and Maintenance
Description: Complex test patching, testing private methods, unnecessary workarounds, or deleting tests without consideration.
Suggested Instruction: "Test public APIs only. Install missing dependencies instead of adding skips. If user wants tests deleted, delete them immediately."
Placement: `testing.instructions.md`.

## 7. File and Import Management
Description: Import path hacks, incomplete file operations, uncoordinated file moves, or removing needed components.
Suggested Instruction: "Fix imports by checking __init__.py files first. When moving files: create new, update imports, delete old, commit all together. Always verify file operations worked."
Placement: `python.instructions.md`, `taming-copilot.instructions.md`, and `dockerfile.instructions.md`.

## 8. Communication and Progress Reporting
Description: Verbose checklist repetition, excessive confirmation requests, scope creep, or missing validation summaries.
Suggested Instruction: "Be brief. Don't ask permission for obvious next steps. Only implement what was requested. Run tests after changes and report pass/fail."
Placement: `.github/copilot-instructions.md` and `taming-copilot.instructions.md`.

## 9. Docker and Container Signal Handling
Description: Container processes don't respond to Ctrl-C/SIGINT properly, entrypoint scripts use sudo/permissions incorrectly.
Key Pattern: Multiple conversations about fixing signal forwarding in Docker containers.
Suggested Instruction: "Use `gosu` with `exec` in production entrypoint scripts to drop privileges and forward signals. Sudo is acceptable for devcontainer usage. Ensure CMD uses direct command execution (not shell wrapping) for proper signal delivery. When docker.sock is mounted, fix permissions in entrypoint with: `chown ${USER}:${USER} /var/run/docker.sock >/dev/null 2>&1 || true`."
Placement: `dockerfile.instructions.md` (add signal handling section).

## 10. Web Framework Integration Debugging
Description: Frontend clicks/navigation not working due to JavaScript framework conflicts (HTMX boost interfering with redirects).
Key Pattern: Debugging template and route interactions where client-side frameworks override expected behavior.
Suggested Instruction: "Check for JS framework conflicts when links/forms don't work. Add `data-*-boost='false'` or equivalent to opt out of framework interception."
Placement: `python.instructions.md` (Flask patterns section).

## 11. Project Tool Preference Enforcement  
Description: Using system tools instead of project-managed tools (uv run -m pytest).
Key Pattern: Consistent pattern of users correcting to use project tooling.
Suggested Instruction: "Always use uv for Python projects. Use `uv run -m pytest` not `pytest`. Use `uv add <library>` not direct installs. Use `uv run` not direct python."
Placement: `python.instructions.md` (strengthen existing tooling guidance).

## 12. Module Deletion and Import Cleanup
Description: When files are deleted, imports and tests still reference them causing ImportErrors during collection.
Key Pattern: User deletes files, agent tries to recreate them instead of cleaning up references.
Suggested Instruction: "When user deletes files: update all imports to use alternatives, move skip() before imports in tests, delete tests that can't be salvaged. Never recreate deleted files."
Placement: `python.instructions.md` and `testing.instructions.md`.

## 13. Make Command Flag Usage
Description: Adding unnecessary flags like `-s` or `-j1` to make commands causes build system failures.
Key Pattern: Agent adds flags to make commands without explicit need or user request.
Suggested Instruction: "Use make commands without flags unless required for the specific task. Do not add `-s`, `-j1`, or other flags unless the user requests them."
Placement: `makefile.instructions.md` and `.github/copilot-instructions.md`.

## 14. Package Installation with uv
Description: Using incorrect uv add syntax or missing development/notebook dependency flags.
Key Pattern: Installing packages without proper context flags for development or notebook environments.
Suggested Instruction: "Use `uv add <library_name>` for production dependencies. Use `uv add --dev <library_name>` for development dependencies. Use `uv add --group notebook <library_name>` for notebook-specific dependencies. Never use direct package installation tools."
Placement: `python.instructions.md` and `.github/copilot-instructions.md`.

# Implementation Notes

**IMPORTANT:** When merging these instruction improvements, update `.github/copilot-instructions.md` and other .github instruction files to use **uv commands by default** for Python projects. 

Required updates:
1. **Workflow section** - Change all examples to use uv commands
2. **Python environment configuration** - Use `uv run` commands instead of direct python
3. **Tool usage examples** - Replace `pytest` with `uv run -m pytest`, replace installs with `uv add <library>`
4. **Docker entrypoint example** - Add the complete entrypoint script from this project's Dockerfile to `dockerfile.instructions.md`
5. **VERSION file** - Run `echo "$(date)" > .github/VERSION` to mark when these instruction improvements were implemented for future .specstory/history analysis

This ensures all instruction files consistently use uv for Python development workflows.



