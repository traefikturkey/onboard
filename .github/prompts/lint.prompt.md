---
mode: agent
description: Run lint via make lint (or fallback) and apply focused fixes without scope creep.
model: 'GPT-5 mini (Preview)'
---

# /lint – Run and Resolve Linting

IMMEDIACY: Run lint immediately; no intro text.

## Preconditions
- From repo root.
- Dependencies installed, assume they are unless error shows otherwise (if needed run): `uv sync --dev` (contains flake8, black, isort, pylint).

## Command Strategy
1. Preferred: `make lint`
2. If target missing, sequential fallback:
   - Style/format: `uv run black --check .`
   - Import order: `uv run isort --check-only .`
   - Lint rules: `uv run flake8 .`
   - (Optional) Static analysis: `uv run pylint app tests` (only on request; can be noisy)

## Execution
Run `make lint` (or fallback). Suppress verbose formatter output in response unless issues remain.

## Issue Classification
| Type | Example Tools | Typical Fix |
|------|---------------|-------------|
| Formatting | black | Apply `uv run black .` |
| Import Order | isort | `uv run isort .` |
| Style/PEP8 | flake8 E/W codes | Minimal code edit / rename |
| Complexity | flake8 C901 / pylint R | Refactor function (only if requested) |
| Unused Imports/Vars | flake8 F401 / F841 | Remove or underscore prefix |
| Potential Bug | flake8 F821 / pylint E | Correct reference / add import |

## Minimal Fix Policy
Apply only edits required to eliminate reported issues. Do not refactor unrelated code. Group related changes per file in a single patch.

## Black + Isort Harmonization
Run formatters before re-running flake8 to avoid cascading style errors.
Order suggestion:
1. `uv run isort .`
2. `uv run black .`
3. `uv run flake8 .`

## Pylint (Optional)
If enabled, limit scope:
- Address Errors (E) first.
- Warnings (W/R/C) only if user requests or trivially fixable.

## Exit Criteria
- flake8 errors = 0.
- After formatting, subsequent checks clean.
- No unrelated edits.

## Output Format
Success: `LINT ok black_reformatted=<n> isort_fixed=<m> flake8_errors=0`

If issues:
1. Summary: `LINT issues black=<n> isort=<m> flake8_errors=<c>`
2. Top (≤25) problems: `file:line | CODE | brief fix`.
3. Consolidated fix plan (≤5 lines).
4. Re-run confirmation.

## Performance Tips
- If many style errors in one file, batch edits rather than one patch per error.
- If massive import reordering required, confirm before applying (risk of noisy diff).

## If make lint Exists Later
Update this prompt to just run that target and interpret consolidated output.

Respond by executing the lint plan now.
