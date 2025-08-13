**Important:**
- Before marking any test step complete, always run `make test` and resolve all errors, failures, and warnings. Only check off a step when the code and tests are fully passing and clean.
- After running `make test`, update the checklist in this file (change `[ ]` to `[x]` for the step).
- Do not proceed to the next step until both actions are done and confirmed.
- If any required action is skipped, go back and complete it before continuing.

**Testing Requirements:**
- **Code Coverage:** Aim for 90%+ test coverage for each class/module being tested
- **Test Quality:** All tests must pass without errors, failures, or warnings
- **Verification:** Run `make test` successfully before marking any step complete
- **Coverage Verification:** Use `uv run pytest tests/path/to/test_file.py --cov=module.path --cov-report=term-missing -v` to verify coverage targets

**⚠️ IMPORT MOCKING REFERENCE:** See `/workspaces/onboard/.devplanning/add_testing/import_analysis.md` for comprehensive mapping of all relative imports and their correct patch paths. Testing templates with correct mocking patterns available in `/workspaces/onboard/.devplanning/add_testing/testing_templates.md`. **ALL IMPORT ISSUES PROACTIVELY RESOLVED** ✅

**🔧 RELATIVE IMPORT FIXES:** All relative import issues in the codebase have been identified and fixed. See `/workspaces/onboard/.devplanning/add_testing/import_fixes_summary.md` for complete details. **ALL 22 TESTS NOW PASSING** ✅

# Step-by-Step Plan: Adding Testing to the Project

## Checklist
1. [x] Select Testing Framework (**pytest** for unit tests, **behave** for BDD/acceptance tests)
   - Both frameworks are now listed as required.
   - Installed with: `uv pip install pytest behave` (already completed)
2. [x] Set Up Test Directory Structure
   - `tests/models/` and `tests/app/` directories created for unit tests.
   - `tests/features/` and `tests/features/steps/` directories created for BDD tests.
3. [x] Identify Core Classes and Functions
4. [x] Add Fixtures and Mocks
   - Mocks and test doubles will be added as needed for each test (using unittest.mock or pytest-mock).
   - Setup/teardown fixtures (e.g., pytest fixtures, setup_method, teardown_method) will be created in each test module as appropriate.
   - Example:
     - Use `@pytest.fixture` for reusable setup.
     - Use `monkeypatch` or `mock.patch` for mocking external dependencies (file I/O, network calls, etc.).
   - Implementation of mocks and fixtures will happen alongside each test, not globally.

## Mocking Best Practices and Common Issues

### Import Path Mocking Resolution (Tab Class Example)
When testing classes that import dependencies, the mock patch path must match exactly where the dependency is imported in the module under test, not where it's originally defined.

**Problem encountered with Tab class:**
- `Tab` imports `from_list` from `.utils` at module level: `from .utils import from_list`
- Initial incorrect patch: `@patch('app.models.utils.from_list')` ❌
- Correct patch: `@patch('app.models.tab.from_list')` ✅

**Rule:** Patch where the import occurs, not where it's defined.

**Example from Tab tests:**
```python
# Tab module has: from .utils import from_list
# Correct mocking approach:
@patch('app.models.tab.from_list')  # Patch in tab module
@patch('app.models.row.Row')        # Patch Row class
def test_from_dict_with_rows(self, mock_row_class, mock_from_list):
    # Setup mocks
    mock_row_instance = MagicMock()
    mock_row_class.from_dict = MagicMock(return_value=mock_row_instance)
    mock_from_list.return_value = [mock_row_instance, mock_row_instance]
    
    # Test execution
    dictionary = {"tab": "TestTab", "rows": ["row1", "row2"]}
    tab = Tab.from_dict(dictionary)
    
    # Verification
    mock_from_list.assert_called_once_with(mock_row_class.from_dict, dictionary["rows"])
```

**Debugging mocking issues:**
1. Check import statements in the module under test
2. Verify patch paths match import locations
3. Use `mock.assert_called_once_with()` to verify mock interactions
4. Test both return values and method calls for comprehensive coverage

**Import Resolution Examples:**
- Module has `from .utils import from_list` → Patch: `'module.from_list'`
- Module has `import models.row` → Patch: `'models.row'`
- Module has `from models import row` → Patch: `'module.row'`

## Write Unit Tests for Each Class
5. [x] app/processors/title_editor.py: TitleEditor
6. [x] app/models/tab.py: Tab
7. [x] app/models/widget_item.py: WidgetItem
8. [x] app/models/widget.py: Widget
9. [x] app/models/row.py: Row
10. [ ] app/models/scheduler.py: Scheduler
11. [ ] app/models/noop_feed_processor.py: NoOpFeedProcessor
12. [ ] app/models/layout.py: Layout
13. [ ] app/models/iframe.py: Iframe
14. [ ] app/models/feed_article.py: FeedArticle
15. [ ] app/models/feed.py: Feed
16. [ ] app/models/bookmarks.py: Bookmarks
17. [ ] app/models/column.py: Column
18. [ ] app/models/exceptions.py: IDException
19. [x] app/models/bookmark.py: Bookmark
20. [ ] app/services/bookmark_bar_manager.py: BookmarkBarManager
21. [ ] app/services/favicon_store.py: FaviconStore
22. [ ] app/services/link_tracker.py: LinkTracker
23. [ ] app/utils.py: Utility functions
24. [ ] app/app.py: Flask app, routes, and startup logic

## Write Unit Tests for Key Functions
25. [ ] app/models/utils.py: from_list
26. [ ] app/models/utils.py: from_dict
27. [ ] app/models/utils.py: normalize_text
28. [ ] app/models/utils.py: calculate_sha1_hash
29. [ ] app/app.py: index route
30. [ ] app/app.py: feed route
31. [ ] app/app.py: click_events route
32. [ ] app/app.py: track route
33. [ ] app/app.py: refresh route
34. [ ] app/app.py: healthcheck route
35. [ ] app/models/scheduler.py: Scheduler logic
36. [ ] app/models/feed.py & app/models/feed_article.py: Feed/article processing
37. [ ] app/utils.py: copy_default_to_configs

38. [ ] Integrate with CI/CD
39. [ ] Measure Coverage
40. [ ] Document Testing Approach
41. [ ] Iterate and Expand

## Key functions to test:
    - app/models/utils.py: from_list, from_dict, normalize_text, calculate_sha1_hash
    - app/app.py: Flask route handlers (index, feed, click_events, track, refresh, healthcheck)
    - app/models/scheduler.py: Scheduler logic
    - app/models/feed.py & app/models/feed_article.py: Feed/article processing
    - app/utils.py: copy_default_to_configs
    - Any other utility or business logic functions

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
