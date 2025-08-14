# Feature: Extract Feed cache into `FeedCache` and integrate archive-on-load

## Goal

- Move cache responsibilities out of `app/models/feed.py` into a small, testable `FeedCache` class (composition).
- Merge the existing `Startup.archive_large_jsons()` behavior into the cache-loading lifecycle so large cache files are archived on load (subject to existing testing/scheduler guards).

**Important:**
- Before marking any test step complete, always run `make test` and resolve all errors, failures, and warnings. Only check off a step when the code and tests are fully passing and clean.
- After running `make test`, update the checklist in this file (change `[ ]` to `[x]` for the step).
- Do not proceed to the next step until both actions are done and confirmed.
- If any required action is skipped, go back and complete it before continuing.

**Testing Requirements:**
- **Code Coverage:** Aim for 90%+ test coverage for each class/module being tested
- **Test Quality:** All tests must pass without errors, failures, or warnings
- **Verification:** Run `make test` successfully before marking any step complete
- **Coverage Verification:** Use `uv run pytest tests/path/to/test_file.py --cov=module.path --cov-report=term-missing -v` to verify coverage targets

## Phases

### Phase 1 — Design & Unit tests

1. [x] Create `SchedulerInterface` abstraction
   - Define `app/models/scheduler_interface.py` with abstract base class or protocol
   - Methods: `add_job(...)`, `remove_job(job_id)`, `modify_job(job_id, ...)`
   - Properties: `running: bool`

2. [x] Implement `APSchedulerScheduler` concrete implementation
   - Create `app/models/apscheduler_scheduler.py` implementing `SchedulerInterface`
   - Wrap existing `app/models/scheduler.py` internals or use APScheduler directly
   - Ensure backward compatibility with current scheduler usage

3. [x] Implement `MockScheduler` for testing
   - Create `tests/mocks/mock_scheduler.py` implementing `SchedulerInterface`
   - Record method calls, never start background threads
   - Provide assertion helpers for testing schedule registration

4. [x] Create `FileStore` abstraction
   - Define `app/models/file_store.py` with abstract base class or protocol
   - Methods: `read_json(path: Path) -> dict`, `write_json_atomic(path: Path, data: dict)`, `list_dir(path: Path) -> List[Path]`, `move(src: Path, dst: Path)`

5. [x] Implement `LocalFileStore` concrete implementation
   - Create `app/models/local_file_store.py` implementing `FileStore`
   - Use real filesystem operations (open/json/os.replace/shutil.move)

6. [x] Implement `InMemoryFileStore` for testing
   - Create `tests/mocks/in_memory_file_store.py` implementing `FileStore`
   - Simulate files in memory with configurable sizes for testing `archive_large_jsons`
   - Support corrupt JSON simulation for error case testing

7. [x] Implement `FeedCache` API and core behavior, and add comprehensive unit tests in `tests/models/test_feed_cache.py`.

    - Update `FeedCache` constructor: `FeedCache(feed_id: str, working_dir: Optional[Path] = None, file_store: Optional[FileStore] = None)`
    - Use injected `file_store` for all file operations (defaults to `LocalFileStore`)
    - Unit tests (pure unit tests using mocks):
       - `test_load_creates_cache_dir_and_returns_empty_when_missing`
       - `test_save_and_load_roundtrip`
       - `test_archive_large_jsons_moves_large_files`
       - `test_load_handles_corrupt_json_gracefully`
       - `test_archive_on_load_behavior_exposed_via_FeedCache` (unit test: ensure archive-on-load can be enabled/disabled via parameter)
       - `test_scheduler_registration_for_archiving` (unit test: mock `Scheduler`/`MockScheduler` to assert any job registration behavior is performed by the application wiring, not by `Startup`)

    - Acceptance criteria:
       - Atomic writes implemented using temp-file + `os.replace()` (or `Path.replace`) for `save_articles`.
       - `archive_on_load` flag implemented and unit-testable; tests should disable it via env or parameter to avoid side-effects.
       - `FeedCache.load_cache()` returns raw serializable article dicts (no `FeedArticle` conversion).
       - Tests use `MockScheduler` and `InMemoryFileStore` for deterministic behavior — no real scheduler or filesystem interactions.
       - Note: `Startup` will be removed at the end of this refactor — its archive and scheduling responsibilities are intended to be migrated into `FeedCache` or into application startup wiring. Tests should target `FeedCache` and the application-level wiring rather than `Startup` itself.

### Phase 2 — Integration

1. [ ] Integrate `FeedCache` into `Feed`
   - Update `app/models/feed.py` to instantiate `self.feed_cache = FeedCache(self.id)`
   - Keep `Feed` responsible for business logic: converting dict -> `FeedArticle`, dedupe, processors, sorting
   - Replace file-IO in `Feed` with calls to `FeedCache.load_cache()` and `FeedCache.save_articles()` as appropriate
