from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Iterable, List, Dict

from .url_tools import canonicalize_url


@dataclass(frozen=True)
class FlatItem:
    url: str
    title: str
    source: str = "bookmark"

    @property
    def item_id(self) -> str:
        return hashlib.sha1(self.url.encode("utf-8")).hexdigest()


def _walk_chrome_nodes(node: dict) -> Iterable[FlatItem]:
    t = node.get("type") or node.get("typeCode")
    if t == "url" or (isinstance(node.get("url"), str) and node.get("url")):
        title = (node.get("name") or node.get("title") or "").strip()
        url = canonicalize_url(node.get("url", ""))
        if url:
            yield FlatItem(url=url, title=title)
    for child in node.get("children", []) or []:
        yield from _walk_chrome_nodes(child)


def flatten_bookmarks(json_path: str) -> List[Dict[str, str]]:
    """
    Parse a Chrome-style bookmarks JSON file and return a deduped flat list:
    [{"url","title","source":"bookmark"}]
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Chrome exports have roots.bookmark_bar and others; accept any root
    roots = data.get("roots") or data
    items: list[FlatItem] = []

    def iter_roots(obj):
        if isinstance(obj, dict):
            for v in obj.values():
                yield v
        elif isinstance(obj, list):
            for v in obj:
                yield v

    for root in iter_roots(roots):
        if isinstance(root, dict):
            items.extend(_walk_chrome_nodes(root))

    # Deduplicate by canonical URL
    seen = set()
    out: List[Dict[str, str]] = []
    for it in items:
        if not it.url or it.url in seen:
            continue
        seen.add(it.url)
        out.append({"url": it.url, "title": it.title, "source": it.source})
    return out
