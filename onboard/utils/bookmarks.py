from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Iterable, List, Dict, Any

from .url_tools import canonicalize_url


@dataclass(frozen=True)
class FlatItem:
    url: str
    title: str
    source: str = "bookmark"

    @property
    def item_id(self) -> str:
        return hashlib.sha1(self.url.encode("utf-8")).hexdigest()


def _walk_chrome_nodes(node: Dict[str, Any]) -> Iterable[FlatItem]:
    """Walk various bookmark JSON shapes and yield flat items.

    Supports:
    - Chrome export style: children in "children", URL in "url"
    - This repo's config style: children in "contents", URL in "href"
    - Titles in either "name" or "title"
    """
    # Resolve potential URL fields
    url_raw = node.get("url") or node.get("href")
    if isinstance(url_raw, str) and url_raw:
        title = (node.get("name") or node.get("title") or "").strip()
        url = canonicalize_url(url_raw)
        if url:
            yield FlatItem(url=url, title=title)

    # Recurse into potential children containers
    children = node.get("children") or node.get("contents") or []
    if isinstance(children, list):
        for child in children:
            if isinstance(child, dict):
                yield from _walk_chrome_nodes(child)


def flatten_bookmarks(json_path: str) -> List[Dict[str, str]]:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        # Chrome export uses top-level "roots"; our config may be the dict itself
        roots = data.get("roots") or data
    else:
        # List root (as in this repo's bookmarks_bar.json)
        roots = data
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

    seen = set()
    out: List[Dict[str, str]] = []
    for it in items:
        if not it.url or it.url in seen:
            continue
        seen.add(it.url)
        out.append(
            {
                "url": it.url,
                "title": it.title,
                "source": it.source,
                "item_id": it.item_id,
            }
        )
    return out
