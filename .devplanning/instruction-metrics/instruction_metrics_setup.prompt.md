# Instruction Metrics Setup Prompt

Goal: Initialize and maintain instruction improvement tracking infrastructure.

Steps:
1. Ensure instruction version file exists at `.github/instructions/VERSION`.
2. Ensure metrics log directory `.devplanning/instruction-metrics/` exists.
3. If missing, create `.devplanning/instruction-metrics/log.tsv` with header.
4. If missing, create `.github/instructions/CHANGELOG.md` with initial version entry.
5. Append new task metric line (parameters supplied at invocation) to `log.tsv`.
6. (Optional) Generate weekly summary section in `tracking_improvements.md`.

Inputs (to be provided when invoking):
- task_id
- build_run (Y/N)
- lint_run (Y/N)
- tests_run (Y/N)
- verification_complete (Y/N)
- premature_done (Y/N)
- edit_attempts (int)
- patch_failures (int)
- scope_creep (Y/N)
- user_corrections (int)
- large_rewrite (Y/N)
- first_pass_tests (Y/N)
- first_pass_lint (Y/N)
- lines_changed (int)
- verbosity_chars (int)
- target_band (simple|moderate|complex)
- delta_reporting (Y/N)
- notes (short free text)

Header (must match log.tsv):
```
# date\ttime\ttask_id\tinstruction_version\tbuild_run\tlint_run\ttests_run\tverification_complete\tpremature_done\tedit_attempts\tpatch_failures\tscope_creep\tuser_corrections\tlarge_rewrite\tfirst_pass_tests\tfirst_pass_lint\tlines_changed\tverbosity_chars\ttarget_band\tdelta_reporting\tnotes
```

Behavior Rules:
- Do not overwrite existing log lines.
- If version file missing, create with current date version `YYYY-MM-DD.1`.
- If same date and version already exists but instructions changed, increment trailing integer.
- Keep CHANGELOG entries minimal: version, date, summary, expected impact.
- Never adjust past log lines.

Quality Gates (auto after entry append):
- If premature_done == Y OR verification_complete == N → emit warning note.
- If large_rewrite == Y and scope_creep == Y → emit escalation note.

Output: Confirmation summary with any warnings.
