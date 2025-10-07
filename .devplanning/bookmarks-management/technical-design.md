# Technical Design

## Overview
Leverage `bookmarks.json` introduced by the consolidation work. Implement a `BookmarksService` that provides CRUD over this file with atomic writes and validation. Expose Flask routes for UI and API consumption. Use the existing `BookmarkBarManager` or replace it with `BookmarksService` that also feeds the layout.

## Components

- BookmarksService (new)
  - load(): read and parse `bookmarks.json` { bar, sections }
  - save(data): write atomically with file lock
  - get_bar(), add_to_bar(), update_bar(), delete_from_bar(), reorder_bar()
  - list_sections(), create_section(), get_section(), update_section(), delete_section()
  - add_bookmark(section), update_bookmark(section, id), delete_bookmark(section, id), reorder(section)
  - generate IDs (uuid4), set add_date, normalize favicon via FaviconStore

- Flask Blueprint `bookmarks_api` (new)
  - Implements endpoints defined in API Design (v1)
  - Token auth via env var `ONBOARD_API_TOKEN`; simple decorator

- Flask Views `bookmarks_ui` (new)
  - Server-rendered HTML with HTMX for partials and modals
  - Routes under `/bookmarks/*`

- Integration with Layout
  - Layout and `Bookmarks` widget updated to read sections via service
  - Changes reflect live via mtime/watch driven by service

## Data Validation
- JSON schema for bookmarks.json; validate on save
- URL format check (urllib.parse), max lengths, allowed fields

## Concurrency & Atomicity
- File lock (fcntl or portalocker) around read-modify-write
- Write to temp file + fsync + rename

## Phase Plan
- Phase 1: CRUD Service, UI (basic), API (create only), wire into layout
- Phase 2: Full API (update/delete/reorder), better UI (drag-and-drop), import/export
- Phase 3: Auto-tagging pipeline
  - Strategy: on create/update, enqueue job -> tagger fetches URL, extracts content → classifies/tags
  - Pluggable taggers: local TF-IDF/keywords, external APIs (OpenRouter, etc.)
  - Store tags in bookmark objects; expose filter/search by tags
