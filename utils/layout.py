from __future__ import annotations

import hashlib
import yaml
from typing import Any, Dict, List

from .url_tools import canonicalize_url


def _extract_from_node(node: Any, out: List[Dict[str, str]]):
    if isinstance(node, dict):
        # Common widget shapes: {type: 'bookmarks', items: [{title, url}]}
        node_type = str(node.get("type", "")).lower()
        if node_type in {"bookmark", "bookmarks", "bookmark_list"}:
            items = node.get("items") or node.get("links") or []
            for it in items:
                if not isinstance(it, dict):
                    continue
                url = canonicalize_url(str(it.get("url", "")))
                title = str(it.get("title") or it.get("name") or "").strip()
                if url:
                    out.append({"url": url, "title": title, "source": "bookmark"})
        # Recurse common containers
        for key in ("widgets", "rows", "columns", "children", "items"):
            child = node.get(key)
            if child:
                _extract_from_node(child, out)
    elif isinstance(node, list):
        for v in node:
            _extract_from_node(v, out)


def extract_bookmark_widgets(yaml_path: str) -> List[Dict[str, str]]:
    """
    Traverse a layout YAML and return bookmark-like entries with fields:
    {"url","title","source":"bookmark"}
    """
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    out: List[Dict[str, str]] = []
    _extract_from_node(data, out)
    # Deduplicate by canonical URL
    seen = set()
    deduped: List[Dict[str, str]] = []
    for it in out:
        url = it.get("url")
        if not url or url in seen:
            continue
        seen.add(url)
        deduped.append(it)
    return deduped


def compute_item_id(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()
