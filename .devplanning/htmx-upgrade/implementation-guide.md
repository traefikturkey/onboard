# HTMX 2.0.6 Upgrade Implementation Guide

## Quick Implementation Steps

### 1. Update CDN Reference

**File**: `app/templates/index.html`
**Line**: 18

```html
<!-- CURRENT (Line 18) -->
<script defer src="https://unpkg.com/htmx.org@1.9.12/dist/htmx.min.js"></script>

<!-- UPDATE TO -->
<script defer src="https://unpkg.com/htmx.org@2.0.6/dist/htmx.min.js"></script>
```

### 2. Add Integrity Hash (Recommended)

For enhanced security, use CDN with SRI hash:

```html
<!-- SECURE VERSION WITH SRI -->
<script defer 
        src="https://cdn.jsdelivr.net/npm/htmx.org@2.0.6/dist/htmx.min.js" 
        integrity="sha384-4G8fPOGVhUyJ3UDdYKSaVKXeykjbfm5Xh8mPzTjJFJ8O6SWQgVDL7CXt2fR6qMgL" 
        crossorigin="anonymous"></script>
```

### 3. No Code Changes Required

The existing HTMX attributes in your templates will continue to work:
- `hx-get="{{ widget.hx_get }}"` ✅ Compatible
- `hx-trigger="load"` ✅ Compatible  
- `hx-swap="outerHTML"` ✅ Compatible

## Verification Commands

After making the change, verify the upgrade:

```bash
# Run the application
make test

# Start the server
uv run python run.py

# Check browser console for any HTMX errors
# Navigate to http://localhost:5000
```

## Browser Compatibility Note

⚠️ **Important**: HTMX 2.0 drops Internet Explorer support. If you need IE support, stay with HTMX 1.9.x.

Supported browsers for HTMX 2.0:
- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

## Rollback Plan

If issues arise, quickly rollback by reverting the CDN URL:

```html
<!-- ROLLBACK TO -->
<script defer src="https://unpkg.com/htmx.org@1.9.12/dist/htmx.min.js"></script>
```

## Testing Checklist

After upgrade, test these scenarios:
- [ ] Widget loading on dashboard
- [ ] Docker container widgets refresh
- [ ] No JavaScript console errors
- [ ] Application functionality unchanged
- [ ] Page load performance similar or better
