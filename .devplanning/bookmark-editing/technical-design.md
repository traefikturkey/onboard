# Technical Design - Bookmark Editing Feature

## Architecture Overview

The bookmark editing feature will extend the existing bookmark system with CRUD capabilities while maintaining the current architecture patterns. The design emphasizes server-side rendering with HTMX for seamless updates.

## Current System Analysis

### Existing Components

**Backend Components:**
- `BookmarkBarManager` - Loads/reloads JSON data
- `Bookmark` model - Individual bookmark representation  
- `Bookmarks` widget - Collection of bookmarks
- JSON data store at `app/configs/bookmarks_bar.json`

**Frontend Components:**
- `bookmark_bar.html` - Recursive template for rendering
- `bookmark_bar.css` - Chrome-like styling
- Favicon integration via `FaviconStore`

### Data Flow
```
JSON File → BookmarkBarManager → Layout → Template → HTML
```

## Enhanced Architecture

### New Backend Components

**1. Bookmark API Controller**
```python
# app/api/bookmarks.py
class BookmarkAPI:
    def __init__(self, bookmark_manager: BookmarkBarManager):
        self.manager = bookmark_manager
    
    def create_bookmark(self, name: str, url: str, parent_id: str = None) -> dict
    def update_bookmark(self, bookmark_id: str, **updates) -> dict  
    def delete_bookmark(self, bookmark_id: str) -> bool
    def move_bookmark(self, bookmark_id: str, target_id: str, position: int) -> bool
    def create_folder(self, name: str, parent_id: str = None) -> dict
```

**2. Enhanced BookmarkBarManager**
```python
# app/services/bookmark_bar_manager.py (enhanced)
class BookmarkBarManager:
    # Existing methods...
    
    def save(self) -> None:
        """Atomically save bookmark data to JSON file"""
        
    def add_bookmark(self, bookmark_data: dict, parent_path: str = None) -> str:
        """Add bookmark and return generated ID"""
        
    def update_bookmark(self, bookmark_id: str, updates: dict) -> bool:
        """Update bookmark by ID"""
        
    def delete_bookmark(self, bookmark_id: str) -> bool:
        """Delete bookmark and children if folder"""
        
    def move_bookmark(self, source_id: str, target_id: str, position: int) -> bool:
        """Move bookmark to new location"""
        
    def find_by_id(self, bookmark_id: str) -> tuple[dict, list]:
        """Find bookmark and its parent path"""
```

**3. Data Validation Service**
```python
# app/services/bookmark_validator.py
class BookmarkValidator:
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format and accessibility"""
        
    @staticmethod  
    def validate_name(name: str) -> bool:
        """Validate bookmark name (length, characters)"""
        
    @staticmethod
    def sanitize_input(data: dict) -> dict:
        """Sanitize user input for safe storage"""
```

### New Frontend Components

**1. Enhanced Bookmark Bar Template**
```html
<!-- app/templates/bookmark_bar_editable.html -->
{% extends "bookmark_bar.html" %}

{% block bookmark_item %}
<li data-bookmark-id="{{ bookmark.id }}" 
    class="bookmark-item{% if bookmark.contents %} folder{% endif %}">
    
    <!-- Existing bookmark display -->
    {{ super() }}
    
    <!-- Edit overlay (hidden by default) -->
    <div class="bookmark-edit-overlay" style="display: none;">
        <input type="text" class="bookmark-name-edit" value="{{ bookmark.name }}">
        <input type="url" class="bookmark-url-edit" value="{{ bookmark.href }}" 
               {% if bookmark.contents %}style="display: none;"{% endif %}>
        <button class="save-edit">✓</button>
        <button class="cancel-edit">✗</button>
    </div>
</li>
{% endblock %}
```

**2. JavaScript Editing Controls**
```javascript
// app/static/js/bookmark-editor.js
class BookmarkEditor {
    constructor() {
        this.setupEventListeners();
        this.setupDragAndDrop();
        this.setupContextMenu();
    }
    
    // Right-click context menu
    setupContextMenu() { /* ... */ }
    
    // Inline editing
    enableInlineEdit(bookmarkElement) { /* ... */ }
    
    // Drag and drop
    setupDragAndDrop() { /* ... */ }
    
    // HTMX integration
    updateBookmark(id, data) { /* ... */ }
}
```

