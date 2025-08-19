"""
Regression tests for Widget template rendering with empty feeds.

Tests that widget templates correctly render "No articles yet" message
instead of "Loading..." when feeds have no articles.
"""
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from flask import Flask, render_template_string

from app.models.feed import Feed


class TestWidgetTemplateRegression(unittest.TestCase):
    """Test Widget template rendering for feeds with no articles."""

    def setUp(self):
        """Set up test fixtures."""
        self.tmpdir = tempfile.TemporaryDirectory()
        os.environ["WORKING_STORAGE"] = self.tmpdir.name

        # Create a minimal Flask app for template testing
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True

        self.widget_config = {
            "name": "Test Feed",
            "feed_url": "http://example.com/rss",
            "display_limit": 10,
        }

    def tearDown(self):
        """Clean up test fixtures."""
        self.tmpdir.cleanup()
        os.environ.pop("WORKING_STORAGE", None)

    def test_widget_template_shows_no_articles_message_when_empty(self):
        """Test that widget template shows 'No articles yet' when feed has no articles."""
        # Simplified widget template (key parts only)
        template = '''
        <div class="box-content feed-content">
          <ul>
            {% for article in widget.display_items %}
            <li>{{ article.name }}</li>
            {% else %}
            <li>No articles yet - feeds will update automatically</li>
            {% endfor %}
          </ul>
        </div>
        '''

        mock_scheduler = MagicMock()
        mock_scheduler.running = False

        with patch(
            "app.models.widget.Scheduler.getScheduler", return_value=mock_scheduler
        ):
            feed = Feed(self.widget_config)

        with self.app.app_context():
            rendered = render_template_string(template, widget=feed)

        # Should show the "No articles yet" message
        self.assertIn("No articles yet - feeds will update automatically", rendered)
        self.assertNotIn("Loading...", rendered)

    def test_widget_template_shows_articles_when_populated(self):
        """Test that widget template shows articles when feed has content."""
        template = '''
        <div class="box-content feed-content">
          <ul>
            {% for article in widget.display_items %}
            <li>{{ article.name }}</li>
            {% else %}
            <li>No articles yet - feeds will update automatically</li>
            {% endfor %}
          </ul>
        </div>
        '''

        mock_scheduler = MagicMock()
        mock_scheduler.running = False

        # Mock feedparser to return articles
        mock_feed_data = MagicMock()
        mock_feed_data.entries = [
            {
                "title": "Test Article 1",
                "link": "http://example.com/article1",
                "description": "Description 1",
                "published_parsed": None,
            },
            {
                "title": "Test Article 2",
                "link": "http://example.com/article2",
                "description": "Description 2",
                "published_parsed": None,
            },
        ]
        mock_feed_data.bozo = False

        with patch(
            "app.models.widget.Scheduler.getScheduler", return_value=mock_scheduler
        ):
            with patch("app.models.feed.feedparser.parse", return_value=mock_feed_data):
                feed = Feed(self.widget_config)
                # Manually populate feed with articles (simulating after update)
                feed.update()

        with self.app.app_context():
            rendered = render_template_string(template, widget=feed)

        # Should show the articles, not the "No articles yet" message
        self.assertIn("Test Article 1", rendered)
        self.assertIn("Test Article 2", rendered)
        self.assertNotIn("No articles yet", rendered)
        self.assertNotIn("Loading...", rendered)

    def test_widget_template_with_skip_htmx_false_shows_loading(self):
        """Test that widget template shows Loading when skip_htmx=False (HTMX mode)."""
        # Template with HTMX behavior (skip_htmx=False)
        template = '''
        {% if not skip_htmx and widget.hx_get %}
        <div hx-get="{{ widget.hx_get }}">
          <ul><li>Loading...</li></ul>
        </div>
        {% else %}
        <div class="box-content">
          <ul>
            {% for article in widget.display_items %}
            <li>{{ article.name }}</li>
            {% else %}
            <li>No articles yet - feeds will update automatically</li>
            {% endfor %}
          </ul>
        </div>
        {% endif %}
        '''

        mock_scheduler = MagicMock()
        mock_scheduler.running = False

        with patch(
            "app.models.widget.Scheduler.getScheduler", return_value=mock_scheduler
        ):
            feed = Feed(self.widget_config)

        with self.app.app_context():
            # Test with skip_htmx=False (HTMX loading mode)
            rendered = render_template_string(template, widget=feed, skip_htmx=False)

        # Should show Loading... in HTMX mode
        self.assertIn("Loading...", rendered)

    def test_widget_template_with_skip_htmx_true_shows_content(self):
        """Test that widget template shows actual content when skip_htmx=True."""
        # Template with HTMX behavior but skip_htmx=True
        template = '''
        {% if not skip_htmx and widget.hx_get %}
        <div hx-get="{{ widget.hx_get }}">
          <ul><li>Loading...</li></ul>
        </div>
        {% else %}
        <div class="box-content">
          <ul>
            {% for article in widget.display_items %}
            <li>{{ article.name }}</li>
            {% else %}
            <li>No articles yet - feeds will update automatically</li>
            {% endfor %}
          </ul>
        </div>
        {% endif %}
        '''

        mock_scheduler = MagicMock()
        mock_scheduler.running = False

        with patch(
            "app.models.widget.Scheduler.getScheduler", return_value=mock_scheduler
        ):
            feed = Feed(self.widget_config)

        with self.app.app_context():
            # Test with skip_htmx=True (direct content mode - what feed endpoints use)
            rendered = render_template_string(template, widget=feed, skip_htmx=True)

        # Should show "No articles yet" message, not Loading...
        self.assertIn("No articles yet - feeds will update automatically", rendered)
        self.assertNotIn("Loading...", rendered)

    def test_feed_has_hx_get_attribute(self):
        """Test that Feed objects have hx_get attribute set correctly."""
        mock_scheduler = MagicMock()
        mock_scheduler.running = False

        with patch(
            "app.models.widget.Scheduler.getScheduler", return_value=mock_scheduler
        ):
            feed = Feed(self.widget_config)

        # Feed should have hx_get attribute set
        self.assertIsNotNone(feed.hx_get)
        self.assertTrue(feed.hx_get.startswith("/feed/"))
        # Should contain the feed ID
        self.assertIn(feed.id, feed.hx_get)


if __name__ == "__main__":
    unittest.main()
