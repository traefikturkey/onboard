# Bookmark Management UI - Product Requirements Document

## Executive Summary

Create a web-based interface for managing `app/configs/bookmarks.json` that allows users to:
- View, add, edit, and delete bookmarks in the bookmark bar
- Manage bookmark sections (folders)
- Organize bookmarks with drag-and-drop
- Edit bookmark metadata (name, URL, favicon, display options)
- Support nested folder structures
- Provide real-time preview of changes

## Goals

### Primary Goals
1. Enable users to manage bookmarks without manually editing JSON files
2. Provide intuitive CRUD operations for bookmarks and sections
3. Support the existing bookmark structure (bar + sections)
4. Ensure changes persist atomically to prevent data corruption

### Secondary Goals
1. Add drag-and-drop reordering capabilities
2. Provide visual feedback and validation
3. Support bulk operations (multi-select, batch delete)
4. Enable bookmark import/export functionality

### Future Goals (Chrome Extension Integration)
1. REST API for programmatic bookmark management
2. Authentication and authorization
3. Real-time sync across devices
4. Version history and rollback

## User Stories

### As a User, I want to:
1. **View** all bookmarks organized by bar and sections
2. **Add** new bookmarks to the bar or any section
3. **Edit** bookmark properties (name, URL, favicon path, metadata)
4. **Delete** bookmarks individually or in bulk
5. **Reorder** bookmarks via drag-and-drop
6. **Create** new sections with custom names
7. **Rename** existing sections
8. **Move** bookmarks between bar and sections
9. **Nest** folders (bookmarks with contents) within sections
10. **Preview** changes before saving
11. **Export** bookmarks to JSON file
12. **Import** bookmarks from JSON file

## Technical Requirements

### Architecture

#### Frontend
- **Framework**: Alpine.js (already used in the app) or HTMX for reactive UI
- **CSS**: Tailwind CSS or existing app styles
- **Drag-and-Drop**: SortableJS or native HTML5 drag-and-drop
- **Icons**: Use existing favicon system

#### Backend
- **Framework**: Flask (existing)
- **Routes**: RESTful API endpoints for bookmark operations
- **Validation**: Pydantic models for request/response validation
- **Atomic Writes**: Use existing `LocalFileStore.write_json_atomic()`

### Data Model (Existing)

```json
{
  "bar": [
    {
      "name": "Gmail",
      "href": "https://mail.google.com/",
      "favicon": "/static/assets/icons/google.com.favicon.ico",
      "add_date": "1587496250"
    },
    {
      "name": "Folder Name",
      "multiColumn": 2,
      "openInNewTab": true,
      "contents": [...]
    }
  ],
  "sections": {
    "section_id": {
      "displayName": "Section Title",
      "bookmarks": [
        {
          "name": "Bookmark Name",
          "link": "https://example.com/"
        }
      ]
    }
  }
}
```

## API Design

### REST Endpoints

#### Bookmarks Bar Operations

```
GET    /api/bookmarks/bar                    - List all bar bookmarks
POST   /api/bookmarks/bar                    - Add bookmark to bar
GET    /api/bookmarks/bar/{index}            - Get specific bar bookmark
PUT    /api/bookmarks/bar/{index}            - Update bar bookmark
DELETE /api/bookmarks/bar/{index}            - Delete bar bookmark
POST   /api/bookmarks/bar/reorder            - Reorder bar bookmarks
```

#### Section Operations

```
GET    /api/bookmarks/sections               - List all sections
POST   /api/bookmarks/sections               - Create new section
GET    /api/bookmarks/sections/{section_id}  - Get section details
PUT    /api/bookmarks/sections/{section_id}  - Update section
DELETE /api/bookmarks/sections/{section_id}  - Delete section
```

#### Section Bookmark Operations

```
GET    /api/bookmarks/sections/{section_id}/bookmarks              - List section bookmarks
POST   /api/bookmarks/sections/{section_id}/bookmarks              - Add bookmark to section
PUT    /api/bookmarks/sections/{section_id}/bookmarks/{index}      - Update section bookmark
DELETE /api/bookmarks/sections/{section_id}/bookmarks/{index}      - Delete section bookmark
POST   /api/bookmarks/sections/{section_id}/bookmarks/reorder      - Reorder section bookmarks
```

