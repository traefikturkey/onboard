import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

from app.models.bookmarks import Bookmarks
from app.models.column import Column
from app.models.exceptions import IDException
from app.models.feed import Feed
from app.models.feed_article import FeedArticle


class TestFeedArticle(unittest.TestCase):
    def test_title_selection_and_summary(self):
        parent = MagicMock()
        a = FeedArticle(
            original_title="Orig",
            title="",
            link="l",
            description="Desc",
            pub_date=datetime.now(),
            processed="",
            parent=parent,
        )
        self.assertIn(a.title, ("Orig", "Desc"))

    def test_filters_remove_and_strip(self):
        parent = MagicMock()
        parent.filters = [
            {"type": "remove", "text": "bad", "attribute": "title"},
            {"type": "strip", "text": "stripme", "attribute": "description"},
        ]

        a = FeedArticle(
            original_title="Orig",
            title="has bad content",
            link="l",
            description="please stripme this",
            pub_date=datetime.now(),
            processed="",
            parent=parent,
        )
        self.assertTrue(a.removed)
        self.assertNotIn("stripme", a.description)

    def test_filter_remove_case_insensitive(self):
        """Remove filter should be case insensitive."""
        parent = MagicMock()
        parent.filters = [
            {"type": "remove", "text": "SPAM", "attribute": "title"},
        ]

        a = FeedArticle(
            original_title="Orig",
            title="this is spam content",
            link="l",
            description="desc",
            pub_date=datetime.now(),
            processed="",
            parent=parent,
        )
        self.assertTrue(a.removed)

    def test_filter_remove_regex_pattern(self):
        """Remove filter should support regex patterns."""
        parent = MagicMock()
        parent.filters = [
            {"type": "remove", "text": r"\[AD\]|\[Sponsored\]", "attribute": "title"},
        ]

        a1 = FeedArticle(
            original_title="O",
            title="[AD] Buy this now",
            link="l",
            description="d",
            pub_date=datetime.now(),
            processed="",
            parent=parent,
        )
        self.assertTrue(a1.removed)

        a2 = FeedArticle(
            original_title="O",
            title="Normal article",
            link="l",
            description="d",
            pub_date=datetime.now(),
            processed="",
            parent=parent,
        )
        self.assertFalse(a2.removed)

    def test_filter_strip_removes_pattern(self):
        """Strip filter removes matching text."""
        parent = MagicMock()
        parent.filters = [
            {"type": "strip", "text": r"\s*-\s*Read more$", "attribute": "description"},
        ]

        a = FeedArticle(
            original_title="O",
            title="T",
            link="l",
            description="Article summary - Read more",
            pub_date=datetime.now(),
            processed="",
            parent=parent,
        )
        self.assertEqual(a.description, "Article summary")

    def test_filter_unknown_type_ignored(self):
        """Unknown filter types are silently ignored."""
        parent = MagicMock()
        parent.filters = [
            {"type": "unknown_filter", "text": "test", "attribute": "title"},
        ]

        a = FeedArticle(
            original_title="O",
            title="test title",
            link="l",
            description="d",
            pub_date=datetime.now(),
            processed="",
            parent=parent,
        )
        # Should not raise and article should not be modified
        self.assertFalse(a.removed)
        self.assertEqual(a.title, "test title")

    def test_filter_nonexistent_attribute_ignored(self):
        """Filter on nonexistent attribute is silently ignored."""
        parent = MagicMock()
        parent.filters = [
            {"type": "remove", "text": "test", "attribute": "nonexistent_field"},
        ]

        a = FeedArticle(
            original_title="O",
            title="T",
            link="l",
            description="d",
            pub_date=datetime.now(),
            processed="",
            parent=parent,
        )
        # Should not raise
        self.assertFalse(a.removed)

    def test_no_filters_does_not_modify(self):
        """Article without filters should not be removed."""
        parent = MagicMock()
        parent.filters = None

        a = FeedArticle(
            original_title="O",
            title="T",
            link="l",
            description="d",
            pub_date=datetime.now(),
            processed="",
            parent=parent,
        )
        self.assertFalse(a.removed)


class TestFeed(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        os.environ["WORKING_STORAGE"] = self.tmpdir.name

    def tearDown(self):
        self.tmpdir.cleanup()
        os.environ.pop("WORKING_STORAGE", None)

    def make_widget(self):
        return {"name": "TestFeed", "feed_url": "http://example.com/rss", "widgets": []}

    def test_feed_url_setter_sets_id(self):
        widget = self.make_widget()
        f = Feed(widget)
        self.assertIsNotNone(f.id)
        self.assertTrue(isinstance(f.id, str) and len(f.id) > 0)

    def test_load_cache_no_file_returns_empty(self):
        widget = self.make_widget()
        f = Feed(widget)
        p = Path(self.tmpdir.name) / "nonexistent.json"
        res = f.load_cache(p)
        self.assertEqual(res, [])

    def test_processors_with_missing_processor_uses_noop(self):
        widget = self.make_widget()
        f = Feed(widget)
        f.widget = {"process": [{"processor": "does_not_exist"}]}
        articles = []
        res = f.processors(articles)
        self.assertEqual(res, [])

    def test_remove_duplicate_articles_keeps_processed(self):
        widget = self.make_widget()
        f = Feed(widget)
        a1 = MagicMock()
        a1.id = "1"
        a1.processed = None
        a1.removed = False

        a2 = MagicMock()
        a2.id = "1"
        a2.processed = "p"
        a2.removed = False

        a3 = MagicMock()
        a3.id = "2"
        a3.processed = None
        a3.removed = False

        res = f.remove_duplicate_articles([a1, a2, a3])
        ids = set([r.id for r in res])
        self.assertEqual(ids, {"1", "2"})

    def test_save_articles_writes_cache(self):
        widget = self.make_widget()
        f = Feed(widget)
        articles = []
        f.save_articles(articles)
        self.assertTrue(f.cache_path.exists())
        with open(f.cache_path, "r") as fh:
            data = json.load(fh)
            self.assertIn("articles", data)


class TestBookmarksColumnExceptions(unittest.TestCase):
    def test_bookmarks_from_dict(self):
        # Create a mock bookmark_manager with sections
        mock_manager = MagicMock()
        mock_manager.get_section.return_value = {
            "displayName": "Test",
            "bookmarks": [{"name": "b1", "link": "l1"}],
        }
        widget = {"bookmarks_section": "test-section", "name": "bookmarks1"}
        b = Bookmarks(widget, bookmark_manager=mock_manager)
        self.assertTrue(len(b.items) == 1)

    def test_column_from_dict_empty(self):
        col = Column.from_dict({"widgets": []})
        self.assertEqual(col.widgets, [])

    def test_id_exception(self):
        with self.assertRaises(IDException):
            raise IDException("boom")


if __name__ == "__main__":
    unittest.main()
