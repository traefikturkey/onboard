import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from flask import template_rendered
from jinja2 import DictLoader

from app.factory import create_app
from app.models.layout import Layout
from app.services.bookmark_bar_manager import BookmarkBarManager


def make_app(tmp_path):
    config = tmp_path / "layout.yml"
    config.write_text("tabs:\n  - tab: Home\n    columns: []\n", encoding="utf-8")
    bookmarks = tmp_path / "bookmarks.json"
    bookmarks.write_text(
        json.dumps({"bar": [{"name": "Before", "href": "https://example.com"}]}),
        encoding="utf-8",
    )
    bar = BookmarkBarManager(
        str(bookmarks),
        favicon_store=SimpleNamespace(fetch_favicons_from=lambda urls: None),
    )
    layout = Layout(str(config), bar_manager=bar, skip_file_init=True)
    layout.reload()
    app = create_app(
        config={"CACHE_TYPE": "flask_caching.backends.simplecache.SimpleCache"},
        layout=layout,
        bookmark_manager=MagicMock(),
        link_tracker=MagicMock(),
        testing=True,
    )
    app.jinja_loader = DictLoader(
        {
            "index.html": "<!DOCTYPE html><main>{{ layout.bookmark_bar[0].name }}"
            "{% include 'layout_error.html' %}</main>",
            "tab_content.html": "<section>{{ tab_name }}:{{ layout.bookmark_bar[0].name }}"
            "{% include 'layout_error.html' %}</section>",
            "layout_error.html": "{{ layout.reload_error or '' }}",
        }
    )
    return app, layout, bookmarks


def test_cache_hits_and_separates_full_pages_from_fragments(tmp_path):
    app, _, _ = make_app(tmp_path)
    rendered = []

    def record(sender, template, **kwargs):
        rendered.append(template.name)

    with template_rendered.connected_to(record, app):
        client = app.test_client()
        full = client.get("/tab/Home")
        assert client.get("/tab/Home").data == full.data
        assert rendered == ["index.html"]
        headers = {"HX-Request": "true", "HX-Target": "main-content"}
        fragment = client.get("/tab/Home", headers=headers)
        assert b"<!DOCTYPE html>" not in fragment.data
        assert client.get("/tab/Home", headers=headers).data == fragment.data
        assert rendered == ["index.html", "tab_content.html"]
        assert client.get("/tab/Home").data == full.data
        assert client.get("/tab/Home", headers={"HX-Request": "true"}).data == full.data
        headers["HX-History-Restore-Request"] = "true"
        assert client.get("/tab/Home", headers=headers).data == full.data
        assert (
            client.get(
                "/", headers={"HX-Request": "true", "HX-Target": "main-content"}
            ).status_code
            == 200
        )


def test_bookmark_changes_invalidate_cached_tabs(tmp_path):
    app, _, bookmarks = make_app(tmp_path)
    client = app.test_client()
    assert b"Before" in client.get("/").data
    assert b"Before" in client.get("/tab/Home").data
    replacement = tmp_path / "replacement.json"
    replacement.write_text(
        json.dumps({"bar": [{"name": "After", "href": "https://example.com"}]}),
        encoding="utf-8",
    )
    replacement.replace(bookmarks)
    assert b"After" in client.get("/").data
    assert b"After" in client.get("/tab/Home").data


def test_invalid_layout_edit_shows_error_and_keeps_last_valid_page(tmp_path):
    app, layout, _ = make_app(tmp_path)
    client = app.test_client()
    assert client.get("/").status_code == 200
    original_tabs = layout.tabs
    layout.config_path.write_text("tabs: [", encoding="utf-8")
    response = client.get("/")
    assert response.status_code == 200
    assert b"Unable to load layout" in response.data
    assert layout.tabs is original_tabs
    layout.config_path.write_text(
        "tabs:\n  - tab: Fixed\n    columns: []\n", encoding="utf-8"
    )
    assert client.get("/").status_code == 200
    assert layout.tabs[0].name == "Fixed"
    assert layout.reload_error is None
    layout.config_path.unlink()
    assert client.get("/").status_code == 200
    assert layout.tabs[0].name == "Fixed"
    assert layout.reload_error
