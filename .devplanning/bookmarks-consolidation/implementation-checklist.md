# Implementation Checklist

1. **Config Preparation**
   - [ ] Rename `app/defaults/bookmarks_bar.json` → `bookmarks.json` and update `_copy_default_to_configs` flow.
   - [ ] Duplicate rename within `app/configs/` while preserving user overrides when present.
   - [ ] Restructure JSON to include `bar` (top navigation) and `sections` keyed by API-safe identifiers while storing human-readable `displayName` values.

2. **Loader Enhancements**
   - [ ] Extend `BookmarkBarManager` (or create `BookmarksConfig`) to parse the new schema and expose getters (`bar`, `get_section(name)`).
   - [ ] Maintain compatibility with any lingering legacy structure until migration is complete.

3. **Layout & Widget Updates**
   - [ ] Allow bookmark widgets to declare `bookmarks_section` in addition to legacy inline `bookmarks`.
   - [ ] Update `Bookmarks` model to hydrate items from either inline lists or section lookups.
   - [ ] Merge bookmark-centric metadata (e.g., `openInNewTab`, tags) from sections while leaving layout-only attributes (e.g., `multiColumn`) in YAML.
   - [ ] Keep legacy inline bookmark lists working until downstream deployments migrate.

4. **Config Refactor**
   - [ ] Replace inline bookmark lists in `app/configs/layout.yml` and `app/defaults/layout.yml` with section references.
   - [ ] Ensure corresponding templates render unchanged output after the refactor.

5. **Testing & Validation**
   - [ ] Update existing tests to reference `bookmarks.json`.
   - [ ] Add new unit tests for section hydration and fallback cases.
   - [ ] Run full `uv run pytest` suite and resolve regressions.

6. **Deployment Considerations**
   - [ ] Document steps for downstream environments to migrate custom layout files.
   - [ ] Provide a CLI migration utility that can run manually and optionally during startup to transform legacy layouts into section-based configuration.
