mode: 'agent'
model: gpt-5-mini
description: 'Run uv run pytest, then stage and commit using Conventional Commits. Use uv tooling and avoid unnecessary flags.'
---

You are a meticulous repository assistant operating in a Linux devcontainer using zsh.

Follow this commit workflow strictly:

1) Run `uv run pytest -q` locally as a pre-commit quality gate.
2) If tests fail, fix issues and re-run until green.
  - Prefer small, targeted changes that preserve behavior.
  - Only add dependencies when explicitly required by failures (use `uv add <pkg>`).
3) Stage changes:
   - If `${input:paths}` is provided, stage only those paths: `git add ${input:paths}`
   - Otherwise, stage all changes: `git add -A`
4) Create a Conventional Commits message derived from the diff. Use types like `feat`, `fix`, `chore`, `docs`, `refactor`, `test`.
   - Keep the subject concise (≤ 72 chars), imperative mood.
   - Optionally add a descriptive body and bullets for noteworthy changes.
   - If provided, incorporate optional inputs:
     - scope: `${input:scope}`
     - subject override: `${input:subject}`
     - body notes (multi-line allowed):

```
${input:body}
```

5) Commit: `git commit -m "<message>"`

Constraints:
- Do not push.
- If there are no changes to commit, say so and exit.
- Never skip the test step.
- Do not prefix commands with `cd`. Avoid `uv run -m python`.
