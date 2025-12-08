# API Design (v1)

Base Path: `/api/v1/bookmarks`
Auth: `Authorization: Bearer <TOKEN>` (config-driven token; optional IP allowlist)
Content-Type: `application/json`

## Models
- Bookmark
  - id: string (sha1 of link or server-generated UUID)
  - name: string
  - link: string (URL)
  - favicon: string (optional; server may compute)
  - tags: string[] (optional)
  - add_date: number (epoch seconds; server sets default)
- Section
  - name: string (unique key)
  - multiColumn: number (optional)
  - openInNewTab: boolean (optional)
  - bookmarks: Bookmark[]

## Endpoints

- GET `/api/v1/bookmarks/health` → 200 OK with status
- GET `/api/v1/bookmarks` → `{ bar: Bookmark[], sections: Record<string, Section|Bookmark[]> }`
- PUT `/api/v1/bookmarks` → replace entire config (admin only)

- GET `/api/v1/bookmarks/bar` → Bookmark[]
- POST `/api/v1/bookmarks/bar` → add to bar (body: BookmarkInput)
- DELETE `/api/v1/bookmarks/bar/:id` → remove from bar
- PATCH `/api/v1/bookmarks/bar/:id` → update
- POST `/api/v1/bookmarks/bar/reorder` → body: { order: string[] }

- GET `/api/v1/bookmarks/sections` → string[]
- POST `/api/v1/bookmarks/sections` → create (body: { name, meta? })
- GET `/api/v1/bookmarks/sections/:name` → Section
- DELETE `/api/v1/bookmarks/sections/:name` → delete (optional cascade flag)
- PATCH `/api/v1/bookmarks/sections/:name` → update metadata/rename

- POST `/api/v1/bookmarks/sections/:name/bookmarks` → add (BookmarkInput)
- PATCH `/api/v1/bookmarks/sections/:name/bookmarks/:id` → update
- DELETE `/api/v1/bookmarks/sections/:name/bookmarks/:id` → remove
- POST `/api/v1/bookmarks/sections/:name/reorder` → { order: string[] }

## Errors
- 400 validation_error
- 401 unauthorized
- 404 not_found
- 409 conflict (duplicate names, id collisions)
- 422 unprocessable_entity

## Notes
- ID strategy: prefer UUIDv4 to avoid collisions, derive hash as fallback.
- Atomic writes with temp file then rename, guarded by file lock.
- ETags / If-Match optional for optimistic concurrency in future.
