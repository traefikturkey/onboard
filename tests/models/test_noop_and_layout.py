import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.models.layout import Layout
from app.models.noop_feed_processor import NoOpFeedProcessor

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


class TestNoOpFeedProcessor(unittest.TestCase):
    def test_process_returns_same_feed(self):
        processor = NoOpFeedProcessor()
        feed = object()
        result = processor.process(feed)
        self.assertIs(result, feed)


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


if __name__ == "__main__":
    unittest.main()
