Audit: test-oriented code in `app/`

Checklist

- [x] Find places under `app/` that were added/kept for tests (hooks, fallbacks, DI).
- [x] Note whether each item diverges from parsing the repo `*.yml` files.
- [x] Give a short recommendation/next step for any questionable spots.

Findings (concise)

- `layout.py`
  - `_load_layout_from_file()` — explicit test hook (docstring: "extracted ... so tests can patch it easily"). Purpose: make tests inject a fake layout content without touching files. This is test-oriented but harmless; it does not change YAML semantics — it just exposes the file-read step for patching.

- `apscheduler.py`
  - Test-detection logic and support for injecting a scheduler. Purpose: avoid starting background jobs during tests and allow injecting a fake scheduler. This is test-only infrastructure (expected), not YAML-related parsing.

- `main.py`
  - `_is_test_environment()` checks for pytest / `PYTEST_CURRENT_TEST` / behave and is used to skip eager scheduler startup in tests. Test-only startup behavior; doesn't alter YAML parsing.

- `feed_cache.py` and `local_file_store.py` + `file_store.py`
  - These implement dependency-injectable file-store behaviour. `FeedCache` accepts an injected `file_store` and delegates moves/reads to it so tests can simulate file I/O. `file_store.CacheStore` has no-op/pass methods with a comment about coverage tests. Purpose: test doubles for file I/O. Not a YAML parsing divergence, but an explicit test seam.

- `file_store.py`
  - The prototype/no-op implementations exist so tests/coverage can create lightweight doubles. Test-oriented helper.

- `widget_item.py` and `bookmark.py`
  - `from_dict()` uses `dictionary.get("name")`. This is a normal mapping from layout/bookmark item YAML -> object; not a test-only fallback. (I call it out because `name` vs `tab` confusion has come up elsewhere.)

- `tab.py`
  - Current code uses `dictionary["tab"]` (strict) when constructing a `Tab`. Historically there was a temporary test-driven change to accept `name` as well, but that was reverted by updating tests to match the on-disk YAML. At present `Tab.from_dict` matches the YAML files in `app/defaults` and `app/configs`. So there's no lingering permissive fallback here right now.

- `widget.py`
  - Has logic for building `id` from `link` or `name`. This is part of normal widget parsing and matches layout schemas; not a test-only concession. The `items` getter/setter has been corrected to avoid a test-visible bug (fix is production-correct).

- `main.py` / `inject_current_date()`
  - Small helper used by templates and also exercised in tests (monkeypatching), but it's normal app behavior.

Summary judgement

- There are a handful of explicit test seams (hooks and DI) that were added intentionally for testing:
  - `_load_layout_from_file()` (layout file read patching)
  - scheduler/test-detection and scheduler injection (`apscheduler.py`, `main.py`)
  - file-store DI & prototype (`feed_cache.py`, `file_store.py`, `local_file_store.py`)
- These do not change how the shipped YAML files are parsed; they are test seams to avoid doing real file I/O or starting schedulers in unit tests.
- The one place that caused test/production mismatch historically was `Tab.from_dict` when tests used `"name"` while YAML used `"tab"`; that was resolved by updating the tests to use `"tab"` and reverting the permissive model change. Currently there is no lingering permissive fallback for the `tab` key.

Recommended next steps (optional)

- If you want a strict audit, I can:
  - produce a single diff that documents test seams (comments) and/or centralize them behind a `TEST_SEAM.md`.
  - or convert `_load_layout_from_file()` into a protected method with a standard testing hook (no functional change) and run full tests + lint to confirm.
- If you prefer code to be permissive instead (accept both `tab` and `name`) I can implement a loader-level normalization (map legacy `name` → `tab`) and add a small deprecation log.

Notes

- Preference: keep model code strict (match on-disk YAML) and update tests to match canonical files. Use loader-level normalization only if we need to be backward-compatible for deployed instances.
- Keep file-store DI and scheduler injection — they are useful, low-risk test seams.

