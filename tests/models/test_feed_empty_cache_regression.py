"""
Regression tests for Feed initialization with empty cache.

Tests the scenario where a Feed is initialized in a production environment
with no cached files, ensuring automatic updates are triggered correctly.
"""
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from app.models.feed import Feed


class TestFeedEmptyCache(unittest.TestCase):
    """Test Feed behavior when no cache files exist (production scenario)."""

    def setUp(self):
        """Set up test fixtures with clean temporary directory."""
        self.tmpdir = tempfile.TemporaryDirectory()
        os.environ["WORKING_STORAGE"] = self.tmpdir.name

        # Basic widget configuration
        self.widget_config = {
            "name": "Test Feed",
            "feed_url": "http://example.com/rss",
            "display_limit": 10,
        }

    def tearDown(self):
        """Clean up test fixtures."""
        self.tmpdir.cleanup()
        os.environ.pop("WORKING_STORAGE", None)

    def test_feed_init_with_no_cache_has_empty_items(self):
        """Test that Feed initialization with no cache results in empty items list."""
        # Mock scheduler to avoid actual scheduling
        mock_scheduler = MagicMock()
        mock_scheduler.running = False  # Disable scheduler for this test

        with patch(
            "app.models.widget.Scheduler.getScheduler", return_value=mock_scheduler
        ):
            feed = Feed(self.widget_config)

        # Feed should initialize with empty items when no cache exists
        self.assertEqual(len(feed.items), 0)
        self.assertIsNone(feed.last_updated)

    def test_feed_needs_update_when_no_cache(self):
        """Test that needs_update returns True when there's no cache (last_updated is None)."""
        mock_scheduler = MagicMock()
        mock_scheduler.running = False

        with patch(
            "app.models.widget.Scheduler.getScheduler", return_value=mock_scheduler
        ):
            feed = Feed(self.widget_config)

        # needs_update should return True when last_updated is None
        self.assertTrue(feed.needs_update)

    def test_feed_triggers_refresh_when_scheduler_running_and_needs_update(self):
        """Test that Feed automatically triggers refresh when scheduler is running and needs update."""
        mock_job = MagicMock()
        mock_job.id = "test-job-id"

        mock_scheduler = MagicMock()
        mock_scheduler.running = True
        mock_scheduler.add_job.return_value = mock_job

        with patch(
            "app.models.widget.Scheduler.getScheduler", return_value=mock_scheduler
        ):
            with patch.object(Feed, 'refresh') as mock_refresh:
                feed = Feed(self.widget_config)

        # Should have called refresh because needs_update=True and scheduler.running=True
        mock_refresh.assert_called_once()

        # Should have added a cron job
        mock_scheduler.add_job.assert_called_once()
        self.assertEqual(feed.job, mock_job)

    def test_feed_display_items_empty_when_no_cache(self):
        """Test that display_items is empty when feed has no cached articles."""
        mock_scheduler = MagicMock()
        mock_scheduler.running = False

        with patch(
            "app.models.widget.Scheduler.getScheduler", return_value=mock_scheduler
        ):
            feed = Feed(self.widget_config)

        # display_items should yield no items
        display_items = list(feed.display_items)
        self.assertEqual(len(display_items), 0)

    def test_feed_download_saves_to_cache(self):
        """Test that feed download saves articles to cache file."""
        mock_scheduler = MagicMock()
        mock_scheduler.running = False

        # Mock feedparser to return sample data
        mock_feed_data = MagicMock()
        mock_feed_data.entries = [
            {
                "title": "Test Article 1",
                "link": "http://example.com/article1",
                "description": "Test description 1",
                "published_parsed": None,
            },
            {
                "title": "Test Article 2",
                "link": "http://example.com/article2",
                "description": "Test description 2",
                "published_parsed": None,
            },
        ]
        mock_feed_data.bozo = False

        with patch(
            "app.models.widget.Scheduler.getScheduler", return_value=mock_scheduler
        ):
            with patch("app.models.feed.feedparser.parse", return_value=mock_feed_data):
                feed = Feed(self.widget_config)

                # Download should return articles
                articles = feed.download(feed.feed_url)

                self.assertEqual(len(articles), 2)
                self.assertEqual(articles[0].title, "Test Article 1")
                self.assertEqual(articles[1].title, "Test Article 2")

    def test_feed_update_populates_items_from_download(self):
        """Test that feed.update() downloads articles and populates feed.items."""
        mock_scheduler = MagicMock()
        mock_scheduler.running = False

        # Mock feedparser
        mock_feed_data = MagicMock()
        mock_feed_data.entries = [
            {
                "title": "Downloaded Article",
                "link": "http://example.com/downloaded",
                "description": "Downloaded content",
                "published_parsed": None,
            }
        ]
        mock_feed_data.bozo = False

        with patch(
            "app.models.widget.Scheduler.getScheduler", return_value=mock_scheduler
        ):
            with patch("app.models.feed.feedparser.parse", return_value=mock_feed_data):
                feed = Feed(self.widget_config)

                # Verify feed starts empty
                self.assertEqual(len(feed.items), 0)

                # Call update to populate
                feed.update()

                # Should now have items
                self.assertEqual(len(feed.items), 1)
                self.assertEqual(feed.items[0].title, "Downloaded Article")

    @patch.dict(os.environ, {"ONBOARD_FEED_FORCE_UPDATE": "True"})
    def test_feed_needs_update_with_force_update_env(self):
        """Test that needs_update returns True when ONBOARD_FEED_FORCE_UPDATE is set."""
        mock_scheduler = MagicMock()
        mock_scheduler.running = False

        with patch(
            "app.models.widget.Scheduler.getScheduler", return_value=mock_scheduler
        ):
            feed = Feed(self.widget_config)

        # Should need update due to environment variable
        self.assertTrue(feed.needs_update)

    def test_feed_cache_path_created_on_init(self):
        """Test that feed cache directory structure is created during initialization."""
        mock_scheduler = MagicMock()
        mock_scheduler.running = False

        with patch(
            "app.models.widget.Scheduler.getScheduler", return_value=mock_scheduler
        ):
            feed = Feed(self.widget_config)

        # Cache path should be set
        self.assertIsNotNone(feed.cache_path)

        # Cache directory should exist (created by FeedCache)
        self.assertTrue(feed.cache_path.parent.exists())


if __name__ == "__main__":
    unittest.main()
