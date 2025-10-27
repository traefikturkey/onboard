from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass
from html import unescape
from typing import Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class Extracted:
    title: str
    text: str
    content_hash: str


class TextExtractor:
    def __init__(self, timeout: float = 8.0, user_agent: str = "OnboardBot/1.0"):
        self.timeout = timeout
        self.user_agent = user_agent

    def _fetch(self, url: str) -> Optional[str]:
        try:
            headers = {"User-Agent": self.user_agent}
            resp = requests.get(url, headers=headers, timeout=self.timeout)
            if resp.ok and resp.text:
                return resp.text
        except Exception as e:
            logger.debug("fetch error: %s", e)
        return None

    def _extract_readability(self, html: str) -> tuple[str, str]:
        try:
            from readability import Document  # type: ignore

            doc = Document(html)
            title = (doc.short_title() or "").strip()
            content_html = doc.summary(html_partial=True)
            text = _strip_html(content_html)
            return title, text
        except Exception:
            return _basic_title(html), _strip_html(html)

    def extract(self, url: str) -> Extracted:
        html = self._fetch(url)
        if not html:
            time.sleep(0.1)
            html = self._fetch(url)
        if not html:
            title = url
            text = ""
        else:
            title, text = self._extract_readability(html)
        text = text[:10000]
        payload = (title or "").strip() + "\n\n" + (text or "").strip()
        content_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return Extracted(title=title or "", text=text or "", content_hash=content_hash)


def _strip_html(html: str) -> str:
    import re

    html = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.IGNORECASE)
    html = re.sub(r"<style[\s\S]*?</style>", " ", html, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", html)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _basic_title(html: str) -> str:
    import re

    m = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    if m:
        return unescape(m.group(1)).strip()
    return ""
