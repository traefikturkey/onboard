import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.models.layout import Layout


class TestLayoutBasicMethods(unittest.TestCase):
    def make_layout(self):
        # Create instance without running __init__
        layout = object.__new__(Layout)
        return layout

    def test_bookmarks_list_flattens_nested(self):
        layout = self.make_layout()
        bookmarks = [
            {"title": "A", "href": "http://a"},
            {"title": "B", "contents": [{"title": "B1", "href": "http://b1"}]},
        ]
        urls = layout.bookmarks_list(bookmarks, [])
        self.assertIn("http://a", urls)
        self.assertIn("http://b1", urls)
        self.assertEqual(len(urls), 2)

    def test_tab_selection_none_and_case_insensitive(self):
        layout = self.make_layout()
        t1 = SimpleNamespace(name="First")
        t2 = SimpleNamespace(name="Second")
        layout.tabs = [t1, t2]

        self.assertIs(layout.tab(None), t1)
        self.assertIs(layout.tab("second"), t2)
        # non-existent returns first
        self.assertIs(layout.tab("missing"), t1)

    def test_get_link_header_and_nested_widget(self):
        layout = self.make_layout()
        # header case
        layout.id = "layout"
        layout.headers = [SimpleNamespace(id="h1", link="header-link")]

        self.assertEqual(layout.get_link("layout", "h1"), "header-link")

        # nested widget case
        # create widget item
        item = SimpleNamespace(id="i1", link="item-link")
        # widget should be iterable and have id

        class Widget:
            def __init__(self, wid, items):
                self.id = wid
                self._items = items

            def __iter__(self):
                return iter(self._items)

        widget = Widget("feed1", [item])
        column = SimpleNamespace(rows=[], widgets=[widget])
        row = SimpleNamespace(columns=[column])
        tab = SimpleNamespace(rows=[row])

        layout.tabs = [tab]

        self.assertEqual(layout.get_link("feed1", "i1"), "item-link")

    def test_favicon_path_delegates(self):
        layout = self.make_layout()
        fake_favicon = MagicMock()
        fake_favicon.icon_path.return_value = "icon-path"
        layout.bar_manager = SimpleNamespace(favicon_store=fake_favicon)

        self.assertEqual(layout.favicon_path("http://example"), "icon-path")
        fake_favicon.icon_path.assert_called_once_with("http://example")


class TestLayout(unittest.TestCase):
    def setUp(self):
        # Create a layout instance without running __init__
        self.layout = object.__new__(Layout)
        # Mock bar_manager since reload() needs it
        self.layout.bar_manager = MagicMock()
        # ensure scheduler methods are patched when reload runs
        self.patcher = patch("app.models.layout.Scheduler.clear_jobs")
        self.mock_clear = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def write_yaml_config(self, content: str) -> Path:
        tf = tempfile.NamedTemporaryFile(delete=False, suffix=".yml")
        tf.write(content.encode("utf-8"))
        tf.flush()
        tf.close()
        return Path(tf.name)

    def test_reload_reads_config_and_sets_tabs_headers_and_last_reload(self):
        yaml = """
        tabs:
          - tab: T1
            columns:
              - widgets: []
        headers:
          - name: H1
            link: L1
        """
        path = self.write_yaml_config(yaml)
        try:
            self.layout.config_path = path
            # run reload which should call Scheduler.clear_jobs (patched)
            self.layout.reload()

            # tabs and headers should be set
            self.assertTrue(hasattr(self.layout, "tabs"))
            self.assertTrue(len(self.layout.tabs) >= 1)
            self.assertEqual(self.layout.tabs[0].name, "T1")

            self.assertTrue(hasattr(self.layout, "headers"))
            self.assertTrue(len(self.layout.headers) >= 1)
            self.assertEqual(self.layout.headers[0].link, "L1")

            # last_reload should equal mtime
            self.assertEqual(self.layout.last_reload, self.layout.mtime)
        finally:
            os.unlink(path)

    def test_mtime_and_is_modified(self):
        path = self.write_yaml_config("tabs: []\nheaders: []\n")
        try:
            self.layout.config_path = path
            # set last_reload to earlier time
            self.layout.last_reload = 0
            self.assertTrue(self.layout.is_modified())

            # set last_reload to current mtime
            self.layout.last_reload = self.layout.mtime
            self.assertFalse(self.layout.is_modified())
        finally:
            os.unlink(path)

    def test_get_feeds_widgets_feed_type(self):
        feed_widget = MagicMock()
        feed_widget.type = "feed"
        feed_widget.id = "f1"
        other_widget = MagicMock()
        other_widget.type = "notfeed"

        columns = MagicMock()
        columns.rows = []
        columns.widgets = [other_widget, feed_widget]

        feeds = Layout.get_feeds(self.layout, columns)
        self.assertIn(feed_widget, feeds)
        self.assertNotIn(other_widget, feeds)

    def test_get_feed_and_refresh(self):
        feed = MagicMock()
        feed.id = "feed1"
        feed.type = "feed"
        feed.refresh = MagicMock()

        column = MagicMock()
        column.rows = []
        column.widgets = [feed]
        row = MagicMock()
        row.columns = [column]
        tab = MagicMock()
        tab.rows = [row]

        self.layout.tabs = [tab]
        self.layout.feed_hash = {}

        found = self.layout.get_feed("feed1")
        self.assertIs(found, feed)

        self.layout.refresh_feeds("feed1")
        feed.refresh.assert_called_once()

    def test_get_link_no_match_returns_none(self):
        self.layout.id = "layout"
        self.layout.headers = []
        self.layout.tabs = []

        self.assertIsNone(self.layout.get_link("layout", "nope"))

    def test_bookmark_bar_and_stop_scheduler_and_favicon_property(self):
        fake_bar = "mybar"
        fake_favicon = MagicMock()
        fake_manager = MagicMock()
        fake_manager.bar = fake_bar
        fake_manager.favicon_store = fake_favicon

        self.layout.bar_manager = fake_manager
        self.assertEqual(self.layout.bookmark_bar, fake_bar)
        # stop_scheduler should call Scheduler.shutdown; patch and assert
        with patch("app.models.layout.Scheduler.shutdown") as mock_shutdown:
            self.layout.stop_scheduler()
            mock_shutdown.assert_called_once()

        fake_favicon.icon_path.return_value = "icon-path"
        self.assertEqual(self.layout.favicon_path("u"), "icon-path")
        fake_favicon.icon_path.assert_called_once_with("u")


