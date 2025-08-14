# HTMX 2.0 Enhancement Implementation Guide

This guide provides step-by-step instructions for implementing each HTMX enhancement in priority order.

## Prerequisites

- ✅ HTMX 2.0.6 already installed
- ✅ Alpine.js 3.x already installed
- ✅ Application running and tested
- ✅ Git branch created for implementation

## Phase 1: Quick Wins

### 1.1 Add Preload Extension

#### Step 1: Install the Extension
Update `/workspaces/onboard/app/templates/index.html`:

```html
<!-- Add after the existing HTMX script tag -->
<script defer src="https://unpkg.com/htmx.org@2.0.6/dist/htmx.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/htmx-ext-preload@2.0.2/dist/preload.js"></script>
```

#### Step 2: Update Widget Templates
Update `/workspaces/onboard/app/templates/widget.html`:

```html
<!-- Change this: -->
<div class="box {{ widget.type }}-box" hx-get="{{ widget.hx_get }}" hx-trigger="load" hx-swap="outerHTML">

<!-- To this: -->
<div class="box {{ widget.type }}-box" 
     hx-get="{{ widget.hx_get }}" 
     hx-trigger="load" 
     hx-swap="outerHTML"
     hx-ext="preload"
     preload="mouseenter">
```

Update `/workspaces/onboard/app/templates/docker_containers.html`:

```html
<!-- Change this: -->
<div class="box"
{% if widget and widget['hx-get'] and not containers %}
  hx-get="{{ widget['hx-get'] }}" hx-trigger="load" hx-swap="outerHTML"
{% endif %}

<!-- To this: -->
<div class="box"
{% if widget and widget['hx-get'] and not containers %}
  hx-get="{{ widget['hx-get'] }}" 
  hx-trigger="load" 
  hx-swap="outerHTML"
  hx-ext="preload"
  preload="mouseenter"
{% endif %}
```

#### Step 3: Test Preloading
1. Start the application: `uv run python run.py`
2. Open browser developer tools (Network tab)
3. Hover over widget boxes that show "Loading..."
4. Verify requests are made on hover, not just on load
5. Confirm subsequent hovers don't trigger duplicate requests

### 1.2 Implement View Transitions

#### Step 1: Enable Global View Transitions
Update `/workspaces/onboard/app/templates/index.html` head section:

```html
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="htmx-config" content='{"globalViewTransitions": true}'>
    <title>{{ site_title }}</title>
```

#### Step 2: Update Tab Navigation
Update the tab navigation section in `/workspaces/onboard/app/templates/index.html`:

```html
<!-- Change this: -->
<div class="row tab-bar">
    {% for tab in layout.tabs %}
        <a href="/tab/{{tab.name}}" data-index="{{ loop.index }}" data-current="{{ tab.name == tab_name }}">{{tab.name}}</a>
    {% endfor %}
</div>

<!-- To this: -->
<div class="row tab-bar">
    {% for tab in layout.tabs %}
        <a href="/tab/{{tab.name}}" 
           hx-get="/tab/{{tab.name}}"
           hx-target="#main-content"
           hx-swap="innerHTML transition:true"
           hx-push-url="true"
           data-index="{{ loop.index }}" 
           data-current="{{ tab.name == tab_name }}">{{tab.name}}</a>
    {% endfor %}
</div>
```

#### Step 3: Add Main Content Container
Wrap the main content area:

```html
<!-- Change this: -->
{% for row in layout.tab(tab_name).rows:  %}
    {% with row=row %}
        {% include "row.html" %}
    {% endwith %}
{% endfor %}

<!-- To this: -->
<div id="main-content">
    {% for row in layout.tab(tab_name).rows:  %}
        {% with row=row %}
            {% include "row.html" %}
        {% endwith %}
    {% endfor %}
</div>
```

#### Step 4: Update Server Routes
Create new partial template `/workspaces/onboard/app/templates/tab_content.html`:

```html
{% for row in layout.tab(tab_name).rows:  %}
    {% with row=row %}
        {% include "row.html" %}
    {% endwith %}
{% endfor %}
```

Update `/workspaces/onboard/app/app.py` to handle partial requests:

```python
@app.route("/tab/<tab_name>")
def tab_view(tab_name):
    """Handle tab navigation with HTMX support"""
    if request.headers.get('HX-Request'):
        # Return partial content for HTMX requests
        return render_template('tab_content.html', 
                             layout=layout, 
                             tab_name=tab_name)
    else:
        # Return full page for direct navigation
        return render_template('index.html', 
                             layout=layout, 
                             tab_name=tab_name,
                             site_title=app.config.get('SITE_TITLE', 'OnBoard'),
                             today_date=datetime.now())
```

#### Step 5: Test View Transitions
1. Restart the application
2. Open in a modern browser (Chrome/Edge recommended)
3. Click between tabs
4. Verify smooth transitions occur
5. Test browser back/forward buttons
6. Verify URLs update correctly

## Phase 2: Enhanced UX

### 2.1 Add Head Support Extension

#### Step 1: Install Head Support
Update `/workspaces/onboard/app/templates/index.html`:

```html
<script defer src="https://unpkg.com/htmx.org@2.0.6/dist/htmx.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/htmx-ext-preload@2.0.2/dist/preload.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/htmx-ext-head-support@2.0.2/dist/head-support.js"></script>
```

