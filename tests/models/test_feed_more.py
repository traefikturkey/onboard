import json
import os
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.models.feed import Feed


class TestFeedMore(unittest.TestCase):
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
        with patch("logging.warn") as mock_warn:
            f.refresh()
            mock_warn.assert_called()
