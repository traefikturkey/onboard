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
    widget = {"bookmarks": [{"name": "b1", "link": "l1"}], "name": "bookmarks1"}
    b = Bookmarks(widget)
    self.assertTrue(len(b.items) == 1)

  def test_column_from_dict_empty(self):
    col = Column.from_dict({"widgets": []})
    self.assertEqual(col.widgets, [])

  def test_id_exception(self):
    with self.assertRaises(IDException):
      raise IDException("boom")


if __name__ == "__main__":
  unittest.main()
