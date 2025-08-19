#!/usr/bin/env python3

import sys
import os

# Add the app directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from models.layout import Layout
from models.feed_cache import FeedCache

def debug_feed_cache():
    print("Loading layout...")
    layout = Layout()

    # Get a specific feed
    feed_id = "tLpigiHqXoGa1pfAK0IEQDfM"  # Lawrence Person's BattleSwarm Blog
    feed = layout.get_feed(feed_id)

    print(f"Feed: {feed.name}")
    print(f"Feed ID: {feed.id}")
    print(f"Cache path: {feed.cache_path}")
    print(f"Cache path exists: {os.path.exists(feed.cache_path)}")

    if os.path.exists(feed.cache_path):
        print(f"Cache file size: {os.path.getsize(feed.cache_path)} bytes")

    print(f"Number of items loaded: {len(feed.items)}")
    print(f"Display limit: {feed.display_limit}")

    if feed.items:
        print(f"First item: {feed.items[0].title}")
        print("Display items:")
        for i, item in enumerate(feed.display_items):
            print(f"  {i+1}. {item.title}")
            if i >= 4:  # Show first 5
                print(f"  ... and {len(list(feed.display_items)) - 5} more")
                break
    else:
        print("No items found in feed!")

        # Try loading cache directly
        print("\nTrying to load cache directly...")
        cache = FeedCache(feed_id)
        cached_items = cache.load_cache(archive_on_load=False)
        print(f"Direct cache load returned {len(cached_items)} items")
        if cached_items:
            print(f"First cached item: {cached_items[0].get('title', 'No title')}")

if __name__ == "__main__":
    debug_feed_cache()
