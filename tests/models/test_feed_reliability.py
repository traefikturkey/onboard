import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import requests

from app.models.feed import Feed
from app.models.feed_cache import FeedCache

RSS = b'''<?xml version="1.0"?><rss version="2.0"><channel>
<title>Example</title><link>https://example.com</link><description>News</description>
<item><title>New</title><link>https://example.com/new</link>
<pubDate>Mon, 01 Jan 2024 12:00:00 +0200</pubDate></item>
</channel></rss>'''


@pytest.fixture
def feed(tmp_path):
    return Feed(
        {"name": "Example", "feed_url": "https://example.com/feed"},
        feed_cache=FeedCache("example", working_dir=tmp_path),
        scheduler=SimpleNamespace(running=False),
    )


def response(monkeypatch, status=200, content=RSS, headers=None):
    result = MagicMock()
    result.status_code = status
    result.content = content
    result.url = "https://example.com/feed"
    result.headers = headers or {}
    if status >= 400:
        result.raise_for_status.side_effect = requests.HTTPError(str(status))
    request = MagicMock()
    request.return_value.__enter__.return_value = result
    monkeypatch.setattr("app.models.feed.requests.get", request)
    return request


def test_conditional_refresh_survives_restart_and_304_keeps_articles(feed, monkeypatch):
    modified = "Mon, 01 Jan 2024 10:00:00 GMT"
    request = response(monkeypatch, headers={"ETag": '"v1"', "Last-Modified": modified})
    feed.update()
    assert feed.items[0].pub_date == datetime(2024, 1, 1, 10, tzinfo=timezone.utc)
    assert request.call_args.kwargs["timeout"] == (5, 30)
    saved_articles = json.loads(feed.cache_path.read_text())["articles"]

    restarted = Feed(feed.widget, feed_cache=feed.feed_cache, scheduler=feed.scheduler)
    assert not restarted.needs_update
    previous_check = restarted.last_updated
    request = response(monkeypatch, status=304)
    restarted.update()
    assert request.call_args.kwargs["headers"] == {
        "If-None-Match": '"v1"',
        "If-Modified-Since": modified,
    }
    assert len(restarted.items) == 1
    assert json.loads(feed.cache_path.read_text())["articles"] == saved_articles
    assert restarted.last_updated >= previous_check
    assert restarted.last_updated.tzinfo == timezone.utc


def test_relative_article_links_use_final_response_url(feed, monkeypatch):
    request = response(
        monkeypatch, content=RSS.replace(b"https://example.com/new", b"new")
    )
    request.return_value.__enter__.return_value.url = (
        "https://redirect.example/news/feed.xml"
    )
    feed.update()
    assert feed.items[0].link == "https://redirect.example/news/new"


@pytest.mark.parametrize("failure", ["timeout", "http", "invalid"])
def test_failed_refresh_preserves_successful_cache_and_freshness(
    feed, monkeypatch, failure
):
    response(monkeypatch, headers={"ETag": '"good"'})
    feed.update()
    previous_items = feed.items
    previous_check = feed.last_updated
    previous_cache = feed.cache_path.read_bytes()
    request = response(
        monkeypatch,
        status=503 if failure == "http" else 200,
        content=b"not a feed" if failure == "invalid" else RSS,
        headers={"ETag": '"bad"'},
    )
    if failure == "timeout":
        request.side_effect = requests.Timeout("timed out")
    feed.update()
    assert feed.items is previous_items
    assert feed.last_updated == previous_check
    assert feed.cache_path.read_bytes() == previous_cache
    assert feed._http_metadata["etag"] == '"good"'


def test_legacy_naive_and_offset_dates_sort_and_preserve_all_articles(
    feed, monkeypatch
):
    articles = [
        {
            "title": f"Old {i}",
            "link": f"https://example.com/{i}",
            "pub_date": "2020-01-01T00:00:00",
            "description": "x" * 1024,
        }
        for i in range(400)
    ]
    articles.append(
        {
            "title": "Offset",
            "link": "https://example.com/offset",
            "pub_date": "2020-01-01T03:00:00+02:00",
        }
    )
    feed.feed_cache.save_articles(articles)
    restarted = Feed(feed.widget, feed_cache=feed.feed_cache, scheduler=feed.scheduler)
    assert len(restarted.items) == 401
    assert all(item.pub_date.tzinfo == timezone.utc for item in restarted.items)
    assert restarted.load_cache()[0].title == "Offset"
    response(monkeypatch)
    restarted.update()
    assert len(restarted.items) == 402
    assert len(json.loads(feed.cache_path.read_text())["articles"]) == 402
    assert not restarted.needs_update
    restarted._last_updated = datetime.now(timezone.utc) - timedelta(minutes=11)
    assert restarted.needs_update


def test_scheduling_can_start_after_candidate_is_built(feed):
    scheduler = MagicMock(running=True)
    feed._scheduler = scheduler
    feed.start_scheduling()
    feed.start_scheduling()
    scheduler.add_job.assert_called_once()
