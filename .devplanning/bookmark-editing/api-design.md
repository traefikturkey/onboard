# API Design - Bookmark Editing Feature

## Overview

This document defines the REST API endpoints and data structures for the bookmark editing feature. The API follows RESTful conventions and integrates with the existing Flask application structure.

## Base URL Structure

All bookmark API endpoints will be prefixed with `/api/bookmarks` to maintain consistency with potential future API endpoints.

## Authentication & Authorization

Currently, the onboard application doesn't implement user authentication. For future-proofing, all endpoints should be designed to support optional authentication headers.

## Core API Endpoints

### 1. Bookmark CRUD Operations

#### GET /api/bookmarks
Retrieve all bookmarks (primarily for debugging/admin use).

**Response:**
```json
{
    "bookmarks": [...],
    "total_count": 42,
    "last_modified": "2025-08-19T10:30:00Z"
}
```

#### POST /api/bookmarks
Create a new bookmark.

**Request Body:**
```json
{
    "name": "Example Site",
    "href": "https://example.com",
    "parent_id": "folder_123",  // Optional: parent folder ID
    "position": 2               // Optional: position within parent (0-indexed)
}
```

**Response (201 Created):**
```json
{
    "success": true,
    "bookmark": {
        "id": "bm_1692454800_a1b2c3d4",
        "name": "Example Site", 
        "href": "https://example.com",
        "favicon": "/static/assets/icons/example.com.favicon.ico",
        "add_date": "1692454800",
        "parent_id": "folder_123",
        "position": 2
    },
    "message": "Bookmark created successfully"
}
```

**Error Response (400 Bad Request):**
```json
{
    "success": false,
    "errors": [
        "Bookmark name is required",
        "Invalid URL format"
    ],
    "message": "Validation failed"
}
```

#### PUT /api/bookmarks/{bookmark_id}
Update an existing bookmark.

**Request Body:**
```json
{
    "name": "Updated Name",        // Optional
    "href": "https://updated.com", // Optional
    "parent_id": "new_folder"      // Optional: move to different folder
}
```

**Response (200 OK):**
```json
{
    "success": true,
    "bookmark": {
        "id": "bm_1692454800_a1b2c3d4",
        "name": "Updated Name",
        "href": "https://updated.com", 
        "favicon": "/static/assets/icons/updated.com.favicon.ico",
        "add_date": "1692454800",
        "parent_id": "new_folder",
        "position": 0
    },
    "message": "Bookmark updated successfully"
}
```

#### DELETE /api/bookmarks/{bookmark_id}
Delete a bookmark.

**Response (200 OK):**
```json
{
    "success": true,
    "message": "Bookmark deleted successfully"
}
```

**Error Response (404 Not Found):**
```json
{
    "success": false,
    "message": "Bookmark not found"
}
```

### 2. Folder Operations

#### POST /api/bookmarks/folders
Create a new folder.

**Request Body:**
```json
{
    "name": "New Folder",
    "parent_id": "parent_folder_123",  // Optional: parent folder
    "position": 1                      // Optional: position within parent
}
```

**Response (201 Created):**
```json
{
    "success": true,
    "folder": {
        "id": "folder_1692454900_e5f6g7h8",
        "name": "New Folder",
        "contents": [],
        "add_date": "1692454900",
        "parent_id": "parent_folder_123",
        "position": 1
    },
    "message": "Folder created successfully"
}
```

#### PUT /api/bookmarks/folders/{folder_id}
Update folder (primarily for renaming).

**Request Body:**
```json
{
    "name": "Renamed Folder"
}
```

#### DELETE /api/bookmarks/folders/{folder_id}
Delete folder and optionally handle children.

**Query Parameters:**
- `recursive=true` - Delete folder and all contents (default: false)
- `move_children_to=parent_id` - Move children to specified parent before deletion

**Response (200 OK):**
```json
{
    "success": true,
    "deleted_items": 5,  // Number of items deleted (including children if recursive)
    "message": "Folder deleted successfully"
}
```

### 3. Organization Operations

#### POST /api/bookmarks/{bookmark_id}/move
Move a bookmark to a new location.

**Request Body:**
```json
{
    "target_parent_id": "folder_456",  // null for root level
    "position": 3                       // Position within target parent
}
```

