# Testing Approach and Guidelines

This document records the concrete testing approach used in this repository, plus repeatable commands, mocking patterns, and CI guidance so the team can reproduce and extend tests reliably.

Summary
- Frameworks: pytest for unit/integration tests, behave for BDD/acceptance tests.
- Test runner: project uses `uv` to run commands inside the project environment (examples below).
- Coverage: measured with pytest-cov and reported to `.htmlcov`.

How to run tests locally

1. Run the full test pipeline (BDD features, then pytest):

```bash
make test
```

2. Run a focused pytest module with coverage:

```bash
uv run pytest tests/app/test_app_extra.py -q --cov=app --cov-report=term-missing
```

3. Run a single behave feature file:

```bash
uv run behave tests/features/app_routes.feature
```

Test structure and conventions
- Tests live under `tests/` using the same package layout as `app/` where possible:
  - `tests/models/` for model unit tests
  - `tests/services/` for service-level tests
  - `tests/app/` for Flask app + route + startup tests
- Use `pytest` fixtures and `monkeypatch` for sandboxed state. Prefer `tmp_path` for filesystem needs.
- Keep tests small and deterministic. Avoid network calls or long-running processes.

Mocking & stubbing patterns (practical examples used in this repo)

- Import-site patching: patch where an object is imported, not where it's defined. Example: if `app.models.tab` does `from .utils import from_list`, patch `app.models.tab.from_list`.
- Monkeypatching module-level side effects: many modules perform work on import (asset building, registering schedulers, etc.). For tests that import a module as `__main__`, ensure you:
  1. Clear cached module before running (e.g., `sys.modules.pop('app.app', None)`).
  2. Monkeypatch heavy dependencies before importing or use runpy with pre-existing stubs.

- Stubbing difficult third-party imports:
  - `flask_assets` and `cssmin` were stubbed in tests to avoid import/build errors. Create minimal `Bundle` and `Environment` no-ops whose `build()` is a no-op.
  - `flask_caching.Cache` may be used with a `@cache.cached` decorator at import time. Provide a FakeCache with a `cached` method that returns a no-op decorator in tests.

- Testing `__main__` flows (development vs production server branches):
  - For development branch: monkeypatch `app.app` internals and stub `Flask.run` or run module with guarded flags.
  - For production/hypercorn branch: stub `hypercorn.asyncio.serve`, provide a fake `Config`, and patch `asyncio.new_event_loop` to return a fake loop that can be started and closed without blocking tests.

Logging and capture
- The project's logger(s) attach a `StreamHandler` writing to stderr. Tests that assert logger output can either:
  - Replace the module `logger` with a tiny fake recorder object exposing `info()` (used in tests added in step 37), or
  - Use `caplog` to capture logging when the logger propagates to the root logger. Note: some loggers in this repo set `propagate = False` and a `StreamHandler` directly; in those cases caplog may not capture the handler output and replacing the logger or using `capsys` may be needed.

Filesystem and config defaults
- The helper `app/utils.copy_default_to_configs()` copies missing default files from `app/defaults` to `app/configs`. Tests should use `tmp_path` and monkeypatch `app.models.utils.pwd` or `app.utils.pwd` to point to a temp base to avoid touching repo files.

CI guidance (GitHub Actions sample)

Below is a minimal GitHub Actions workflow snippet you can copy into `.github/workflows/test.yml` to run the project's `make test` on pushes and PRs.

```yaml
name: CI - tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          python -m venv .venv
          source .venv/bin/activate
          pip install -U pip
          pip install -r requirements.txt || true
          pip install -e .
      - name: Run tests
        run: make test

```

Notes and troubleshooting
- If tests fail during CI due to import-time side effects (asset building or starting servers), ensure tests stub those modules as in our app tests. It's usually easiest to put small stubs in tests themselves where the import happens.
- Keep `make test` green locally before marking steps complete in the testing plan.

Appendix: Quick checklist for adding a new test
1. Identify module under test and whether it does work on import.
2. Add `tests/...` alongside module path.
3. Use `tmp_path` and `monkeypatch` to isolate filesystem and environment.
4. Stub third-party heavy dependencies locally in the test.
5. Run `uv run pytest tests/path/to/file.py -q` and iterate until green.
6. Run `make test` and update `.devplanning/add_testing/plan.md` to mark the step complete.
