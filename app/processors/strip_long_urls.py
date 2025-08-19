import os
import re
from typing import List


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
        env = os.getenv("ONBOARD_STRIP_URL_LENGTH")
        if threshold is not None:
            self.threshold = int(threshold)
        elif env is not None:
            try:
                self.threshold = int(env)
            except Exception:
                self.threshold = 30
        else:
            self.threshold = 30

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

    def process(self, articles: List[object]) -> List[object]:
        for a in articles:
            try:
                title = getattr(a, "title", None)
                if not title:
                    continue

                stripped = self._strip_long_urls(title)
                # Only set the title if we actually removed something or the result is non-empty
                if stripped and stripped != title:
                    a.title = stripped
                elif stripped == "":
                    # If stripping produced an empty string, prefer leaving original title intact
                    # so we don't erase useful content. (This avoids blank titles.)
                    continue
            except Exception:
                # Be defensive: processors should not raise
                continue

        return articles
