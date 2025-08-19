Test seams in `app/`

This document records the intentional test seams used by the application so
maintainers understand why they exist and how to use them safely.

Key seams

- `Layout._load_layout_from_file()` — read helper that tests patch to inject layout dicts.
- `Layout._normalize_layout_content()` — normalization layer (added) that maps legacy `name` -> `tab`.
- `apscheduler.Scheduler` — provides test-detection and allows injecting a mock scheduler to avoid starting background jobs in tests.
- `FeedCache.file_store` → `CacheStore` prototype — allows swapping file I/O for an in-memory test double.

Guidance

- Keep model-level parsers strict (e.g., `Tab.from_dict` expects `tab`). Use loader normalization only when backward compatibility is required.
- When adding seams, prefer dependency injection rather than global state.
- Document seams here and include a small unit test showing how to patch or inject the replacement.