2. [ ] Remove legacy `Startup` and migrate responsibilities
   - Remove or deprecate `app/startup.py` once its responsibilities are fully migrated.
   - Migrate `Startup.archive_large_jsons()` behavior into `FeedCache.archive_large_jsons()` (already done) and ensure any remaining scheduling/registration logic is moved into application startup wiring that uses `MockScheduler`/`SchedulerInterface` for tests.
   - Update or remove tests that assert behavior on `Startup`; instead, test the new application wiring or `FeedCache` directly.
   - cleanup and remove all old code and files that are no longer used

### Phase 3 — Testing & QA

1. [ ] Implement integration tests and validate behaviors
   - Integration test: `tests/models/test_feed_integration.py` verifying `Feed` uses `FeedCache` and preserves dedupe/processor behavior.
   - End-to-end validation that archive-on-load works correctly in production-like scenarios.

### Phase 4 — Review & Refinements

1. [ ] Code review and small improvements
   - Add optional locking if concurrent writers are observed (future)
   - Improve logging and error messages
   - Consider performance (batch writes, caching) if needed

### Phase 5 — Documentation & Rollout

1. [ ] Documentation & rollout
   - Add short note to `.devplanning/feature-feed-cache/README.md` or update `README.md` describing `WORKING_STORAGE`, archive-on-load behavior, and any operational guidance
   - Merge during a quiet window; recommend backing up `cache/` before first rollout in production

## Contract (API surface)

**Interfaces:**
- SchedulerInterface
  - Methods: `add_job(...)`, `remove_job(job_id)`, `modify_job(job_id, ...)`
  - Properties: `running: bool`
- FileStore
  - Methods: `read_json(path: Path) -> dict`, `write_json_atomic(path: Path, data: dict)`, `list_dir(path: Path) -> List[Path]`, `move(src: Path, dst: Path)`

**Classes:**
- FeedCache(feed_id: str, working_dir: Optional[Path] = None, file_store: Optional[FileStore] = None)
  - Attributes:
    - `cache_dir: Path` (folder where cache files and archive live)
    - `cache_path: Path` (file for this feed's cache)
  - Methods:
    - `load_cache(archive_on_load: bool = True) -> list[dict]` — returns serializable article dicts; archives large files before loading when enabled
    - `save_articles(articles: list) -> list` — writes JSON atomically and returns saved list
    - `archive_large_jsons(min_size_bytes: int = 300*1024) -> list[Path]` — moves large `.json` files into `archive-YYYY-MM-DD` folder

## Edge cases & decisions

- Testing: Do not archive on load in tests. Tests will set `ONBOARD_DISABLE_SCHEDULER=True` and/or `FLASK_ENV=testing` during imports.
- Concurrency: initial implementation will mirror existing behaviour (no locking). We will implement atomic write (temp file + rename/replace) for save to reduce corruption risk.
- Error handling: keep current Feed behavior — log exceptions when reading/parsing cache and return an empty list.

## Quality gates

- All tests pass locally with `make test`.
- Lint/type-check passes (project linters/typing as applicable).
- New unit tests added for `FeedCache`, `SchedulerInterface`, and `FileStore` (happy path + error cases + archive behavior).
- No accidental scheduler registration or filesystem side-effects in unit tests (use `MockScheduler` and `InMemoryFileStore`).

## Rollback and manual remediation notes

- The archive behavior moves large files into `cache/archive-YYYY-MM-DD/` (where `cache` is the `cache_dir` next to `WORKING_STORAGE` value). If merged during production, provide a short mitigation doc:
  - Dry-run first in staging: set `ONBOARD_DISABLE_SCHEDULER=True` and run a small script which calls `Startup.archive_large_jsons(min_size_bytes=...)` to validate.
  - To rollback: move files back from the archive folder(s), e.g.:

    ```sh
    # Example: move files from archive back into cache
    mv cache/archive-2025-08-14/*.json cache/
    ```

  - Keep backups of `cache/` before first rollout if the data is critical.

## Timeline estimate (rough)

- Phase 1: Design & unit tests: 2–3 hours
- Phase 2: Integration: 1–2 hours
- Phase 3: Testing & QA: 1 hour
- Phase 4–5: Review & rollout: 1 hour
- Total: ~5–7 hours depending on edge-case fixes and review feedback

## Next step

- I can implement the IoC abstractions, update `FeedCache` to use them, and add unit tests. Reply with "Implement" to proceed or "Patch only" to produce the diffs without running tests.