**Response (200 OK):**
```json
{
    "success": true,
    "bookmark": {
        "id": "bm_1692454800_a1b2c3d4",
        "name": "Moved Bookmark",
        "href": "https://example.com",
        "parent_id": "folder_456",
        "position": 3
    },
    "message": "Bookmark moved successfully"
}
```

#### POST /api/bookmarks/reorder
Reorder multiple items within a parent (batch operation).

**Request Body:**
```json
{
    "parent_id": "folder_123",  // null for root level
    "ordered_ids": [
        "bm_1692454800_a1b2c3d4",
        "folder_1692454900_e5f6g7h8", 
        "bm_1692455000_i9j0k1l2"
    ]
}
```

**Response (200 OK):**
```json
{
    "success": true,
    "updated_count": 3,
    "message": "Items reordered successfully"
}
```

## HTMX Integration Endpoints

These endpoints return HTML fragments for seamless UI updates.

### 1. Partial Content Updates

#### GET /bookmarks/render/item/{bookmark_id}
Return HTML for a single bookmark item.

**Response (text/html):**
```html
<li data-bookmark-id="bm_1692454800_a1b2c3d4" class="bookmark-item">
    <a href="https://example.com">
        <img src="/static/assets/icons/example.com.favicon.ico" alt="Example Site">
        Example Site
    </a>
</li>
```

#### GET /bookmarks/render/bar
Return complete bookmark bar HTML.

**Response (text/html):**
```html
<ul>
    <li data-bookmark-id="...">...</li>
    <!-- ... more bookmarks ... -->
</ul>
```

### 2. Form Rendering

#### GET /bookmarks/forms/edit/{bookmark_id}
Return edit form for a bookmark.

**Response (text/html):**
```html
<form hx-put="/api/bookmarks/bm_1692454800_a1b2c3d4" 
      hx-target="#bookmark-bm_1692454800_a1b2c3d4">
    <input type="text" name="name" value="Example Site" required>
    <input type="url" name="href" value="https://example.com" required>
    <button type="submit">Save</button>
    <button type="button" hx-get="/bookmarks/render/item/bm_1692454800_a1b2c3d4">Cancel</button>
</form>
```

#### GET /bookmarks/forms/create
Return new bookmark creation form.

**Query Parameters:**
- `parent_id` - Parent folder ID
- `name` - Pre-fill bookmark name
- `href` - Pre-fill bookmark URL

## Error Handling

### Standard Error Response Format

All API endpoints follow a consistent error response format:

```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "One or more validation errors occurred",
        "details": [
            {
                "field": "name",
                "message": "Bookmark name is required"
            },
            {
                "field": "href", 
                "message": "Invalid URL format"
            }
        ]
    },
    "timestamp": "2025-08-19T10:30:00Z"
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Input validation failed |
| `BOOKMARK_NOT_FOUND` | 404 | Bookmark ID doesn't exist |
| `FOLDER_NOT_FOUND` | 404 | Folder ID doesn't exist |
| `DUPLICATE_NAME` | 409 | Bookmark name already exists in parent |
| `CIRCULAR_REFERENCE` | 409 | Attempt to move folder into itself |
| `PERMISSION_DENIED` | 403 | Insufficient permissions (future use) |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

## Data Validation Rules

### Bookmark Validation

```python
BOOKMARK_VALIDATION_RULES = {
    'name': {
        'required': True,
        'min_length': 1,
        'max_length': 200,
        'pattern': r'^[^<>"\\/|?*]+$'  # Exclude filesystem-unsafe characters
    },
    'href': {
        'required': True,
        'format': 'url',
        'schemes': ['http', 'https', 'ftp'],
        'max_length': 2048
    },
    'parent_id': {
        'required': False,
        'format': 'bookmark_id',
        'exists_check': True
    },
    'position': {
        'required': False,
        'type': 'integer',
        'min': 0
    }
}
```

### Folder Validation

```python
FOLDER_VALIDATION_RULES = {
    'name': {
        'required': True,
        'min_length': 1,
        'max_length': 100,
        'pattern': r'^[^<>"\\/|?*]+$'
    },
    'parent_id': {
        'required': False,
        'format': 'bookmark_id',
        'exists_check': True,
        'circular_check': True  # Prevent moving folder into itself
    }
}
```

## Rate Limiting

To prevent abuse and ensure system stability:

```python
RATE_LIMITS = {
    'create_bookmark': '10 per minute',
    'update_bookmark': '20 per minute', 
    'delete_bookmark': '5 per minute',
    'move_bookmark': '30 per minute',
    'create_folder': '5 per minute'
}
```

## Caching Strategy

### Cache Headers

All GET endpoints should include appropriate cache headers:

```http
# For bookmark data
Cache-Control: private, max-age=300, must-revalidate
ETag: "bookmark-bar-v1-1692454800"

