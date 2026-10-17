import types

import pytest

import app.main as app_module


class FakeFeed:
    def __init__(self, template="widget.html"):
        self.template = template


class FakeLayout:
    def __init__(self):
        self.favicon_path = "/static/img/favicon.ico"
        self._refreshed = []
        self._reloaded = False

    def is_modified(self):
        return False

    def reload(self):
        self._reloaded = True

    def get_feed(self, feed_id):
        return FakeFeed()

    def get_link(self, feed_id, link_id):
        return "http://example.com"

    def refresh_feeds(self, feed_id):
        self._refreshed.append(feed_id)

    def tab(self, tab_name=None):
        # minimal object with rows for the index template iteration
        return types.SimpleNamespace(rows=[])


class DummyDF:
    def to_html(self, classes=None, index=False):
        return "<table class='data'></table>"


def test_index_and_tab():
    app_module.layout = FakeLayout()
    client = app_module.app.test_client()

    r = client.get("/")
    assert r.status_code == 200

    r2 = client.get("/tab/testtab")
    assert r2.status_code == 200


def test_feed_route():
    app_module.layout = FakeLayout()
    client = app_module.app.test_client()

    r = client.get("/feed/someid")
    assert r.status_code == 200
    assert b"<html" in r.data or b"<div" in r.data


def test_click_events(monkeypatch):
    monkeypatch.setattr(
        app_module,
        "link_tracker",
        types.SimpleNamespace(get_click_events=lambda: DummyDF()),
    )
    app_module.layout = FakeLayout()
    client = app_module.app.test_client()

    r = client.get("/click_events")
    assert r.status_code == 200
    assert r.headers["Content-Type"] == "text/html"
    assert b"<table" in r.data


@pytest.mark.parametrize("method", ["GET", "POST"])
def test_track_redirect(monkeypatch, method):
    called = {}

    def fake_track(feed_id, link_id, link):
        called["args"] = (feed_id, link_id, link)

    monkeypatch.setattr(
        app_module, "link_tracker", types.SimpleNamespace(track_click_event=fake_track)
    )
    app_module.layout = FakeLayout()
    client = app_module.app.test_client()

    r = client.open("/redirect/f1/l1", method=method)
    if method == "POST":
        assert r.status_code == 204
        assert r.data == b""
        assert "Location" not in r.headers
    else:
        assert r.status_code == 302
        assert r.headers["Location"] == "http://example.com"
    assert called["args"] == ("f1", "l1", "http://example.com")


@pytest.mark.parametrize("tracking_url", ["/redirect/f1/l1", None])
def test_widget_link_keeps_destination_in_href(tracking_url):
    from bs4 import BeautifulSoup
    from flask import render_template

    article = types.SimpleNamespace(
        id="l1",
        name="Example",
        link="https://example.com/article",
        tracking_link=tracking_url,
        summary=None,
    )
    widget = types.SimpleNamespace(
        type="feed",
        link="https://example.com",
        name="Feed",
        display_header=True,
        display_items=[article],
    )
    with app_module.app.test_request_context():
        html = render_template("widget.html", widget=widget, skip_htmx=True)
    link = BeautifulSoup(html, "html.parser").select_one("a.feed-link")
    assert link["href"] == article.link
    assert link.get("data-tracking-url") == tracking_url
    assert "data-real-url" not in link.attrs


def test_refresh():
    fake = FakeLayout()
    app_module.layout = fake
    client = app_module.app.test_client()

    r = client.get("/feed/abc/refresh")
    assert r.status_code == 302
    assert fake._refreshed == ["abc"]


def test_healthcheck():
    client = app_module.app.test_client()
    r = client.get("/api/healthcheck")
    assert r.status_code == 200
    assert r.get_data(as_text=True) == "OK"
