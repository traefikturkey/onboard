# Step-by-Step Plan: Adding Testing to the Project

## Checklist
1. [x] Select Testing Framework (**pytest** for unit tests, **behave** for BDD/acceptance tests)
   - Both frameworks are now listed as required.
   - Installed with: `uv pip install pytest behave` (already completed)
2. [x] Set Up Test Directory Structure
   - `tests/models/` and `tests/app/` directories created for unit tests.
   - `tests/features/` and `tests/features/steps/` directories created for BDD tests.
3. [ ] Identify Core Classes and Functions
4. [ ] Add Fixtures and Mocks
5. [ ] Integrate with CI/CD
6. [ ] Measure Coverage
7. [ ] Document Testing Approach
8. [ ] Iterate and Expand

## Write Unit Tests for Each Class
9. [ ] app/processors/title_editor.py: TitleEditor
10. [ ] app/models/tab.py: Tab
11. [ ] app/models/widget_item.py: WidgetItem
12. [ ] app/models/widget.py: Widget
13. [ ] app/models/row.py: Row
14. [ ] app/models/scheduler.py: Scheduler
15. [ ] app/models/noop_feed_processor.py: NoOpFeedProcessor
16. [ ] app/models/layout.py: Layout
17. [ ] app/models/iframe.py: Iframe
18. [ ] app/models/feed_article.py: FeedArticle
19. [ ] app/models/feed.py: Feed
20. [ ] app/models/bookmarks.py: Bookmarks
21. [ ] app/models/column.py: Column
22. [ ] app/models/exceptions.py: IDException
23. [ ] app/models/bookmark.py: Bookmark
24. [ ] app/services/favicon_store.py: FaviconStore
25. [ ] app/services/link_tracker.py: LinkTracker
26. [ ] app/services/bookmark_bar_manager.py: BookmarkBarManager

---

## Testing Frameworks
- **pytest**: For unit and integration tests
- **behave**: For BDD/acceptance tests (feature files, scenarios)

## Example Directory Structure

```
tests/
  models/
    test_bookmark.py
    test_feed.py
    ...
  app/
    test_app.py
    test_utils.py
    ...
  features/
    *.feature
    steps/
      step_definitions.py
```

## Example Makefile Additions

```
test:
    pytest --cov=app --cov=models --cov=services --cov-report=term-missing
bdd:
    behave tests/features
```
