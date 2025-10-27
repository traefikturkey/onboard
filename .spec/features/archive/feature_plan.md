```markdown
Feature Plan: Layout & Feed robustness, test seams, and baseline

Summary
- Goal: make layout parsing and feed processing robust in production images (no native deps), preserve canonical YAML semantics, keep test seams for safe unit testing, and provide a clear migration path where necessary.

Contract (inputs/outputs/error modes)
- Inputs: YAML layout files under `app/configs/layout.yml` and `app/defaults/layout.yml`; runtime env vars; feed URLs.
- Outputs: stable in-memory `Layout`/`Tab`/`Widget` model instances, feed cache files, server-rendered pages and HTMX fragments.
- Errors: missing cache files, missing parser libs, malformed pub_date, scheduler not started in tests.

High-level tasks
- [ ] Audit and document existing test seams (file-store, scheduler, layout loader). (small)
- [ ] Normalize loader boundary (optionally add a non-destructive normalization step) to map legacy keys if required and log deprecations. (medium)
- [ ] Keep `Tab.from_dict` strict to canonical `tab` key; update any tests that use legacy keys. (small)
- [ ] Ensure BeautifulSoup uses built-in parser (`html.parser`) by default; keep a configuration toggle if callers want lxml. (small)
- [ ] Harden feed cache load/save: defensive pub_date parsing and clear failure modes. (small)
- [ ] Maintain file-store DI for tests; document the interface in `app/models/file_store.py`. (small)
- [ ] Keep scheduler startup behavior test-aware; document the detection heuristics. (small)
- [ ] Add tests: loader normalization (if implemented), feed parsing fallback, empty-cache flow, scheduler injection. (medium)
- [ ] CI: run `make lint` and `make test` before merging; add a targeted smoke test for production-like minimal image (no lxml). (medium)

Edge cases
- Empty or missing cache dir on fresh containers.
- Feeds with malformed/missing dates.
- Layout YAML with unexpected/legacy keys.
- Running in CI where env detection may be different.

Quality gates
- Lint passes (make lint) ✅
- Unit tests + integration tests pass (make test) ✅
- Manual smoke: run app in minimal environment (no lxml) and request a feed endpoint. ✅

Deliverables / artifacts
- `.spec/feature_plan.md` (this file)
- Small PRs (one per change):
  - parser fallback & tests
  - loader normalization or test updates
  - feed cache defensive parsing + tests
  - docs and README updates

Timeline (rough)
- Day 0: baseline commit + audit and tests adjustments
- Day 1-2: parser + cache hardening + tests
- Day 3: loader normalization (if chosen) + tests
- Day 4: run full CI, address issues, merge

Notes
- Preference: keep model code strict (match on-disk YAML) and update tests to match canonical files. Use loader-level normalization only if we need to be backward-compatible for deployed instances.
- Keep file-store DI and scheduler injection — they are useful, low-risk test seams.

Next steps (immediate)
- Commit this plan as a baseline.
- Run full `make lint` + `make test` to confirm baseline health.

```
