import types
from datetime import datetime

import app.app as app_module


class FakeLayoutModified:
    def __init__(self):
        self.favicon_path = "/static/img/favicon.ico"
        self._reloaded = False

    def is_modified(self):
        # simulate modified state
        return True

    def reload(self):
        self._reloaded = True

    def get_link(self, feed_id, link_id):
        return None

    def tab(self, tab_name=None):
        # minimal object with rows for the index template iteration
        return types.SimpleNamespace(rows=[])


def test_inject_current_date_uses_env_and_layout(monkeypatch):
    # ensure env var is used for site title and layout favicon is returned
    monkeypatch.setenv("ONBOARD_SITE_TITLE", "MySite")
    app_module.layout = types.SimpleNamespace(favicon_path="/fav.ico")

    ctx = app_module.inject_current_date()
    assert "today_date" in ctx
    assert isinstance(ctx["today_date"], datetime)
    assert ctx["site_title"] == "MySite"
    assert ctx["favicon_path"] == "/fav.ico"


def test_index_calls_reload_when_layout_modified():
    fake = FakeLayoutModified()
    app_module.layout = fake
    client = app_module.app.test_client()

    r = client.get("/")
    assert r.status_code == 200
    # layout.reload should have been called because is_modified returned True
    assert fake._reloaded is True


def test_track_redirect_with_missing_link(monkeypatch):
    called = {}

    def fake_track(feed_id, link_id, link):
        called["args"] = (feed_id, link_id, link)

    monkeypatch.setattr(
        app_module, "link_tracker", types.SimpleNamespace(track_click_event=fake_track)
    )
    # layout returns None for get_link
    app_module.layout = FakeLayoutModified()
    client = app_module.app.test_client()

    r = client.get("/redirect/f1/l1")
    assert r.status_code == 302
    # when link is missing the app redirects to index
    assert r.headers["Location"] == "/"
    assert called["args"] == ("f1", "l1", None)


def test_track_redirect_with_empty_string_link(monkeypatch):
    called = {}

    def fake_track(feed_id, link_id, link):
        called["args"] = (feed_id, link_id, link)

    monkeypatch.setattr(
        app_module, "link_tracker", types.SimpleNamespace(track_click_event=fake_track)
    )

    class FakeLayoutEmpty:
        def get_link(self, feed_id, link_id):
            return ""

    app_module.layout = FakeLayoutEmpty()
    client = app_module.app.test_client()

    r = client.get("/redirect/f2/l2")
    assert r.status_code == 302
    assert r.headers["Location"] == "/"
    assert called["args"] == ("f2", "l2", "")
