import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.models.feed import Feed
from app.models.feed_article import FeedArticle


class TestFeedExtra(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        os.environ["WORKING_STORAGE"] = self.tmpdir.name

    def tearDown(self):
        self.tmpdir.cleanup()
        os.environ.pop("WORKING_STORAGE", None)

    def make_widget(self):
        return {"name": "XFeed", "feed_url": "http://example.com/rss", "widgets": []}

    def test_load_cache_invalid_json_returns_empty(self):
        widget = self.make_widget()
        f = Feed(widget)

        # write invalid json to cache path
        p = Path(self.tmpdir.name) / "bad.json"
        p.write_text("not-a-json")

        # should not raise
        res = f.load_cache(p)
        self.assertEqual(res, [])

    @patch("feedparser.parse")
    def test_download_parses_entries(self, mock_parse):
        widget = self.make_widget()
        f = Feed(widget)

        class DummyEntry:
            def __init__(self, title, link, published, description=None):
                self.title = title
                self.link = link
                self.published = published
                if description is not None:
                    self.description = description

            def get(self, key, default=None):
                return getattr(self, key, default)

            def __contains__(self, key):
                return hasattr(self, key)

        mock_parse.return_value = MagicMock(
            entries=[DummyEntry("t1", "l1", "Mon, 01 Jan 2020 00:00:00 GMT", "d1")]
        )

        articles = f.download("ignored")
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0].title, "t1")
        self.assertEqual(articles[0].link, "l1")

    def test_processors_loads_existing_processor_file(self):
        widget = self.make_widget()
        f = Feed(widget)

        f.widget = {"process": [{"processor": "test_processor"}]}

        a = FeedArticle(
            original_title="o",
            title="t",
            link="l",
            description="d",
            pub_date=datetime.now(),
            processed="",
            parent=f,
        )
        res = f.processors([a])
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].processed, "test_processor")

    def test_remove_duplicate_articles_filters_removed_and_prefers_processed(self):
        widget = self.make_widget()
        f = Feed(widget)

        a1 = MagicMock()
        a1.id = "1"
        a1.processed = None
        a1.removed = True

        a2 = MagicMock()
        a2.id = "1"
        a2.processed = "p"
        a2.removed = False

        a3 = MagicMock()
        a3.id = "2"
        a3.processed = None
        a3.removed = False

        out = f.remove_duplicate_articles([a1, a2, a3])
        ids = set([o.id for o in out])
        self.assertEqual(ids, {"1", "2"})

    def test_save_articles_writes_file_and_formats_dates(self):
        widget = self.make_widget()
        f = Feed(widget)

        a = FeedArticle(
            original_title="o",
            title="t",
            link="l",
            description="d",
            pub_date=datetime(2020, 1, 1),
            processed="",
            parent=f,
        )
        f.save_articles([a])

        self.assertTrue(f.cache_path.exists())
        data = json.loads(f.cache_path.read_text())
        self.assertIn("articles", data)
        self.assertIn("pub_date", data["articles"][0])

    def test_update_calls_download_and_save(self):
        widget = self.make_widget()
        f = Feed(widget)

        with patch.object(
            Feed, "download", return_value=[]
        ) as mock_download, patch.object(
            Feed, "save_articles", return_value=[]
        ) as mock_save:
            f.update()
            mock_download.assert_called_once()
            mock_save.assert_called_once()
