# Bookmarks Management PRD

## Summary
Deliver an in-app web UI to add/edit/delete/manage bookmarks and sections; expose a REST API so a Chrome extension can add bookmarks on-the-fly while browsing; and plan a follow-up phase for automatic tagging similar to KaraKeep.

## Goals
- CRUD UI inside the app for bookmarks and sections (collections) stored in `app/configs/bookmarks.json`.
- REST API for creating/updating/deleting bookmarks and sections.
- Permissions and simple auth suitable for extension access (token-based).
- Import/export helpers for backup/migration.
- Phase 3: automatic tagging on create/update (background task) with configurable providers.

## Non-Goals
- OAuth SSO or complex multi-user permissions (initially single-tenant with token).
- Full-text search indexing (basic filter/search in-memory for now).
- Browser extension implementation (only the API to enable it).

## Success Criteria
1. Users can create/update/delete bookmarks through a UI, and the changes persist to `bookmarks.json`.
2. The top bar and bookmark widgets update to reflect changes without server restart.
3. API endpoints are documented and stable (v1) and accept a token header.
4. Unit tests cover API and file persistence edge cases.
5. Phase 3 plan documented with clear interface for pluggable taggers.

## Key Use Cases
- Add a new bookmark to an existing section.
- Create a new section and add multiple bookmarks.
- Edit bookmark name/link/favicon and reorder.
- Delete a bookmark and empty sections safely.
- Chrome extension posts the current tab URL/title into a chosen section.
- Automatic tagging enriches the bookmark with tags based on content and metadata.

## Constraints
- Single-writer semantics for `bookmarks.json`; prevent corruption on concurrent writes.
- Must maintain backward compatibility with existing layout rendering.

## Risks
- Race conditions during writes → use atomic file writes (temp file + rename) and a lock.
- Schema drift → add JSON schema validation and migration helpers.
- Tagging latency → offload to background scheduler job, show pending state.
