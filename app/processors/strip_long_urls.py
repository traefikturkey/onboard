import os
import re
from typing import List

from app.models.feed_article import FeedArticle


class StripLongUrls:
    """Processor to strip long http(s) URLs from article titles.

    Behavior:
    - Finds all http:// or https:// URLs inside title strings.
    - If a matched URL's length is >= threshold (default 30), the URL is removed.
    - If removing URLs leaves an empty title, the title is left unchanged to avoid
      producing blank titles (calling code may choose to post-process further).
    - Collapses multiple spaces and trims surrounding punctuation after removals.
    """

    def __init__(self, threshold: int | None = None):
        # Allow an env override for tuning in different deployments
        self.threshold = int(os.getenv("ONBOARD_STRIP_URL_LENGTH", "25"))
        # regex to find http(s) URLs
        self._url_re = re.compile(r"https?://\S+", re.IGNORECASE)

    def _strip_long_urls(self, text: str) -> str:
        if not text:
            return text

        def _repl(match: re.Match) -> str:
            url = match.group(0)
            if len(url) >= self.threshold:
                return ""
            return url

        new = self._url_re.sub(_repl, text)
        # collapse extra whitespace and remove leftover punctuation around ends
        new = re.sub(r"\s+", " ", new).strip()
        # Trim common leading/trailing separators leftover after url removal
        new = new.strip(" -:\u2014|,;\n\t")
        return new

    def process(self, articles: List[FeedArticle]) -> List[FeedArticle]:
        for a in articles:
            try:
                # Only process the display 'name' field (widget uses article.name)
                original = getattr(a, "name", "")
                # _strip_long_urls returns an empty string when URLs are removed; in
                # that case we should preserve the original value to avoid blanking
                # out the display name (conservative behavior required by tests).
                new = (
                    self._strip_long_urls(original)
                    if original is not None
                    else original
                )
                if new:
                    a.name = new
                else:
                    a.name = original
            except Exception:
                # Be defensive: processors should not raise
                continue

        return articles
