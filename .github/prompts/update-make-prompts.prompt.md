---
mode: agent
description: Analyze recent history for test/lint issues, update test & lint prompts, and bump prompt VERSION.
---

# /update-make-prompts – Maintain test & lint prompt quality

IMMEDIACY: Perform actions directly; minimize narration. Only output a final concise summary (or detailed diagnostics if changes applied).

## Objective
Automate (procedurally) the review + potential refinement of `test.prompt.md` and `lint.prompt.md` based on recent execution evidence in history logs, then bump `.github/prompts/VERSION` if a change occurs.

## Data Sources
- Current prompt files: `.github/prompts/test.prompt.md`, `.github/prompts/lint.prompt.md`
- Version file: `.github/prompts/VERSION` (contains `INSTRUCTION_VERSION=YYYY-MM-DD.N`)
- History: `.specstory/history/*.md`

## Version Cutoff Logic
1. Parse current `INSTRUCTION_VERSION` → `version_date` (YYYY-MM-DD) and `increment` (N).
2. Only consider history files whose leading timestamp date (first 10 chars of filename) is >= `version_date`.

## Scan Procedure (Per Eligible History File)
For each file in chronological order:
1. Detect literal occurrences of `make test` or `make lint` (include variants in code blocks / inline).
2. Collect surrounding 40 lines (20 before / 20 after) for context.
3. Identify any of these signals:
   - Repeated reruns (pattern: multiple identical `make test` or `make lint` lines) → Suggest adding brevity or rerun guidance.
   - Flaky test indication (`re-run`, `flaky`, `intermittent`) → Consider adding a flaky triage bullet to test prompt (if absent).
   - Import/path confusion after test run (`ImportError`, `ModuleNotFoundError`, `sys.path`) → Ensure import guidance present (skip if already there).
   - Lint over-verbosity (large pasted lint output, >30 consecutive lint lines) → Consider instruction to suppress verbose echoing.
   - Missing fallback usage (errors referencing `make: *** No rule to make target 'test'`) → Ensure fallback instructions present.
   - Coverage concerns (phrases: `low coverage`, `increase coverage`) during test run → Optionally propose optional coverage line if not already present.

## Prompt Update Rules
- Do NOT duplicate existing guidance; only insert concise, atomic new lines.
- Prefer adding under existing relevant section headers.
- Keep additions ≤ 1–2 short lines per category per run.
- If no new actionable issues found, make no file modifications and skip version bump.

## Editing Strategy
1. Build an in-memory diff plan: list of insertions keyed by filename + anchor (e.g., after a header).
2. Apply all planned insertions in minimal patches.
3. Record which file(s) changed.

## Version Bump Logic
After edits:
1. Run current date command: `date +%F` → `today`.
2. If `today` == `version_date`: bump increment (N → N+1).
3. Else: set `INSTRUCTION_VERSION=today.1`.
4. Write updated line back to `.github/prompts/VERSION`.

## Git Commit Step (Only When Modifications Applied)
If (and only if) at least one of `test.prompt.md` or `lint.prompt.md` was modified:
1. Stage changed prompt files + `.github/prompts/VERSION`:
   - `git add .github/prompts/VERSION` and each changed `*.prompt.md`.
2. Generate a Conventional Commit style message:
   - Type: `chore(prompts):`
   - Short summary listing categories added (comma-separated) and new version.
   - Example: `chore(prompts): add flaky test guidance & lint verbosity note (version 2025-08-14.2)`
3. (Optional) If multiple distinct additions, append a blank line then bullet list of inserted lines grouped by file.
4. Execute `git commit -m "<message>"` (include extended description via heredoc if bullets present).
5. Do NOT push (leave that to higher-level automation/user).
6. Reflect commit occurrence in final output (see Output Format).

## Output Format
If no changes:
`UPDATE ok no-modifications version=<existing>`

If changes applied:
```
UPDATE applied version=<old> -> <new>
CHANGED: <comma-separated prompt files>
ADDITIONS:
<file>:<anchor_header>: <summary of each inserted line>
COMMIT: <commit message first line>
```

If scan error:
`UPDATE error reason=<brief>`

## Constraints
- No speculative changes (must tie to detected evidence snippet).
- Keep each new instruction line ≤ 120 chars.
- Avoid altering existing lines except to append new bullet(s).

## Post-Conditions
- Prompts reflect any newly observed recurring issues.
- Version file bumped only when prompts changed.

Execute the above procedure now.