#### Bulk Operations

```
POST   /api/bookmarks/move                   - Move bookmark(s) between bar/sections
POST   /api/bookmarks/import                 - Import bookmarks from JSON
GET    /api/bookmarks/export                 - Export bookmarks as JSON
POST   /api/bookmarks/validate               - Validate bookmark data
```

#### Management UI

```
GET    /bookmarks/manage                     - Main bookmark management page
```

### Request/Response Models

#### Bookmark Model (Request)
```json
{
  "name": "Gmail",
  "href": "https://mail.google.com/",
  "favicon": "/static/assets/icons/google.com.favicon.ico",
  "add_date": "1587496250",
  "multiColumn": 2,           // Optional: for folders
  "openInNewTab": true,       // Optional: for folders
  "contents": []              // Optional: nested bookmarks
}
```

#### Section Model (Request)
```json
{
  "section_id": "shopping",
  "displayName": "Shopping",
  "bookmarks": [...]
}
```

#### Move Operation (Request)
```json
{
  "source": {
    "type": "bar",            // or "section"
    "section_id": null,       // if type is "section"
    "index": 0
  },
  "destination": {
    "type": "section",
    "section_id": "shopping",
    "index": 2
  }
}
```

#### Reorder Operation (Request)
```json
{
  "indices": [3, 0, 1, 2, 4]  // New order by original indices
}
```

## UI/UX Design

### Page Layout

