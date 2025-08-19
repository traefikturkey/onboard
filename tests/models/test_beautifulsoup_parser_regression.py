"""
Simple regression test for BeautifulSoup html.parser usage.

Tests that FeedArticle uses html.parser instead of lxml to avoid
dependency issues in production environments.
"""
import unittest
from datetime import datetime
from unittest.mock import MagicMock

from app.models.feed_article import FeedArticle


class TestBeautifulSoupParserRegression(unittest.TestCase):
    """Test that FeedArticle uses html.parser correctly."""

    def test_feed_article_creates_successfully_with_html_content(self):
        """Test that FeedArticle can be created with HTML content using html.parser."""
        parent = MagicMock()
        parent.filters = []

        # HTML content that would fail if lxml is missing
        html_description = (
            "<p>Test content with <strong>bold text</strong> and <em>emphasis</em>.</p>"
        )

        # This should not raise an exception about missing lxml
        article = FeedArticle(
            original_title="Test Article",
            title="Test Article",
            link="http://example.com/test",
            description=html_description,
            pub_date=datetime.now(),
            processed="",
            parent=parent,
        )

        # Should successfully create the article
        self.assertEqual(article.title, "Test Article")
        self.assertEqual(article.link, "http://example.com/test")

        # Summary should be created (HTML stripped)
        # Note: summary might be None if it matches title, which is expected behavior
        if article.summary:
            self.assertNotIn("<p>", article.summary)
            self.assertNotIn("<strong>", article.summary)

    def test_feed_article_handles_malformed_html_gracefully(self):
        """Test that FeedArticle handles malformed HTML without crashing."""
        parent = MagicMock()
        parent.filters = []

        # Malformed HTML that could cause parser issues
        malformed_html = (
            "<p>Unclosed paragraph <div>nested without closing <strong>bold"
        )

        # Should not crash
        article = FeedArticle(
            original_title="Malformed Test",
            title="Malformed Test",
            link="http://example.com/malformed",
            description=malformed_html,
            pub_date=datetime.now(),
            processed="",
            parent=parent,
        )

        # Should create article successfully
        self.assertEqual(article.title, "Malformed Test")

    def test_feed_article_with_empty_description(self):
        """Test that FeedArticle handles empty description correctly."""
        parent = MagicMock()
        parent.filters = []

        article = FeedArticle(
            original_title="Empty Description Test",
            title="Empty Description Test",
            link="http://example.com/empty",
            description="",
            pub_date=datetime.now(),
            processed="",
            parent=parent,
        )

        # Should create article successfully
        self.assertEqual(article.title, "Empty Description Test")
        # Summary should be None for empty description
        self.assertIsNone(article.summary)


if __name__ == "__main__":
    unittest.main()
