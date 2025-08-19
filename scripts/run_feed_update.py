#!/usr/bin/env python3
"""Utility: run a single Feed.download/update outside the scheduler.

Usage: python scripts/run_feed_update.py [FEED_ID|FEED_URL|FEED_NAME]

If no identifier is passed the script will update the first feed found in
the layout. This script is safe to run locally and prints debugging output
to help diagnose empty downloads.
"""
import logging
import sys
from pathlib import Path

from app.models.layout import Layout


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("run_feed_update")


def find_feed(layout: Layout, identifier: str | None):
    # Try by id, then by url substring, then by name substring
    def iter_widgets():
        for tab in getattr(layout, "tabs", []):
            for row in getattr(tab, "rows", []):
                for column in getattr(row, "columns", []):
                    for widget in getattr(column, "widgets", []):
                        yield widget

    if identifier is None:
        # return first feed widget object
        for w in iter_widgets():
            if getattr(w, "type", None) == "feed":
                return w
        return None

    # exact id using layout.get_feed (fast path)
    try:
        return layout.get_feed(identifier)
    except Exception:
        pass

    # substring matches (feed_url or name)
    for w in iter_widgets():
        if getattr(w, "type", None) != "feed":
            continue
        if identifier in getattr(w, "feed_url", "") or identifier in getattr(w, "name", ""):
            return w

    return None


def main():
    identifier = sys.argv[1] if len(sys.argv) > 1 else None

    # Ensure working dir
    here = Path(__file__).resolve().parents[2]
    logger.debug("Workspace: %s", here)

    layout = Layout()
    # force load
    layout.reload()

    feed = find_feed(layout, identifier)
    if not feed:
        logger.error("No feed found matching '%s'", identifier)
        sys.exit(2)

    logger.info("Found feed: %s (%s)", feed.name, feed.feed_url)

    # Call download() directly to observe parse results
    articles = feed.download(feed.feed_url)
    logger.info("download() returned %d articles", len(articles))
    for i, a in enumerate(articles[:10], start=1):
        logger.info("%d: %s - %s", i, a.title, a.link)

    # Run full update (which saves cache)
    feed.update()
    logger.info("After update, items=%d, cache_path=%s", len(feed.items), feed.cache_path)


if __name__ == "__main__":
    main()