class TestLayoutUncoveredPaths(unittest.TestCase):
    """Tests for previously uncovered paths in layout.py"""

    def setUp(self):
        self.layout = object.__new__(Layout)
        self.layout.bar_manager = MagicMock()
        self.patcher = patch("app.models.layout.Scheduler.clear_jobs")
        self.mock_clear = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def write_yaml_config(self, content: str) -> Path:
        tf = tempfile.NamedTemporaryFile(delete=False, suffix=".yml")
        tf.write(content.encode("utf-8"))
        tf.flush()
        tf.close()
        return Path(tf.name)

    def test_load_layout_empty_file_returns_empty_dict(self):
        """Empty YAML file returns empty dict via yaml.safe_load or {}."""
        path = self.write_yaml_config("")
        try:
            self.layout.config_path = path
            self.layout.reload()
            # Should have no tabs and no headers
            self.assertEqual(self.layout.tabs, [])
            self.assertEqual(self.layout.headers, [])
        finally:
            os.unlink(path)

    def test_get_feeds_with_nested_rows(self):
        """get_feeds recursively finds feeds in nested row/column structures."""
        inner_feed = MagicMock()
        inner_feed.type = "feed"
        inner_feed.id = "nested-feed"

        # Inner column with the feed
        inner_column = MagicMock()
        inner_column.rows = []
        inner_column.widgets = [inner_feed]

        # Inner row containing inner column
        inner_row = MagicMock()
        inner_row.columns = [inner_column]

        # Outer column containing inner row
        outer_column = MagicMock()
        outer_column.rows = [inner_row]
        outer_column.widgets = []

        feeds = self.layout.get_feeds(outer_column)
        self.assertIn(inner_feed, feeds)

    def test_find_link_nested_rows_returns_none_when_not_found(self):
        """find_link returns None when widget/link not found in nested structure."""
        self.layout.id = "layout"
        self.layout.headers = []

        # Create nested structure without matching widget
        inner_column = MagicMock()
        inner_column.rows = []
        inner_column.widgets = []

        inner_row = MagicMock()
        inner_row.columns = [inner_column]

        outer_column = MagicMock()
        outer_column.rows = [inner_row]
        outer_column.widgets = []

        outer_row = MagicMock()
        outer_row.columns = [outer_column]

        result = self.layout.find_link(outer_row, "nonexistent", "nope")
        self.assertIsNone(result)

    def test_process_rows_recursively_collects_feeds(self):
        """process_rows helper recursively finds feed widgets."""
        feed1 = MagicMock()
        feed1.type = "feed"
        feed2 = MagicMock()
        feed2.type = "feed"
        not_feed = MagicMock()
        not_feed.type = "bookmarks"

        # Nested structure: column with row containing column with feeds
        inner_column = MagicMock()
        inner_column.rows = None
        inner_column.widgets = [feed2, not_feed]

        inner_row = MagicMock()
        inner_row.columns = [inner_column]

        outer_column = MagicMock()
        outer_column.rows = [inner_row]
        outer_column.widgets = [feed1]

        feeds = self.layout.process_rows(outer_column)
        self.assertIn(feed1, feeds)
        self.assertIn(feed2, feeds)
        self.assertNotIn(not_feed, feeds)


if __name__ == "__main__":
    unittest.main()