#### Step 2: Enable Extension
Update body tag:

```html
<body hx-ext="head-support">
```

#### Step 3: Update Tab Content Template
Update `/workspaces/onboard/app/templates/tab_content.html` to include head tags:

```html
<head>
    <title>{{ tab_name }} - {{ site_title }}</title>
    <meta property="og:title" content="{{ tab_name }} - {{ site_title }}">
</head>
{% for row in layout.tab(tab_name).rows:  %}
    {% with row=row %}
        {% include "row.html" %}
    {% endwith %}
{% endfor %}
```

#### Step 4: Test Dynamic Titles
1. Navigate between tabs
2. Verify browser tab title updates
3. Test browser bookmarking functionality

### 2.2 Add hx-boost Navigation

#### Step 1: Enable Boost
Update body tag to include boost:

```html
<body hx-boost="true" hx-ext="head-support">
```

#### Step 2: Test Boosted Navigation
1. Click on header links
2. Verify AJAX requests are made
3. Check browser history works correctly
4. Test any forms in the application

### 2.3 Add Loading States Extension

#### Step 1: Install Loading States
Add to scripts:

```html
<script defer src="https://cdn.jsdelivr.net/npm/htmx-ext-loading-states@2.0.2/dist/loading-states.js"></script>
```

#### Step 2: Add CSS for Loading States
Create or update `/workspaces/onboard/app/static/css/loading-states.css`:

```css
/* Loading states for widgets */
.widget-loading {
    opacity: 0.6;
    position: relative;
    pointer-events: none;
}

.widget-loading::after {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 20px;
    height: 20px;
    margin: -10px 0 0 -10px;
    border: 2px solid #ccc;
    border-top-color: #007bff;
    border-radius: 50%;
    animation: widget-spin 1s linear infinite;
    z-index: 1000;
}

@keyframes widget-spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Loading states for tabs */
.tab-loading {
    opacity: 0.7;
    transition: opacity 0.2s ease;
}

/* Loading state for general elements */
.htmx-loading {
    opacity: 0.5;
    cursor: wait;
}
```

#### Step 3: Update Widget Templates
Update widget templates to use loading states:

```html
<div class="box {{ widget.type }}-box" 
     hx-get="{{ widget.hx_get }}" 
     hx-trigger="load" 
     hx-swap="outerHTML"
     hx-ext="preload loading-states"
     preload="mouseenter"
     data-loading-class="widget-loading"
     data-loading-disable>
```

#### Step 4: Update Tab Navigation
Add loading states to tabs:

```html
<a href="/tab/{{tab.name}}" 
   hx-get="/tab/{{tab.name}}"
   hx-target="#main-content"
   hx-swap="innerHTML transition:true"
   hx-push-url="true"
   hx-ext="loading-states"
   data-loading-class="tab-loading"
   data-index="{{ loop.index }}" 
   data-current="{{ tab.name == tab_name }}">{{tab.name}}</a>
```

## Phase 3: Polish

### 3.1 Alpine-morph Integration

#### Step 1: Install Alpine-morph Extension
Add to scripts:

```html
<script defer src="https://cdn.jsdelivr.net/npm/htmx-ext-alpine-morph@2.0.2/dist/alpine-morph.js"></script>
```

#### Step 2: Update Components with Alpine State
Update widgets that use Alpine.js to use morphing:

```html
<div class="box {{ widget.type }}-box" 
     hx-get="{{ widget.hx_get }}" 
     hx-trigger="load" 
     hx-swap="morph"
     hx-ext="preload loading-states alpine-morph"
     preload="mouseenter"
     data-loading-class="widget-loading"
     data-loading-disable>
```

## Testing Checklist

### Functional Testing
- [ ] All widgets load correctly
- [ ] Preloading works on hover
- [ ] Tab navigation is smooth
- [ ] View transitions work in supported browsers
- [ ] Loading states display correctly
- [ ] Alpine.js state is preserved
- [ ] Browser history works correctly
- [ ] Direct URL navigation works

### Performance Testing
- [ ] No performance regressions
- [ ] Loading feels faster
- [ ] Transitions are smooth (60fps)
- [ ] No memory leaks during extended use

### Cross-browser Testing
- [ ] Chrome/Edge (full support)
- [ ] Firefox (graceful degradation)
- [ ] Safari (basic functionality)
- [ ] Mobile browsers

### Accessibility Testing
- [ ] Screen reader compatibility
- [ ] Keyboard navigation works
- [ ] Focus management during transitions
- [ ] ARIA states for loading

## Rollback Plan

If any issues arise, rollback can be done incrementally:

1. **Remove loading-states extension** - Remove script and CSS
2. **Disable alpine-morph** - Change back to outerHTML swaps
3. **Remove head-support** - Remove script and head tags from partials
4. **Disable hx-boost** - Remove from body tag
5. **Remove view transitions** - Remove config and hx-get from tabs
6. **Remove preload** - Remove extension and preload attributes

Each phase can be rolled back independently without affecting others.

## Performance Monitoring

After implementation, monitor these metrics:

- Page load times
- Time to interactive
- User engagement metrics
- Error rates
- Network request patterns

Use browser developer tools and analytics to validate improvements.