# For rendered HTML
Cache-Control: private, max-age=60, must-revalidate
```

### Cache Invalidation

When bookmarks are modified:
1. Update the bookmark bar ETag
2. Clear relevant cached HTML fragments
3. Trigger favicon updates if URLs changed

## Implementation Examples

### Flask Route Implementation

```python
from flask import Blueprint, request, jsonify
from app.services.bookmark_bar_manager import BookmarkBarManager
from app.services.bookmark_validator import BookmarkValidator

bookmark_api = Blueprint('bookmark_api', __name__, url_prefix='/api/bookmarks')

@bookmark_api.route('', methods=['POST'])
def create_bookmark():
    data = request.json
    
    # Validate input
    is_valid, errors = BookmarkValidator.validate_bookmark_data(data)
    if not is_valid:
        return jsonify({
            'success': False,
            'errors': errors,
            'message': 'Validation failed'
        }), 400
    
    # Create bookmark
    try:
        bookmark_id = bookmark_manager.add_bookmark(data)
        bookmark = bookmark_manager.get_bookmark(bookmark_id)
        
        return jsonify({
            'success': True,
            'bookmark': bookmark,
            'message': 'Bookmark created successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Failed to create bookmark: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500
```

### HTMX Integration Example

```javascript
// Handle bookmark form submission
document.body.addEventListener('htmx:afterRequest', function(evt) {
    if (evt.detail.xhr.status === 201) {
        // Bookmark created successfully
        showToast('Bookmark created!', 'success');
        closeModal();
    } else if (evt.detail.xhr.status === 400) {
        // Validation errors - HTMX will update the form with errors
        showToast('Please fix the errors below', 'error');
    }
});
```

## Testing Strategy

### API Testing

```python
# tests/api/test_bookmark_api.py
def test_create_bookmark_success(client):
    response = client.post('/api/bookmarks', json={
        'name': 'Test Bookmark',
        'href': 'https://test.com'
    })
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] is True
    assert 'bookmark' in data
    assert data['bookmark']['name'] == 'Test Bookmark'

def test_create_bookmark_validation_error(client):
    response = client.post('/api/bookmarks', json={
        'name': '',  # Invalid empty name
        'href': 'invalid-url'  # Invalid URL
    })
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert 'errors' in data
```

### Integration Testing

```python
# tests/integration/test_bookmark_workflow.py
def test_full_bookmark_workflow(client):
    # Create folder
    folder_response = client.post('/api/bookmarks/folders', json={
        'name': 'Test Folder'
    })
    folder_id = folder_response.get_json()['folder']['id']
    
    # Create bookmark in folder
    bookmark_response = client.post('/api/bookmarks', json={
        'name': 'Test Bookmark',
        'href': 'https://test.com',
        'parent_id': folder_id
    })
    bookmark_id = bookmark_response.get_json()['bookmark']['id']
    
    # Move bookmark
    move_response = client.post(f'/api/bookmarks/{bookmark_id}/move', json={
        'target_parent_id': None,  # Move to root
        'position': 0
    })
    
    assert move_response.status_code == 200
```

## Security Considerations

### Input Sanitization

All user input must be sanitized to prevent XSS and other attacks:

```python
import bleach
from urllib.parse import urlparse

def sanitize_bookmark_data(data):
    if 'name' in data:
        data['name'] = bleach.clean(data['name'], tags=[], strip=True)
    
    if 'href' in data:
        parsed_url = urlparse(data['href'])
        if parsed_url.scheme not in ['http', 'https', 'ftp']:
            raise ValueError("Invalid URL scheme")
    
    return data
```

### CSRF Protection

```python
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()

# Include CSRF tokens in HTMX requests
@app.after_request
def add_csrf_token(response):
    if request.endpoint and 'api' in request.endpoint:
        response.headers['X-CSRF-Token'] = generate_csrf()
    return response
```

This API design provides a solid foundation for the bookmark editing feature while maintaining consistency with the existing application architecture and preparing for future enhancements.
