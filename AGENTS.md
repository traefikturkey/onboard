# Repository agent guidance

## Overview

- Onboard is a Python 3.12–3.13 Flask application for a configurable dashboard of feeds and bookmarks.
- Use `uv` for Python environments and commands; dependencies are declared in the root `pyproject.toml` and locked in `uv.lock`.
- Keep changes focused. Preserve existing public behavior and add or update tests for changed behavior.

## Primary commands

Run commands from the repository root.

- Install/sync development dependencies: `uv sync --dev`
- Run the application locally: `make run`
- Run non-integration tests with coverage: `make test`
- Run a focused test: `uv run pytest tests/path/to/test_file.py`
- Run the full suite, including container-based integration tests: `make test-all`
- Format Python: `make format`
- Lint Python: `make lint`
- Check dependency declarations: `make deptry`
- Build the production container: `make build`
- Run the production container on port 9830: `make up`

`make lint` runs `make format` first and therefore modifies files. Use it only when formatting changes are acceptable. The `bump-*` and `publish` targets create tags and push to Git; never run them unless the user explicitly requests a release. The Makefile may create an empty ignored `.env` as a build prerequisite.

## Validation

- For Python changes, start with the narrowest relevant `uv run pytest ...` command, then run `make test` when practical.
- Pytest defaults exclude tests marked `integration` and enforce strict markers/configuration (`pytest.ini`).
- Integration tests require Docker, build `onboard:prod`, start Selenium and app containers, and remove matching test containers. Run them only when the change needs integration coverage and container mutation is acceptable.
- For formatting-only documentation changes, reread the rendered Markdown/diff; a full test suite is unnecessary.
- Container changes can be checked with `make test-build-prod`; `make test-build` also builds the larger devcontainer image.

## Architecture and project structure

- `run.py` imports the production Flask app from `app/main.py`; Gunicorn and container commands use `run:app`.
- `app/main.py` contains the runtime app, routes, cache/assets setup, layout initialization, and scheduler lifecycle.
- `app/factory.py` provides an injectable application factory used by shared pytest fixtures. When changing routes or initialization, check whether behavior must remain aligned between this factory and `app/main.py`.
- `app/api/` contains Flask blueprints and Pydantic-backed request/response models.
- `app/models/` contains layouts, feeds, widgets, scheduling, and file-store models.
- `app/services/` contains bookmark, favicon, Docker, migration, and click-tracking services.
- `app/templates/` and `app/static/css/` implement the Jinja/HTMX/Alpine UI. Flask-Assets generates `app/static/assets/`; do not edit generated assets directly.
- `app/defaults/` contains tracked seed configuration. Runtime files under `app/configs/`, `app/.working/`, `app/feed_cache/`, and `data/` are ignored and must not be treated as source.
- `tests/` mirrors application areas; `tests/integration/` contains Docker/Selenium tests and `tests/features/` contains Behave scenarios.
- `notebooks/` is exploratory work with its own `pyproject.toml`; it is not part of the production image.

## Coding conventions

- Follow `.editorconfig`: UTF-8, LF endings, final newline, four-space Python indentation, and two-space YAML/JSON/HTML/CSS/JS indentation.
- Format Python with Black at line length 88; the repository preserves existing string quoting (`skip-string-normalization = true`).
- Sort imports with isort's Black profile and lint with Flake8 as encoded by the Make targets.
- Use snake_case for Python functions, variables, and modules; PascalCase for classes; UPPER_SNAKE_CASE for constants.
- Prefer modern type annotations and specific exceptions. Follow nearby code rather than introducing broad refactors or a new architectural pattern.
- Keep templates, route behavior, API validation, and corresponding tests synchronized.

## Testing guidance

- Put tests under the matching `tests/` area and use descriptive `test_*` names.
- Reuse fixtures from `tests/conftest.py`; the `test_app` fixture injects layout, bookmark manager, and link tracker dependencies through `create_app(..., testing=True)`.
- Mark tests that require external services or containers with `@pytest.mark.integration`.
- Isolate filesystem and environment-dependent behavior with `tmp_path` and `monkeypatch`; avoid writing runtime state into tracked defaults.
- Keep scheduler/background work disabled or mocked in tests that do not explicitly exercise it.

## Security and generated files

- Never read, display, or copy `.env`, `.devcontainer/.env`, credential stores, tokens, webhooks, or other secrets. Use environment-variable names and documented defaults only.
- Do not commit runtime bookmark data, databases, caches, coverage reports, screenshots, or generated CSS assets.
- Do not modify generated dependency/build directories such as `.venv/`, `node_modules/`, `build/`, `dist/`, caches, or `*.egg-info/`.
- Treat user-provided URLs, bookmark imports, and feed content as untrusted input; preserve existing Pydantic validation and output escaping.

## Agent notes

- Inspect the relevant implementation, tests, and applicable files under `.github/instructions/` before editing.
- Some `.github/instructions/` text refers to a different project (Joyride DNS Service). Follow only guidance supported by this repository's code and tooling.
- Do not create unrelated documentation or files. Update documentation when explicitly requested or when a code change would otherwise make existing guidance inaccurate.
- Preserve the user's working tree. Do not clean caches, stop containers, tag, commit, or push unless the task explicitly requires it.
