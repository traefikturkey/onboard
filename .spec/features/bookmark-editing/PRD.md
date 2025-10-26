# Bookmark Editing Feature - Product Requirements Document

## Overview

Implement a comprehensive bookmark editing system that mimics Chrome's bookmark bar workflow, providing users with intuitive browser-like bookmark management directly within the onboard application.

## Current State Analysis

### Existing Implementation
- **Data Storage**: JSON file at `app/configs/bookmarks_bar.json`
- **Models**: `Bookmark` and `Bookmarks` classes with hierarchical structure
- **Display**: Recursive template rendering with folder support
- **Styling**: Chrome-like appearance with hover effects and favicons
- **Management**: `BookmarkBarManager` service for loading and reloading

### Data Structure
```json
[
  {
    "name": "Gmail",
    "href": "https://mail.google.com/mail/u/0/#inbox", 
    "favicon": "/static/assets/icons/google.com.favicon.ico",
    "add_date": "1587496250"
  },
  {
    "name": "Links",
    "contents": [
      {
        "name": "Subfolder",
        "contents": [...]
      }
    ]
  }
]
```

## Goals

### Primary Goals
1. **Chrome-like UX**: Replicate Chrome's bookmark management experience
2. **In-place Editing**: Edit bookmarks directly in the bookmark bar
3. **Drag & Drop**: Reorganize bookmarks and folders via dragging
4. **Context Menus**: Right-click menus for quick actions
5. **Real-time Updates**: Immediate visual feedback without page refresh

### Secondary Goals
1. **Bulk Operations**: Select multiple bookmarks for batch operations
2. **Import/Export**: Support Chrome bookmark imports
3. **Search**: Find bookmarks by name or URL
4. **Keyboard Shortcuts**: Power user navigation

## User Stories

### Core User Stories

**As a user, I want to:**

1. **Add Bookmarks**
   - Right-click in bookmark bar → "Add Bookmark"
   - Ctrl+D to bookmark current page
   - Quick-add via URL paste

2. **Edit Bookmarks**
   - Right-click bookmark → "Edit"
   - Click bookmark name to inline edit
   - Edit name, URL, and folder location

3. **Organize Bookmarks**
   - Drag bookmark to reorder
   - Drag bookmark onto folder to move
   - Create new folders via right-click

4. **Delete Bookmarks**
   - Right-click → "Delete"
   - Delete key after selection
   - Confirm deletion for folders with contents

5. **Manage Folders**
   - Create nested folder structures
   - Rename folders inline
   - Move folders and their contents

### Advanced User Stories

**As a power user, I want to:**

1. **Batch Operations**
   - Select multiple bookmarks (Ctrl+click)
   - Move multiple items to folder
   - Delete multiple bookmarks

2. **Quick Access**
   - Search bookmarks with Ctrl+F
   - Keyboard navigation (arrow keys)
   - Quick folder collapse/expand

## Success Criteria

### Must Have
- [ ] Add new bookmarks via right-click menu
- [ ] Edit bookmark name and URL inline
- [ ] Delete bookmarks with confirmation
- [ ] Create and manage folders
- [ ] Drag and drop reorganization
- [ ] Data persistence to JSON file
- [ ] Real-time UI updates

### Should Have  
- [ ] Keyboard shortcuts (Ctrl+D, Delete, etc.)
- [ ] Undo last action
- [ ] Duplicate bookmark detection
- [ ] Bulk selection and operations

### Nice to Have
- [ ] Chrome bookmark import
- [ ] Bookmark search functionality
- [ ] Export bookmarks to file
- [ ] Bookmark validation (check broken links)

## Technical Constraints

### Existing Architecture
- Must work with current Flask/Jinja2 setup
- Preserve existing bookmark bar styling
- Maintain JSON file structure compatibility
- Work with current `BookmarkBarManager` service

### Browser Compatibility
- Support modern browsers (Chrome, Firefox, Safari, Edge)
- Graceful degradation for JavaScript-disabled browsers
- Mobile-responsive design

### Performance
- Smooth drag and drop experience
- Immediate UI feedback (<100ms)
- Efficient JSON file updates
- Minimal JavaScript bundle size

## Non-Goals

- Social bookmark sharing
- Cloud synchronization
- Bookmark analytics/usage tracking
- Advanced bookmark metadata (tags, descriptions)
- Integration with external bookmark services

## Risks and Mitigation

### Technical Risks
1. **Data Loss**: Accidental bookmark deletion
   - *Mitigation*: Confirmation dialogs, undo functionality
   
2. **Concurrent Editing**: Multiple users editing simultaneously
   - *Mitigation*: File locking, optimistic updates with conflict detection
   
3. **Large Bookmark Collections**: Performance with 1000+ bookmarks
   - *Mitigation*: Virtual scrolling, lazy loading, pagination

### UX Risks
1. **Accidental Reorganization**: Unintended drag and drop
   - *Mitigation*: Drag threshold, visual feedback, undo
   
2. **Mobile Usability**: Touch-based bookmark management
   - *Mitigation*: Touch-friendly targets, long-press menus

## Dependencies

### Frontend Technologies
- **HTMX**: For server-side rendering with AJAX updates
- **Sortable.js**: Drag and drop functionality
- **Context Menu Library**: Right-click menu implementation

### Backend Requirements  
- Flask route handlers for CRUD operations
- Enhanced `BookmarkBarManager` for editing operations
- Data validation and sanitization
- Atomic file operations for data safety

## Timeline Estimate

### Phase 1: Core Editing (2 weeks)
- Basic CRUD operations via right-click menus
- Inline editing for bookmark names and URLs
- Data persistence and validation

### Phase 2: Drag & Drop (1 week)  
- Implement drag and drop reorganization
- Visual feedback during dragging
- Drop zone highlighting

### Phase 3: Polish & Testing (1 week)
- Keyboard shortcuts
- Error handling and user feedback
- Comprehensive testing
- Documentation

**Total Estimated Timeline: 4 weeks**
