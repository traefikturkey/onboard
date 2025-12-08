# UI Flows & Wireframes (low-fi)

## Screens

1) Bookmarks Overview
- Table grouped by Sections
- Actions: Create Section, Import, Export
- Search box (filter by name, tag, URL)

2) Section Detail
- Header: Section name + metadata (multiColumn, openInNewTab)
- List of bookmarks (drag to reorder)
- Actions: Add Bookmark, Edit Section, Delete Section

3) Bookmark Editor
- Fields: Name, URL, Tags (chips), Favicon (auto), Add to Bar (checkbox)
- Save/Cancel

4) Bar Manager (optional separate tab)
- List of Bar bookmarks with drag-to-reorder
- Add from existing or new URL

## Interaction Notes
- Use HTMX for partial updates; progressive enhancement over Flask templates.
- Validation: URL format, required name.
- Confirmations on destructive actions.
- Toaster-style flash messages for success/fail.

## Wireframe Notes (text)
- Overview: [Create Section] [Import] [Export]
  - Section Card: name, counts, quick actions (Add, Edit, Delete, View)
- Section Detail: [Add Bookmark] [Edit Section] [Delete]
  - List rows: [drag] [favicon] name — url — tags — actions (Edit/Delete)
- Bookmark Editor: simple form in modal (htmx or dedicated route).
