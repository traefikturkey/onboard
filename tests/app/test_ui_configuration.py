import json
from unittest.mock import MagicMock

import pytest
import yaml
from bs4 import BeautifulSoup
from pydantic import ValidationError

from app.factory import create_app
from app.models.bookmark import Bookmark
from app.models.column import Column
from app.models.layout import Layout
from app.models.presentation import UISettings
from app.services.bookmark_bar_manager import BookmarkBarManager


def make_layout(tmp_path, config, bookmarks=None):
    bookmark_file = tmp_path / "bookmarks.json"
    bookmark_file.write_text(
        json.dumps(bookmarks or {"bar": [], "sections": {}}), encoding="utf-8"
    )
    config_file = tmp_path / "layout.yml"
    config_file.write_text(yaml.safe_dump(config), encoding="utf-8")
    manager = BookmarkBarManager(str(bookmark_file), favicon_store=MagicMock())
    manager.favicon_store.icon_path.return_value = None
    layout = Layout(str(config_file), bar_manager=manager, skip_file_init=True)
    layout.reload()
    return layout


def make_app(layout):
    return create_app(
        layout=layout,
        bookmark_manager=MagicMock(),
        link_tracker=MagicMock(),
        config={"CACHE_TYPE": "SimpleCache"},
        testing=True,
    )


@pytest.mark.parametrize(
    "settings",
    [
        {"unknown_setting": "4px"},
        {"header_icon_gap": "4px; color:red"},
        {"header_icon_size": "</style><script>alert(1)</script>"},
        {"header_background": "url(https://example.com/)"},
        {"feed_height": "-10px"},
    ],
)
def test_invalid_ui_settings_retain_active_layout(tmp_path, settings):
    layout = make_layout(
        tmp_path,
        {
            "ui": {"header_icon_gap": "6px"},
            "tabs": [{"tab": "Home", "columns": []}],
        },
    )
    layout.config_path.write_text(
        yaml.safe_dump({"ui": settings, "tabs": [{"tab": "Changed", "columns": []}]}),
        encoding="utf-8",
    )
    assert layout.reload() is False
    assert layout.tabs[0].name == "Home"
    assert layout.ui.css_variables == {"--header-icon-gap": "6px"}
    assert layout.reload_error


@pytest.mark.parametrize("value", [0, -1, float("inf"), "2; color:red", True])
def test_invalid_column_proportions_are_rejected(value):
    with pytest.raises(ValidationError):
        Column.from_dict({"flex": value, "widgets": []})


def test_presentation_defaults_preserve_existing_behavior():
    bookmark = Bookmark.from_dict(
        {"name": "Gmail", "link": "https://mail.google.com/"}, MagicMock(id="layout")
    )
    assert bookmark.header_favicon == "/static/img/gmail.ico"
    assert bookmark.hover_delay_ms == 2000
    assert bookmark.multi_column == 2
    assert bookmark.open_in_new_tab is True
    assert Column.from_dict({"widgets": []}).flex == 1
    assert UISettings().css_variables == {}


def test_header_section_and_presentation_reload_without_rebuild(tmp_path):
    original_url = "https://example.com/search?q=3d%20printer&filter=1"
    config = {
        "ui": {"header_icon_size": "20px", "header_icon_gap": "6px"},
        "headers": [
            {
                "name": "Renamed utility",
                "link": "https://example.com/",
                "favicon": "gmail.ico",
                "bookmarks_section": "searches",
                "hover_delay_ms": 350,
                "multiColumn": 3,
                "openInNewTab": False,
                "contents": [{"name": "Old inline", "href": "https://old.example/"}],
            }
        ],
        "tabs": [{"tab": "Home", "columns": []}],
    }
    bookmarks = {
        "bar": [
            {
                "name": "Explicit icon",
                "href": "https://example.com/",
                "favicon": "docs.ico",
            }
        ],
        "sections": {
            "searches": {
                "displayName": "Searches",
                "bookmarks": [{"name": "Original search", "link": original_url}],
            }
        },
    }
    layout = make_layout(tmp_path, config, bookmarks)
    with make_app(layout).test_client() as client:
        soup = BeautifulSoup(client.get("/").data, "html.parser")
        menu = soup.select_one("[data-utility-menu]")
        assert menu["data-hover-delay"] == "350"
        assert menu.select_one(":scope > a img")["src"] == "/static/img/gmail.ico"
        assert not menu.select_one(":scope > a").has_attr("target")
        assert menu.select_one("ul")["style"] == "--menu-columns: 3; --menu-rows: 1"
        assert menu.select_one("ul a")["href"] == original_url
        assert "Old inline" not in menu.get_text()
        assert "--header-icon-size: 20px" in soup.select_one("#ui-settings").get_text()
        assert soup.select_one("#bookmarkBar img")["src"] == "/static/img/docs.ico"

        bookmarks["sections"]["searches"]["bookmarks"].append(
            {"name": "Added search", "link": "https://example.com/second"}
        )
        layout.bar_manager.bookmark_bar_path.write_text(
            json.dumps(bookmarks), encoding="utf-8"
        )
        updated = BeautifulSoup(client.get("/").data, "html.parser")
        assert len(updated.select(".utility-menu-links a")) == 2

        config["ui"]["header_icon_gap"] = "9px"
        config["headers"][0]["hover_delay_ms"] = 750
        layout.config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
        updated = BeautifulSoup(client.get("/").data, "html.parser")
        assert "--header-icon-gap: 9px" in updated.select_one("#ui-settings").get_text()
        assert updated.select_one("[data-utility-menu]")["data-hover-delay"] == "750"


def test_bookmark_columns_and_favicons_are_layout_options(tmp_path):
    config = {
        "tabs": [
            {
                "tab": "Home",
                "columns": [
                    {
                        "flex": 2.5,
                        "widgets": [
                            {
                                "name": "Bookmarks",
                                "type": "bookmarks",
                                "bookmarks_section": "links",
                                "columns": 2,
                                "show_favicons": True,
                            }
                        ],
                    }
                ],
            }
        ],
    }
    bookmarks = {
        "bar": [],
        "sections": {
            "links": {
                "displayName": "Links",
                "bookmarks": [
                    {
                        "name": "Example",
                        "link": "https://example.com/",
                        "favicon": "/static/assets/icons/example.ico",
                    }
                ],
            }
        },
    }
    layout = make_layout(tmp_path, config, bookmarks)
    with make_app(layout).test_client() as client:
        soup = BeautifulSoup(client.get("/").data, "html.parser")
    assert soup.select_one("#main-content .column")["style"] == "flex: 2.5"
    assert soup.select_one(".bookmarks-content")["style"] == "--bookmark-columns: 2"
    assert (
        soup.select_one(".bookmarks-link img")["src"]
        == "/static/assets/icons/example.ico"
    )