**3. Context Menu Component**
```html
<!-- app/templates/components/bookmark_context_menu.html -->
<div id="bookmark-context-menu" class="context-menu" style="display: none;">
    <ul>
        <li><a href="#" data-action="edit">Edit</a></li>
        <li><a href="#" data-action="delete">Delete</a></li>
        <li class="separator"></li>
        <li><a href="#" data-action="add-bookmark">Add Bookmark</a></li>
        <li><a href="#" data-action="add-folder">Add Folder</a></li>
        <li class="separator"></li>
        <li><a href="#" data-action="cut">Cut</a></li>
        <li><a href="#" data-action="copy">Copy</a></li>
        <li><a href="#" data-action="paste">Paste</a></li>
    </ul>
</div>
```

## API Design

### REST Endpoints

```python
# Flask routes
@app.route('/api/bookmarks', methods=['POST'])
def create_bookmark():
    """Create new bookmark"""
    
@app.route('/api/bookmarks/<bookmark_id>', methods=['PUT'])  
def update_bookmark(bookmark_id):
    """Update existing bookmark"""
    
@app.route('/api/bookmarks/<bookmark_id>', methods=['DELETE'])
def delete_bookmark(bookmark_id):
    """Delete bookmark"""
    
@app.route('/api/bookmarks/<bookmark_id>/move', methods=['POST'])
def move_bookmark(bookmark_id):
    """Move bookmark to new location"""
    
@app.route('/api/folders', methods=['POST'])
def create_folder():
    """Create new folder"""

# HTMX partial updates
@app.route('/bookmarks/bar/refresh')
def refresh_bookmark_bar():
    """Return updated bookmark bar HTML"""
```

### Request/Response Formats

**Create Bookmark Request:**
```json
{
    "name": "Example Site",
    "href": "https://example.com",
    "parent_id": "folder123",  // optional
    "position": 2              // optional, append if not specified
}
```

**Update Bookmark Request:**
```json
{
    "name": "New Name",        // optional
    "href": "https://new-url.com",  // optional
    "parent_id": "new-folder"  // optional - moves bookmark
}
```

**Move Bookmark Request:**
```json
{
    "target_parent_id": "folder456",
    "position": 1
}
```

## Data Model Enhancements

### ID Generation Strategy
Since the current JSON structure lacks IDs, we'll generate them:

```python
def generate_bookmark_id() -> str:
    """Generate unique bookmark ID"""
    return f"bm_{int(time.time())}_{secrets.token_hex(4)}"
```

### Enhanced JSON Structure
```json
{
    "id": "bm_1625097600_a1b2c3d4",
    "name": "Example Bookmark", 
    "href": "https://example.com",
    "favicon": "/static/assets/icons/example.com.favicon.ico",
    "add_date": "1625097600",
    "contents": [
        {
            "id": "bm_1625097700_e5f6g7h8",
            "name": "Nested Bookmark",
            "href": "https://nested.example.com",
            "add_date": "1625097700"
        }
    ]
}
```

### Migration Strategy
```python
def migrate_bookmarks_to_include_ids(bookmarks: list) -> list:
    """Add IDs to existing bookmarks without IDs"""
    for bookmark in bookmarks:
        if 'id' not in bookmark:
            bookmark['id'] = generate_bookmark_id()
        if 'contents' in bookmark:
            migrate_bookmarks_to_include_ids(bookmark['contents'])
    return bookmarks
```

## User Interface Design

### Editing Modes

**1. Inline Editing**
- Single-click on bookmark name enables edit mode
- ESC cancels, Enter saves
- Visual feedback with input styling

**2. Context Menu Editing**  
- Right-click opens context menu
- "Edit" opens modal dialog for complex edits
- Folder-specific options (rename, delete, etc.)

**3. Drag and Drop**
- Visual feedback during drag (ghost image)
- Drop zones highlighted on hover
- Snap-to-position indication

### Visual Feedback

**States:**
- Normal: Default bookmark appearance
- Hover: Highlight background
- Editing: Input fields replace text
- Dragging: Semi-transparent with drop zones
- Error: Red border for validation errors

