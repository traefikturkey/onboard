import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.models.feed import Feed
from app.models.feed_article import FeedArticle


class TestFeed(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        os.environ["WORKING_STORAGE"] = self.tmpdir.name

    def tearDown(self):
        self.tmpdir.cleanup()
        os.environ.pop("WORKING_STORAGE", None)

    def make_widget(self):
        return {"name": "MoreFeed", "feed_url": "http://example.com/rss", "widgets": []}

    def test_init_parses_filters_and_scheduler_add_job(self):
        widget = self.make_widget()
        # add filters structure expected by Feed
        widget["filters"] = {
            "remove": [{"title": "bad"}],
            "strip": [{"description": "stripme"}],
        }

        # fake scheduler with running True and add_job
        job = MagicMock()
        job.id = "job-1"
        sched = MagicMock()
        sched.running = True
        sched.add_job.return_value = job

        with patch("app.models.widget.Scheduler.getScheduler", return_value=sched):
            f = Feed(widget)

        # scheduler.add_job should have been called and job attached
        sched.add_job.assert_called()
        self.assertIs(f.job, job)
        # filters parsed into list
        self.assertTrue(any(x["type"] == "remove" for x in f.filters))

    def test_load_cache_reads_valid_json(self):
        widget = self.make_widget()
        f = Feed(widget)

        sample = {
            "articles": [
                {
                    "original_title": "o",
                    "title": "t",
                    "link": "l",
                    "description": "d",
                    "pub_date": "Wed, 01 Jan 2020 00:00:00 GMT",
                    "id": "1",
                    "processed": None,
                }
            ]
        }
        # write to cache path
        f.cache_path.write_text(json.dumps(sample))

        res = f.load_cache(f.cache_path)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].title, "t")

    @patch("feedparser.parse")
    def test_download_handles_missing_description(self, mock_parse):
        widget = self.make_widget()
        f = Feed(widget)

        class E:
            def __init__(self):
                self.title = "tt"
                self.link = "ll"
                self.published = "Wed, 01 Jan 2020 00:00:00 GMT"

            def get(self, key, default=None):
                return getattr(self, key, default)

            def __contains__(self, key):
                return hasattr(self, key)

        mock_parse.return_value = MagicMock(entries=[E()])
        articles = f.download("u")
        self.assertEqual(articles[0].description, "")

    def test_refresh_with_no_job_warns(self):
        widget = self.make_widget()
        f = Feed(widget)
        f.job = None
        # patch the module logger.warning used by Feed.refresh
        with patch("app.models.feed.logger.warning") as mock_warn:
            f.refresh()
            mock_warn.assert_called()

    def test_refresh_with_missing_job_attribute_no_raise(self):
        """Ensure refresh() is defensive when the 'job' attribute is missing entirely."""
        widget = self.make_widget()
        f = Feed(widget)
        # remove the attribute if present to simulate older objects
        if hasattr(f, "job"):
            delattr(f, "job")

        with patch("app.models.feed.logger.warning") as mock_warn:
            # should not raise
            f.refresh()
            mock_warn.assert_called()

    # ---- tests migrated from test_feed_extra.py ----
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

    def test_needs_update_returns_true_when_force_update_env_set(self):
        """needs_update returns True when ONBOARD_FEED_FORCE_UPDATE is set."""
        widget = self.make_widget()
        f = Feed(widget)
        f._last_updated = datetime.now()  # recently updated

        with patch.dict(os.environ, {"ONBOARD_FEED_FORCE_UPDATE": "True"}):
            self.assertTrue(f.needs_update)

    def test_needs_update_returns_true_when_never_updated(self):
        """needs_update returns True when last_updated is None."""
        widget = self.make_widget()
        f = Feed(widget)
        f._last_updated = None

        self.assertTrue(f.needs_update)

    def test_needs_update_returns_false_when_recently_updated(self):
        """needs_update returns False when updated less than 10 minutes ago."""
        widget = self.make_widget()
        f = Feed(widget)
        f._last_updated = datetime.now()  # just now

        # Mock the force_update check to return False, then test the time-based logic
        with patch("app.models.feed.os.getenv", return_value=""):
            self.assertFalse(f.needs_update)

    def test_processors_returns_noop_when_processor_file_missing(self):
        """processors() returns NoOpFeedProcessor when processor file doesn't exist."""
        widget = self.make_widget()
        f = Feed(widget)

        # Configure a processor that doesn't exist
        f.widget = {"process": [{"processor": "nonexistent_processor"}]}

        a = FeedArticle(
            original_title="o",
            title="t",
            link="l",
            description="d",
            pub_date=datetime.now(),
            processed="",
            parent=f,
        )
        # Should not raise, should return articles unchanged (NoOpFeedProcessor)
        res = f.processors([a])
        self.assertEqual(len(res), 1)
        # NoOp doesn't modify processed field
        self.assertEqual(res[0].processed, "")

    @patch("feedparser.parse")
    def test_download_handles_entry_without_pubdate(self, mock_parse):
        """download() handles entries without published or updated dates."""
        widget = self.make_widget()
        f = Feed(widget)

        class EntryNoDates:
            def __init__(self):
                self.title = "No dates"
                self.link = "http://example.com"

            def get(self, key, default=None):
                return getattr(self, key, default)

            def __contains__(self, key):
                return hasattr(self, key)

        mock_parse.return_value = MagicMock(entries=[EntryNoDates()])
        articles = f.download("url")
        # Should have created article with current time as fallback
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0].title, "No dates")
        self.assertIsNotNone(articles[0].pub_date)

    @patch("feedparser.parse")
    def test_download_handles_entry_without_link(self, mock_parse):
        """download() handles entries missing link field."""
        widget = self.make_widget()
        f = Feed(widget)

        class EntryNoLink:
            def __init__(self):
                self.title = "No link"
                self.published = "Wed, 01 Jan 2020 00:00:00 GMT"

            def get(self, key, default=None):
                return getattr(self, key, default)

            def __contains__(self, key):
                return hasattr(self, key)

        mock_parse.return_value = MagicMock(entries=[EntryNoLink()])
        articles = f.download("url")
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0].link, "")