```
┌─────────────────────────────────────────────────────────┐
│ Bookmark Manager                            [Import] [Export]
├─────────────────────────────────────────────────────────┤
│ ┌───────────────┬─────────────────────────────────────┐ │
│ │               │                                     │ │
│ │  Navigation   │  Content Area                       │ │
│ │               │                                     │ │
│ │  • Bar        │  [+ Add Bookmark]                   │ │
│ │  • Sections   │                                     │ │
│ │    - Shopping │  ┌──────────────────────────────┐  │ │
│ │    - AI       │  │ Gmail                   [✎][✕]│  │ │
│ │    - Tools    │  │ https://mail.google.com       │  │ │
│ │    ...        │  └──────────────────────────────┘  │ │
│ │               │                                     │ │
│ │  [+ Section]  │  ┌──────────────────────────────┐  │ │
│ │               │  │ Links (Folder)          [✎][✕]│  │ │
│ │               │  │ ➤ 15 bookmarks                │  │ │
│ │               │  └──────────────────────────────┘  │ │
│ │               │                                     │ │
│ └───────────────┴─────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Key UI Components

1. **Navigation Panel**
   - Tree view of bar and sections
   - Click to switch context
   - Add section button

2. **Content Area**
   - List of bookmarks in current context
   - Each bookmark has edit/delete buttons
   - Drag handles for reordering
   - Add bookmark button at top

3. **Bookmark Card**
   - Display name, URL, favicon
   - Show metadata (multiColumn, openInNewTab)
   - Expand/collapse nested contents
   - Edit/delete actions

4. **Edit Modal**
   - Form with fields: name, href, favicon, add_date
   - Folder-specific: multiColumn, openInNewTab
   - Nested contents editor
   - Save/Cancel buttons
   - Real-time validation

5. **Add Modal**
   - Similar to edit modal
   - Choose destination (bar or section)
   - Auto-fetch favicon option

6. **Import/Export**
   - File upload for import
   - JSON download for export
   - Validation feedback

## Implementation Phases

### Phase 1: Backend API Foundation (Current Focus)
- [ ] Create bookmark management service (`BookmarkManager`)
- [ ] Implement bar CRUD endpoints
- [ ] Implement section CRUD endpoints
- [ ] Add request/response validation with Pydantic
- [ ] Implement atomic save with rollback on error
- [ ] Add comprehensive error handling
- [ ] Write unit tests for all endpoints

### Phase 2: Basic UI
- [ ] Create bookmark management page template
- [ ] Implement navigation panel
- [ ] Add bookmark list view
- [ ] Create add/edit/delete modals
- [ ] Implement form validation
- [ ] Add success/error notifications
- [ ] Test basic CRUD operations

### Phase 3: Advanced Features
- [ ] Implement drag-and-drop reordering
- [ ] Add bulk operations (multi-select)
- [ ] Implement move between bar/sections
- [ ] Add nested folder editing
- [ ] Create import/export functionality
- [ ] Add search and filtering

### Phase 4: Polish & UX
- [ ] Add loading states and animations
- [ ] Implement undo/redo functionality
- [ ] Add keyboard shortcuts
- [ ] Improve error messages and validation
- [ ] Add confirmation dialogs for destructive actions
- [ ] Implement auto-save with change detection

### Phase 5: Chrome Extension Preparation
- [ ] Add authentication system
- [ ] Implement API token generation
- [ ] Add CORS configuration
- [ ] Create API documentation
- [ ] Implement rate limiting
- [ ] Add version history tracking

## Technical Considerations

### Security
- **Input Validation**: Sanitize all user input to prevent XSS
- **URL Validation**: Ensure URLs are properly formatted
- **Path Validation**: Prevent directory traversal in favicon paths
- **Authentication**: Add auth before exposing to internet
- **CSRF Protection**: Use Flask-WTF for form protection

### Performance
- **Lazy Loading**: Load nested folders on demand
- **Debouncing**: Debounce search and auto-save operations
- **Caching**: Cache bookmark data in frontend
- **Optimistic Updates**: Update UI before server confirmation

### Error Handling
- **Validation Errors**: Show inline field errors
- **Network Errors**: Retry with exponential backoff
- **Conflict Resolution**: Handle concurrent edits
- **Rollback**: Revert changes on save failure

### Testing
- **Unit Tests**: Test all API endpoints and services
- **Integration Tests**: Test full CRUD workflows
- **E2E Tests**: Test UI interactions with Selenium
- **Load Tests**: Ensure performance with large bookmark sets

## Success Metrics

### MVP Success Criteria
- [ ] Users can add, edit, delete bookmarks without editing JSON
- [ ] Changes persist correctly to `bookmarks.json`
- [ ] No data corruption or loss during operations
- [ ] All CRUD operations complete in < 500ms

### Phase 2+ Success Criteria
- [ ] Drag-and-drop reordering works smoothly
- [ ] Import/export preserves all bookmark data
- [ ] UI is responsive and intuitive
- [ ] Users prefer UI over manual JSON editing

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Data corruption during save | High | Use atomic writes, add validation, create backups |
| Concurrent edits conflict | Medium | Add optimistic locking, last-write-wins with warning |
| Large bookmark sets slow | Medium | Implement pagination, lazy loading, virtualization |
| Complex nested folders hard to edit | Medium | Provide tree view, breadcrumbs, search functionality |
| Favicon management complex | Low | Auto-fetch favicons, provide URL templates |

## Dependencies

- Flask (existing)
- Alpine.js or HTMX (for reactive UI)
- SortableJS (for drag-and-drop)
- Pydantic (for validation)
- LocalFileStore (existing atomic writes)

## Timeline Estimate

- **Phase 1 (Backend API)**: 3-5 days
- **Phase 2 (Basic UI)**: 4-6 days
- **Phase 3 (Advanced Features)**: 5-7 days
- **Phase 4 (Polish & UX)**: 3-4 days
- **Phase 5 (Extension Prep)**: 4-6 days

**Total Estimate**: 19-28 days (3-5 weeks)

## Open Questions

1. Should we support bookmark tags/categories in addition to sections?
2. Do we need version history and rollback functionality?
3. Should we auto-fetch favicons when adding new bookmarks?
4. Do we need a "preview mode" before saving changes?
5. Should we support exporting to Chrome bookmark format?
6. Do we need collaborative editing features?

## References

- Existing bookmark structure in `app/defaults/bookmarks.json`
- BookmarkBarManager service: `app/services/bookmark_bar_manager.py`
- Atomic file writes: `app/models/local_file_store.py`
- Current Flask routes: `app/main.py`