**Loading States:**
- Saving indicator during HTMX requests
- Disable interactions during operations
- Success/error toast notifications

## Security Considerations

### Input Validation
```python
# Server-side validation
def validate_bookmark_data(data: dict) -> tuple[bool, list[str]]:
    errors = []
    
    # Validate name
    if not data.get('name') or len(data['name'].strip()) == 0:
        errors.append("Bookmark name is required")
    elif len(data['name']) > 200:
        errors.append("Bookmark name too long")
        
    # Validate URL
    if 'href' in data:
        if not validators.url(data['href']):
            errors.append("Invalid URL format")
            
    return len(errors) == 0, errors
```

### XSS Prevention
- HTML escape all user input
- Validate URLs against allowed schemes (http, https)
- Sanitize bookmark names to prevent script injection

### File Safety
- Atomic writes to prevent corruption
- Backup before modifications
- File locking for concurrent access protection

## Performance Considerations

### Optimization Strategies

**1. Efficient Updates**
```python
# Only reload affected parts
def update_bookmark_partial(bookmark_id: str, updates: dict) -> str:
    """Update specific bookmark and return minimal HTML"""
    bookmark = find_bookmark_by_id(bookmark_id)
    bookmark.update(updates)
    save_bookmarks()
    return render_bookmark_item(bookmark)
```

**2. Debounced Saves**
```javascript
// Debounce rapid edits
const debouncedSave = debounce(saveBookmark, 500);
```

**3. Lazy Loading**
```python
# For large bookmark collections
def get_bookmarks_paginated(page: int = 1, limit: int = 50) -> dict:
    """Return paginated bookmark results"""
```

### Caching Strategy
- Cache parsed bookmark data in memory
- Invalidate cache on file modification
- Use ETags for conditional requests

## Testing Strategy

### Unit Tests
```python
# tests/services/test_bookmark_manager.py
class TestBookmarkManager:
    def test_add_bookmark(self):
        """Test bookmark creation"""
        
    def test_update_bookmark(self):
        """Test bookmark updates"""
        
    def test_delete_bookmark(self):
        """Test bookmark deletion"""
        
    def test_move_bookmark(self):
        """Test bookmark reorganization"""
```

### Integration Tests
```python
# tests/api/test_bookmark_api.py  
class TestBookmarkAPI:
    def test_create_bookmark_endpoint(self):
        """Test POST /api/bookmarks"""
        
    def test_update_bookmark_endpoint(self):
        """Test PUT /api/bookmarks/<id>"""
```

### Frontend Tests
```javascript
// tests/js/bookmark-editor.test.js
describe('BookmarkEditor', () => {
    test('enables inline editing on click', () => {
        // Test inline editing functionality
    });
    
    test('saves changes via HTMX', () => {
        // Test AJAX save operations
    });
});
```

## Implementation Phases

### Phase 1: Foundation (Week 1)
- [ ] Add ID generation and migration
- [ ] Create BookmarkAPI controller
- [ ] Implement basic CRUD endpoints
- [ ] Add input validation and sanitization

### Phase 2: Basic Editing (Week 2)  
- [ ] Right-click context menu
- [ ] Inline editing for names
- [ ] Modal editing for complex changes
- [ ] HTMX integration for live updates

### Phase 3: Drag & Drop (Week 3)
- [ ] Implement Sortable.js integration
- [ ] Add visual feedback for dragging
- [ ] Handle move operations via API
- [ ] Add undo functionality

### Phase 4: Polish (Week 4)
- [ ] Keyboard shortcuts
- [ ] Error handling and user feedback  
- [ ] Performance optimization
- [ ] Comprehensive testing
- [ ] Documentation updates

## Risk Mitigation

### Data Integrity
- Validate all inputs server-side
- Use atomic file operations
- Implement backup/restore functionality
- Add operation logging for debugging

### User Experience
- Provide clear visual feedback
- Implement undo for destructive actions
- Add confirmation dialogs for deletions
- Graceful handling of network errors

### Performance
- Optimize for common use cases (<100 bookmarks)
- Implement virtual scrolling for large collections
- Use efficient diff algorithms for updates
- Monitor and profile real-world usage
