"""
Integration tests for the complete feed loading workflow.

Tests the end-to-end process of feed initialization, download, and caching
to prevent regressions in the production feed loading scenario.
"""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import pytest

from app.models.feed import Feed
from app.models.layout import Layout

# mark this module as integration so pytest -m "not integration" will deselect it
pytestmark = pytest.mark.integration


class TestFeedIntegrationRegression(unittest.TestCase):
    """Integration tests for feed loading workflow."""

    def setUp(self):
        """Set up test fixtures with clean environment."""
        self.tmpdir = tempfile.TemporaryDirectory()
        os.environ["WORKING_STORAGE"] = self.tmpdir.name

        # Sample feed configuration
        self.feed_config = {
            "name": "Test RSS Feed",
            "feed_url": "http://example.com/rss.xml",
            "display_limit": 5,
        }

    def tearDown(self):
        """Clean up test fixtures."""
        self.tmpdir.cleanup()
        os.environ.pop("WORKING_STORAGE", None)

    def test_complete_feed_workflow_from_empty_cache(self):
        """Test complete workflow: empty cache -> download -> cache -> display."""
        # Mock scheduler
        mock_scheduler = MagicMock()
        mock_scheduler.running = False

        # Mock RSS feed data
        mock_feed_data = MagicMock()
        mock_feed_data.entries = [
            {
                "title": "Article 1: Important News",
                "link": "http://example.com/article1",
                "description": "<p>This is the <strong>first</strong> article description.</p>",
                "published_parsed": None,
            },
            {
                "title": "Article 2: Breaking Update",
                "link": "http://example.com/article2",
                "description": "<p>Second article with <em>emphasis</em> and content.</p>",
                "published_parsed": None,
            },
            {
                "title": "Article 3: Analysis",
                "link": "http://example.com/article3",
                "description": "Simple text description without HTML.",
                "published_parsed": None,
            },
        ]
        mock_feed_data.bozo = False

        with patch(
            "app.models.widget.Scheduler.getScheduler", return_value=mock_scheduler
        ):
            with patch("app.models.feed.feedparser.parse", return_value=mock_feed_data):
                # Step 1: Initialize feed with empty cache
                feed = Feed(self.feed_config)

                # Initially should be empty
                self.assertEqual(len(feed.items), 0)
                self.assertTrue(feed.needs_update)

                # Step 2: Download articles (simulates what happens on refresh)
                articles = feed.download(feed.feed_url)

                # Should have downloaded articles
                self.assertEqual(len(articles), 3)
                self.assertEqual(articles[0].title, "Article 1: Important News")

                # Articles should have processed HTML descriptions
                # (This tests our html.parser fix)
                self.assertIsNotNone(articles[0].summary)
                if articles[0].summary:
                    self.assertNotIn("<p>", articles[0].summary)
                    self.assertNotIn("<strong>", articles[0].summary)

                # Step 3: Update feed (download + save to cache)
                feed.update()

                # Feed should now have items
                self.assertEqual(len(feed.items), 3)
                self.assertEqual(feed.items[0].title, "Article 1: Important News")

                # Step 4: Test display_items (respects display_limit)
                display_items = list(feed.display_items)
                self.assertEqual(len(display_items), 3)  # All 3 since limit is 5

                # Step 5: Cache file should exist and contain articles
                self.assertTrue(feed.cache_path.exists())

                # Step 6: Create new feed instance and verify it loads from cache
                feed2 = Feed(self.feed_config)
                self.assertEqual(len(feed2.items), 3)
                self.assertEqual(feed2.items[0].title, "Article 1: Important News")

    def test_feed_article_html_parsing_regression(self):
        """Test that FeedArticle can handle HTML parsing without lxml dependency."""
        mock_scheduler = MagicMock()
        mock_scheduler.running = False

        # Test various HTML scenarios that could break with missing lxml
        html_scenarios = [
            "<p>Simple paragraph</p>",
            "<div><p>Nested <strong>tags</strong></p></div>",
            "Malformed HTML <p>without closing",
            "&lt;escaped&gt; HTML &amp; entities",
            "",  # Empty description
            "   \n\t   ",  # Whitespace only
        ]

        mock_feed_data = MagicMock()
        mock_feed_data.entries = [
            {
                "title": f"Article {i}",
                "link": f"http://example.com/article{i}",
                "description": desc,
                "published_parsed": None,
            }
            for i, desc in enumerate(html_scenarios, 1)
        ]
        mock_feed_data.bozo = False

        with patch(
            "app.models.widget.Scheduler.getScheduler", return_value=mock_scheduler
        ):
            with patch("app.models.feed.feedparser.parse", return_value=mock_feed_data):
                feed = Feed(self.feed_config)

                # Should not crash during download/parsing
                articles = feed.download(feed.feed_url)

                # Should have created articles for all scenarios
                self.assertEqual(len(articles), len(html_scenarios))

                # All articles should be valid FeedArticle objects
                for article in articles:
                    self.assertIsNotNone(article.title)
                    self.assertIsNotNone(article.link)
                    # summary can be None for empty/whitespace descriptions

    def test_feed_update_in_production_scenario(self):
        """Test that feed initialization properly triggers updates when scheduler is running."""
        # Mock job for scheduler
        mock_job = MagicMock()
        mock_job.id = "feed-job-123"

        # Mock running scheduler (production scenario)
        mock_scheduler = MagicMock()
        mock_scheduler.running = True
        mock_scheduler.add_job.return_value = mock_job

        # Mock feedparser for the auto-triggered update
        mock_feed_data = MagicMock()
        mock_feed_data.entries = [
            {
                "title": "Auto-loaded Article",
                "link": "http://example.com/auto",
                "description": "Automatically loaded on init",
                "published_parsed": None,
            }
        ]
        mock_feed_data.bozo = False

        with patch(
            "app.models.widget.Scheduler.getScheduler", return_value=mock_scheduler
        ):
            with patch("app.models.feed.feedparser.parse", return_value=mock_feed_data):
                with patch.object(Feed, 'refresh') as mock_refresh:
                    # Initialize feed (should trigger refresh due to needs_update=True)
                    feed = Feed(self.feed_config)

        # Should have scheduled a cron job
        mock_scheduler.add_job.assert_called_once()

        # Should have called refresh because needs_update=True in empty cache scenario
        mock_refresh.assert_called_once()

        # Feed should have the job attached
        self.assertEqual(feed.job, mock_job)

    def test_layout_integration_with_empty_feeds(self):
        """Test Layout loading with feeds that have no cached data."""
        # Create a minimal layout YAML configuration
        layout_config = {
            "tabs": [
                {
                    "tab": "News",
                    "rows": [
                        {
                            "columns": [
                                {
                                    "widgets": [
                                        {
                                            "type": "feed",
                                            "name": "Test Feed 1",
                                            "feed_url": "http://example.com/feed1.xml",
                                            "display_limit": 10,
                                        },
                                        {
                                            "type": "feed",
                                            "name": "Test Feed 2",
                                            "feed_url": "http://example.com/feed2.xml",
                                            "display_limit": 5,
                                        },
                                    ]
                                }
                            ]
                        }
                    ],
                }
            ]
        }

        mock_scheduler = MagicMock()
        mock_scheduler.running = False

        with patch(
            "app.models.widget.Scheduler.getScheduler", return_value=mock_scheduler
        ):
            with patch.object(
                Layout, '_load_layout_from_file', return_value=layout_config
            ):
                # This should not crash even with no cached feeds
                layout = Layout()

                # Should have loaded feeds
                feeds = []
                for tab in layout.tabs:
                    for row in tab.rows:
                        for column in row.columns:
                            feeds.extend(layout.get_feeds(column))

                self.assertEqual(len(feeds), 2)

                # All feeds should have empty items initially
                for feed in feeds:
                    self.assertEqual(len(feed.items), 0)
                    self.assertTrue(feed.needs_update)


if __name__ == "__main__":
    unittest.main()
