import os
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from app.models.feed import Feed
from app.models.feed_article import FeedArticle


def make_widget():
  return {"name": "XFeed", "feed_url": "http://example.com/rss", "widgets": []}


def test_feed_uses_feedcache_and_preserves_save_and_load(tmp_path):
  os.environ["WORKING_STORAGE"] = str(tmp_path)
  widget = make_widget()
  f = Feed(widget)

  # create two articles with same id but one processed
  a1 = FeedArticle(
      original_title="o1",
      title="t1",
      link="l1",
      description="d1",
      pub_date=datetime(2020, 1, 1),
      processed=None,
      parent=f,
  )
  a2 = FeedArticle(
      original_title="o2",
      title="t1",
      link="l1",
      description="d2",
      pub_date=datetime(2020, 1, 2),
      processed="p",
      parent=f,
  )

  f.save_articles([a1, a2])

  # Ensure cache file exists
  assert f.cache_path.exists()

  # Load via feed.load_cache (which should use FeedCache underneath)
  loaded = f.load_cache(None)
  # Expect two FeedArticle objects (dedupe keeps one per id)
  assert len(loaded) == 1
  assert loaded[0].processed == "p"

  # Clean up env
  os.environ.pop("WORKING_STORAGE", None)
