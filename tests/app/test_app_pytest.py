import types

import app.app as app_module


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


def test_track_redirect(monkeypatch):
    called = {}

    def fake_track(feed_id, link_id, link):
        called["args"] = (feed_id, link_id, link)

    monkeypatch.setattr(
        app_module, "link_tracker", types.SimpleNamespace(track_click_event=fake_track)
    )
    app_module.layout = FakeLayout()
    client = app_module.app.test_client()

    r = client.get("/redirect/f1/l1")
    assert r.status_code == 302
    assert r.headers["Location"] == "http://example.com"
    assert called["args"] == ("f1", "l1", "http://example.com")


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
