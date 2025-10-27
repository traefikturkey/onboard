from __future__ import annotations

import re
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode


TRACKING_KEYS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "gclid",
    "fbclid",
    "mc_cid",
    "mc_eid",
    "ref",
}


def canonicalize_url(url: str) -> str:
    if not url:
        return ""
    try:
        parts = urlsplit(url.strip())
        scheme = (parts.scheme or "http").lower()
        netloc = parts.netloc.lower()
        # Remove default ports
        netloc = re.sub(r":(80|443)$", "", netloc)
        path = parts.path or "/"
        # Normalize multiple slashes and drop trailing slash (except root)
        path = re.sub(r"//+", "/", path)
        if len(path) > 1 and path.endswith("/"):
            path = path[:-1]
        # Strip tracking params
        q = [
            (k, v)
            for k, v in parse_qsl(parts.query, keep_blank_values=False)
            if k not in TRACKING_KEYS
        ]
        query = urlencode(q, doseq=True)
        frag = ""  # drop fragments
        return urlunsplit((scheme, netloc, path, query, frag))
    except Exception:
        return url
