"""
Regression tests for FeedArticle HTML parsing issues.

Tests that FeedArticle constructor properly handles HTML parsing
with different parsers and gracefully handles parsing failures.
"""
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.models.feed_article import FeedArticle


class TestFeedArticleHTMLParsing(unittest.TestCase):
    """Test FeedArticle HTML parsing resilience and parser compatibility."""

    def setUp(self):
        """Set up test fixtures."""
        self.parent = MagicMock()
        self.parent.filters = []
        self.base_args = {
            "original_title": "Test Article",
            "title": "Test Article",
            "link": "http://example.com/article",
            "pub_date": datetime.now(),
            "processed": "",
            "parent": self.parent,
        }

    def test_html_parser_works_with_simple_html(self):
        """Test that html.parser correctly processes simple HTML descriptions."""
        description = "<p>This is a <strong>test</strong> article with HTML.</p>"

        article = FeedArticle(description=description, **self.base_args)

        # Should successfully create article and extract text from HTML
        self.assertIsNotNone(article.summary)
        if article.summary:
            self.assertNotIn("<p>", article.summary)
            self.assertNotIn("<strong>", article.summary)
            self.assertIn("test article", article.summary)

    def test_html_parser_works_with_complex_html(self):
        """Test html.parser with more complex HTML structures."""
        description = """
        <div class="article-content">
            <p>This is the <em>first paragraph</em> with some content.</p>
            <p>This is the second paragraph with <a href="link">a link</a>.</p>
            <ul>
                <li>List item 1</li>
                <li>List item 2</li>
            </ul>
        </div>
        """

        article = FeedArticle(description=description, **self.base_args)

        # Should extract clean text without HTML tags
        self.assertIsNotNone(article.summary)
        self.assertNotIn("<div>", article.summary)
        self.assertNotIn("<p>", article.summary)
        self.assertNotIn("<ul>", article.summary)
        self.assertIn("first paragraph", article.summary)

    def test_html_parser_handles_malformed_html(self):
        """Test that html.parser gracefully handles malformed HTML."""
        description = "<p>Unclosed paragraph <strong>bold text <em>nested emphasis"

        article = FeedArticle(description=description, **self.base_args)

        # Should not crash and should extract some text
        self.assertIsNotNone(article.summary)
        self.assertIn("Unclosed paragraph", article.summary)

    def test_html_parser_handles_empty_description(self):
        """Test behavior with empty description."""
        article = FeedArticle(description="", **self.base_args)

        # Should handle empty description gracefully
        self.assertIsNone(article.summary)

    def test_html_parser_handles_whitespace_only_description(self):
        """Test behavior with whitespace-only description."""
        article = FeedArticle(description="   \n\t   ", **self.base_args)

        # Should handle whitespace-only description gracefully
        self.assertIsNone(article.summary)

    def test_html_parser_with_entities(self):
        """Test HTML entity decoding with html.parser."""
        description = (
            "&lt;p&gt;This has HTML entities: &amp;amp; &quot;quoted&quot;&lt;/p&gt;"
        )

        article = FeedArticle(description=description, **self.base_args)

        # Should decode HTML entities properly
        self.assertIsNotNone(article.summary)
        self.assertIn("&", article.summary)
        self.assertIn('"quoted"', article.summary)

    def test_lxml_fallback_compatibility(self):
        """Test that if lxml is unavailable, html.parser is used successfully."""
        # This test ensures our fix works - if someone accidentally uses lxml again,
        # and it's not available, the test will catch it
        description = "<p>Test <strong>content</strong> for parser compatibility.</p>"

        # Mock BeautifulSoup to simulate lxml being unavailable
        with patch('app.models.feed_article.BeautifulSoup') as mock_bs:

            def side_effect(html, parser):
                if parser == "lxml":
                    from bs4.exceptions import FeatureNotFound

                    raise FeatureNotFound("lxml not available")
                # Fall back to actual BeautifulSoup with html.parser
                from bs4 import BeautifulSoup

                return BeautifulSoup(html, "html.parser")

            mock_bs.side_effect = side_effect

            # This should not raise an exception
            FeedArticle(description=description, **self.base_args)

            # Verify that BeautifulSoup was called with html.parser
            mock_bs.assert_called()
            args, kwargs = mock_bs.call_args
            self.assertEqual(args[1], "html.parser")

    def test_summary_generation_with_long_description(self):
        """Test summary generation with long HTML descriptions."""
        # Create a long description that would be truncated
        long_content = " ".join([f"Sentence {i} with some content." for i in range(20)])
        description = f"<p>{long_content}</p>"

        article = FeedArticle(description=description, **self.base_args)

        # Should create a summary (implementation may truncate)
        self.assertIsNotNone(article.summary)
        self.assertIn("Sentence", article.summary)

    def test_summary_None_when_same_as_title(self):
        """Test that summary is None when it matches the title."""
        title = "This is the article title"
        description = f"<p>{title}</p>"
        # Avoid passing duplicate 'title' via base_args; create a shallow copy without title
        base_args_copy = dict(self.base_args)
        base_args_copy.pop("title", None)

        article = FeedArticle(title=title, description=description, **base_args_copy)

        # Summary should be None when it's the same as title
        self.assertIsNone(article.summary)


if __name__ == "__main__":
    unittest.main()
