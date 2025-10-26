mode: 'agent'
model: gpt-5-mini
description: 'Unified quality gate: run uv run pytest; triage and fix failures; optionally run lint (isort/black/flake8). Keep changes minimal and avoid unnecessary flags.'
---

# Quality Check and Fix

## Objective
Run `uv run pytest -q` and systematically address any test collection/execution failures until the suite passes cleanly. Optionally, run lint (isort/black/flake8) and fix high-signal issues.

## Context
- Project uses uv; tests are executed with `uv run pytest` (no Make targets required)
- Primary quality gate: tests green. Lint checks are optional if configured
- Constraints from repository instructions:
  - Use `uv run pytest` (do not add `-m`)
  - Do not prefix commands with `cd`
  - Prefer small, surgical fixes that preserve behavior

## Instructions

### Phase 1: Initial Assessment
1. Run `uv run pytest -q` to see current status
2. Categorize issues:
   - Import errors (pytest collection)
   - Test failures (pytest execution)
   - Missing dependencies (only add via `uv add` if strictly necessary)
   - Optional: Lint errors if `flake8` is configured

### Phase 2: Systematic Resolution
For each category of issues, apply these steps:

#### Test Collection/Import Issues
1. Identify missing modules or bad imports from pytest output
2. Align test imports with actual implementation or add minimal shims where appropriate
3. Re-run `uv run pytest -q` to confirm collection succeeds

#### Test Failures (execution)
1. Triage failing tests; prefer fixing source with minimal, behavior-preserving edits
2. Add/adjust tests only when behavior contract has changed intentionally
3. Re-run `uv run pytest -q` until clean

#### Missing Dependencies
1. Only when a failure clearly indicates a missing dependency, add it using `uv add <package>`
2. Re-run tests to verify resolution

#### Optional Lint (if configured)
Run in this order for minimal conflicts:
1. `uv run isort .`
2. `uv run black .`
3. `uv run flake8 .` (address high-signal issues; avoid scope creep)

### Phase 3: Iteration Loop
**CRITICAL**: Continue this process until completion:

1. Run `uv run pytest -q`
2. If ANY failures exist:
   - Identify the next highest priority issue
   - Apply appropriate fix from Phase 2
   - Return to step 1
3. If NO failures exist:
   - Optionally run lint if configured (isort/black/flake8 order)
   - Document any changes made
   - TASK COMPLETE

### Phase 4: Verification
1. Run `uv run pytest -q` and confirm all tests pass with exit code 0
2. Optional: If lint was run, ensure `uv run flake8 .` reports no errors
3. Confirm no regressions in core functionality (spot-check key flows if needed)

## Success Criteria
- [ ] `uv run pytest -q` exits with code 0
- [ ] Zero pytest collection errors
- [ ] All tests pass or skip appropriately
- [ ] Optional: Lint passes clean if run

## Error Handling

### Common Issues and Solutions
- Import errors: check packages have `__init__.py`, verify absolute imports (`from app.models.bookmark import Bookmark`)
- Interface mismatches: align test expectations with current implementation (prefer fixing source to match contracts)
- Missing dependencies: add only when failures explicitly require them using `uv add`

### When Stuck
1. Focus on one error at a time
2. Check actual source code to understand current interfaces
3. Prioritize getting tests passing before optional lint
4. Use `git status` to track changes and avoid regressions

### Quality Gates Priority
1. Test collection (pytest)
2. Test execution (pytest)
3. Optional lint (isort/black/flake8)

### Helpful Triage Aids
- Re-run a single test: `uv run pytest path/to/test_file.py::TestClass::test_name -q`
- Import path guidance:
   1) Run from repo root; avoid modifying `sys.path`
   2) Ensure packages have `__init__.py`
   3) Prefer absolute imports over relative ad-hoc paths

### Optional Coverage (only if requested)
- `uv run pytest --maxfail=1 --cov=app --cov-report=term-missing -q`

## Notes
- This is an iterative process - expect multiple cycles
- Each fix may reveal new issues
- Always verify fixes don't break existing functionality
- Document significant changes for review
