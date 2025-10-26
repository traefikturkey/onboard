mode: agent
model: gpt-5-mini
description: Unified test run wrapper; uses uv run pytest. Prefer the /check prompt for full triage.
---

# /test – Execute and Triage Test Run

IMMEDIACY: Run the command first with no preamble. Only then output results.

## Preconditions
- From repo root.
- Dependencies installed, assume they are unless error shows otherwise (if needed run): `uv sync --dev`.

## Command Strategy
1. `uv run pytest -q` (primary)
2. Re-run only failing tests as needed: `uv run pytest <path>::<TestClass>::<test_name> -q`

## Execution
Run immediately. Capture details internally; emit minimal success line. On failure/warning, include classified details.

## Failure / Error Classification
Classify each failing test into one of:
- ImportError / ModuleNotFoundError (likely PYTHONPATH / package init)
- AssertionError (logic discrepancy)
- Exception during setup/teardown (fixture or resource issue)
- Data / Environment dependency (e.g., needs file, network)
- Flaky / nondeterministic (timing, randomness)

## Remediation Playbook
| Category | Checklist | Fix Patterns |
|----------|-----------|--------------|
| ImportError | Confirm `__init__.py` in package dirs, run from project root, avoid ad-hoc sys.path | Add missing `__init__.py`, adjust imports to absolute (e.g. `from app.models.bookmark import Bookmark`) |
| AssertionError | Inspect expected vs actual, compute minimal code delta | Update logic or test expectation; add clarifying variable names |
| Setup Error | Identify fixture raising; isolate by running test alone | Guard resource creation, mock external deps |
| Environment/Data | Check test referencing real services | Replace with mock / stub, inject test data |
| Flaky | Re-run failing test 3x (`-k <name>`), check time/sleep usage | Add deterministic seed, remove arbitrary sleeps |

## Import Path Guidance
If imports fail:
1. Ensure working directory is repository root.
2. Avoid modifying `sys.path`; rely on package layout.
3. Add missing `__init__.py` where needed.
4. Prefer absolute imports that match package structure (e.g., `from app.models.bookmark import Bookmark`).

## Re-run Loop
After fixes, re-run only failing subset first. When all pass, perform full run again to confirm no regressions.

## Exit Criteria
- No failures/errors.
- Warnings eliminated or justified.
- Skips documented.

## Output Format
Success (no failures/errors, no new warnings):
`TEST ok total=<t> failed=0 errors=0 skipped=<s> scenarios=<sc> time=<sec> coverage=<pct>%`

If failures or warnings:
1. Summary line (replace ok with FAIL or WARN).
2. Each failure: `path::test | Category | root cause`.
3. Consolidated fix list (≤6 lines).
4. Post-fix confirmation line.

## If No Tests Found
- Verify tests directory exists and naming `test_*.py`.
- Ensure not accidentally inside subdirectory when running.
- Run explicit: `uv run pytest tests -q`.

## Optional Enhancements (Do Not Add Unless Requested)
- Coverage: `uv run pytest --maxfail=1 --cov=app --cov-report=term-missing -q`.
- Parallel: `pytest -n auto` (add `pytest-xdist` first).

For end-to-end quality (tests + optional lint), prefer `.github/prompts/check.prompt.md`.

Respond now by executing the plan.
