# Implementation Checklist

## ✅ COMPLETED

1. **Config Preparation**
   - [x] Rename `app/defaults/bookmarks_bar.json` → `bookmarks.json` and update `_copy_default_to_configs` flow.
   - [x] Duplicate rename within `app/configs/` while preserving user overrides when present.
   - [x] Restructure JSON to include `bar` (top navigation) and `sections` keyed by API-safe identifiers while storing human-readable `displayName` values.

2. **Loader Enhancements**
   - [x] Extend `BookmarkBarManager` to parse the new schema and expose getters (`bar`, `get_section(name)`).
   - [x] Maintain compatibility with any lingering legacy structure (bookmarks_bar.json fallback).

3. **Layout & Widget Updates**
   - [x] Allow bookmark widgets to declare `bookmarks_section` in addition to legacy inline `bookmarks`.
   - [x] Update `Bookmarks` model to hydrate items from either inline lists or section lookups.
   - [x] Merge bookmark-centric metadata (e.g., `openInNewTab`) from sections while leaving layout-only attributes in YAML.
   - [x] Keep legacy inline bookmark lists working with fallback support.
   - [x] Thread `bookmark_manager` parameter through model hierarchy (Layout → Tab → Row → Column → Widget → Bookmarks).

4. **Config Refactor**
   - [x] Replace inline bookmark lists in `app/configs/layout.yml` with section references (6 widgets).
   - [x] Replace inline bookmark lists in `app/defaults/layout.yml` with section references (7 widgets).
   - [x] Fix nested row bookmark_manager threading in Column.from_dict().

5. **Testing & Validation**
   - [x] Update existing tests to reference `bookmarks.json`.
   - [x] Update test mocks to match new signatures (bookmark_manager parameter).
   - [x] Run full `uv run pytest` suite - **163 passed, 8 deselected**.
   - [x] Validate bookmark loading from sections (all 13 widgets loading correctly).

6. **Deployment Considerations**
   - [x] Created CLI migration utility (`scripts/migrate_bookmarks.py`).
   - [x] Created reusable migration service (`app/services/bookmarks_migrator.py`) with atomic file writes.
   - [x] Documented migration approach in technical design.
