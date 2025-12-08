# Consolidated Bookmarks PRD

## Summary
Move all bookmark definitions into a single JSON configuration stored at `app/configs/bookmarks.json`, replacing the existing split between `bookmarks_bar.json` and inline bookmark widgets inside `layout.yml`. The application should continue to render the bookmark bar and all bookmark widgets without losing structure while gaining centralised data management.

## Problem Statement
- Bookmark data lives in two places today: the runtime configurable `app/configs/bookmarks_bar.json` and hard-coded lists in `layout.yml`.
- Updating bookmark sets requires editing YAML layout structures, risking schema errors and duplicating data between sections.
- Tests and services assume the old filename (`bookmarks_bar.json`) which will need migration support.

## Goals
- Rename `app/defaults/bookmarks_bar.json` to `app/defaults/bookmarks.json` and mirror the change in `app/configs/`.
- Represent all bookmark collections in the JSON file, including:
  - A dedicated bookmark bar section for the top navigation.
  - Named collections that layout widgets can reference.
- Allow layout widgets to reference bookmark collections symbolically rather than embedding lists inline.
- Preserve backwards compatibility as much as feasible (graceful handling of existing inline widgets during migration).

## Non-Goals
- Redesign of the layout widget schema beyond what is necessary to consume external bookmark collections.
- Visual redesign of templates; only data sourcing changes should be required.
- Build tooling to edit bookmark collections via UI (remains manual config editing).

## Stakeholders & Impact
- **Operators** editing configs get a single source of truth for bookmarks.
- **Developers** gain simpler data model and reduced duplication.
- **Automated tests** need updates to load the new file path and schema.

## Acceptance Criteria
1. `BookmarkBarManager` reads bookmark bar data from `bookmarks.json`.
2. Bookmark widgets defined in `layout.yml` reference named sections provided by the JSON file; runtime resolves those references correctly.
3. Existing tests updated or new tests added to cover the consolidated data flow, including copy-from-default behaviour.
4. Layout loader gracefully handles both legacy inline bookmarks and new section references during migration.
5. Default configuration ships with the newly structured JSON and updated layout referencing it.

## Key Decisions
- Sections expose both a human-readable display name and a unique API-safe key so UI remains friendly while integrations rely on deterministic identifiers.
- Layout-centric presentation attributes such as `multiColumn` stay defined in `layout.yml`; bookmark-specific metadata (for example `openInNewTab` or tags) lives in `bookmarks.json`.
- Legacy inline bookmark arrays in `layout.yml` remain supported when practical, enabling gradual migration for downstream deployments.
- A CLI migration utility will be provided; operators can run it manually and it may be invoked automatically during startup to convert existing configs.
- The initial implementation targets a single locale; multi-locale support will be revisited when a requirement emerges.
