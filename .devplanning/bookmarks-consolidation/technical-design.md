# Technical Design: Consolidated Bookmarks

## Current State
- `BookmarkBarManager` loads a flat list from `configs/bookmarks_bar.json`.
- Bookmark widgets in `layout.yml` include inline `bookmarks` arrays which are parsed into `Bookmark` model instances.
- The layout loader and templates expect widgets to already contain their resolved bookmark data.

## Target Data Model
Store bookmark metadata in a single JSON document located at `app/configs/bookmarks.json` with the following structure:

```jsonc
{
  "bar": [
    // Ordered list rendered in the top bookmark bar
  ],
  "sections": {
    "shopping": {
      "displayName": "Shopping",
      "openInNewTab": true,
      "bookmarks": [ /* bookmarks */ ]
    },
    "ai-tools": {
      "displayName": "AI Tools",
      "bookmarks": [ /* bookmarks */ ]
    }
  }
}
```

### Notes
- Each section is keyed by an API-safe identifier (slug/UUID) while storing a `displayName` for UI rendering.
- `openInNewTab`, tags, and other bookmark-centric metadata remain in `bookmarks.json`; layout-only properties such as `multiColumn` live in `layout.yml`.
- Keep accepting legacy array values temporarily; hydrate them by treating list entries as bookmarks with no additional metadata.

## Application Changes

### 1. Bookmark Configuration Loader
- Introduce a reusable loader (new module or an extension of `BookmarkBarManager`) that reads `bookmarks.json`, validates presence of `bar` and `sections`, and exposes lookups by section name.
- The loader should memoise file contents and expose `mtime` tracking similar to the current manager to support reloads.
- Provide graceful fallbacks when `sections` is missing or malformed (log issue and return empty dict).

### 2. BookmarkBarManager Updates
- Update default file path to `configs/bookmarks.json`.
- Parse the top-level `bar` field to populate the bookmark bar items.
- Expose a helper (`get_section(name)`) that returns the resolved section payload for layout consumers.
- Maintain backwards compatibility by support-loading a flat list if `bar` is not available so deployments can roll forward gradually.

### 3. Layout / Widget Integration
- Extend the bookmark widget schema to allow either:
  - `bookmarks`: inline list (legacy support), or
  - `bookmarks_section`: string referencing a section in `bookmarks.json`.
- Modify `app/models/bookmarks.py` to detect the section reference. When present, request the data from `BookmarkBarManager` (or the new loader) and hydrate `Bookmark` models from that data.
- Merge bookmark metadata (e.g., `openInNewTab`, tags) from the section into the widget; continue sourcing layout-centric structure such as `multiColumn` from `layout.yml`.

### 4. Layout Configuration
- Refactor `app/configs/layout.yml` and corresponding defaults so bookmark widgets reference sections rather than embedding bookmark lists.
- Preserve `multiColumn` and other layout-only attributes in the YAML while ensuring templates consume bookmark metadata supplied via the service.

### 5. Default File Copy Utility
- Update `_copy_default_to_configs` to account for the renamed JSON file. It already copies unknown files generically; ensure rename logic handles the transition gracefully, possibly by deleting stale `bookmarks_bar.json` when `bookmarks.json` exists.

### 6. Tests
- Update unit tests in `tests/services/test_bookmark_and_favicon.py` and `tests/app/test_copy_default_to_configs.py` to point at the new filename and schema.
- Add new tests for:
  - Section lookup behaviour.
  - Bookmark widget hydration via section reference.
  - Backwards compatibility for inline bookmark lists.

## Migration Strategy
1. Introduce loader changes with support for both old (`bookmarks_bar.json`) and new (`bookmarks.json`) filenames.
2. Provide a CLI migration utility (invokable manually or during startup) to transform existing layout bookmark lists into section definitions inside the new JSON file.
3. Once downstream configs are updated, remove fallback logic for the old filename in a future clean-up (optional).

## Risks & Mitigations
- **Risk:** Layout widgets may rely on inline attributes that need to be preserved when moving into JSON sections.
  - *Mitigation:* Allow section entries to store structured objects (not just bookmark arrays) and merge metadata at hydration time.
- **Risk:** Large JSON file could become unwieldy.
  - *Mitigation:* Document recommended organisation (alphabetical sections, nested categories) and consider tooling later.
- **Risk:** Existing tests or scripts referencing `bookmarks_bar.json` fail.
  - *Mitigation:* Search and update all references; add regression tests to catch future renames.
