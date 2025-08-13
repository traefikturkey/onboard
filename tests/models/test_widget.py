from unittest.mock import MagicMock, patch

import pytest

from app.models.exceptions import IDException
from app.models.widget import Widget


@pytest.fixture
def widget_data():
    return {
        "name": "TestWidget",
        "type": "bookmarks",
        "link": "http://example.com",
        "display_limit": 2,
        "display_header": False,
    }


def test_init_sets_id_and_template(widget_data):
    with patch(
        "app.models.widget.calculate_sha1_hash", return_value="hashed_id"
    ) as mock_hash:
        with patch("app.models.widget.pwd") as mock_pwd:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_path.name = "widget.html"
            mock_pwd.joinpath.return_value = mock_path
            widget = Widget(widget_data)
            assert widget.id == "hashed_id"
            assert widget.template == "widget.html"
            mock_hash.assert_called_once_with(widget_data["link"])


def test_init_raises_id_exception():
    with pytest.raises(IDException):
        Widget({"type": "bookmarks"})


def test_loaded_property(widget_data):
    widget = Widget(widget_data)
    widget._items = [1, 2]
    assert widget.loaded is True
    widget._items = []
    # Widget.loaded returns self.items and len(self.items) > 0, so for empty list, returns []
    assert not widget.loaded


def test_items_setter_and_last_updated(widget_data):
    widget = Widget(widget_data)
    items = ["a", "b"]
    widget.items = items
    assert widget._items == items
    assert widget.last_updated is not None


def test_iter(widget_data):
    widget = Widget(widget_data)
    widget._items = [1, 2, 3]
    assert list(iter(widget)) == [1, 2, 3]


def test_display_items_with_limit(widget_data):
    widget = Widget(widget_data)
    widget._items = [1, 2, 3, 4]
    widget.display_limit = 2
    assert list(widget.display_items) == [1, 2]


def test_display_items_without_limit(widget_data):
    widget = Widget(widget_data)
    widget._items = [1, 2, 3]
    widget.display_limit = None
    assert list(widget.display_items) == [1, 2, 3]


def test_name_type_link_display_header(widget_data):
    widget = Widget(widget_data)
    assert widget.name == "TestWidget"
    assert widget.type == "bookmarks"
    assert widget.link == "http://example.com"
    assert widget.display_header is False


def test_hasattr_and_get(widget_data):
    widget = Widget(widget_data)
    assert widget.hasattr("name") is True
    assert widget.hasattr("nonexistent") is False
    assert widget.get("name") == "TestWidget"
    assert widget.get("nonexistent", "default") == "default"


@patch("app.models.widget.Scheduler.getScheduler")
def test_scheduler_property(mock_get_scheduler, widget_data):
    mock_get_scheduler.return_value = "scheduler_instance"
    widget = Widget(widget_data)
    assert widget.scheduler == "scheduler_instance"


def test_from_dict_dispatch(widget_data):
    # Patch importlib.import_module to return mock classes for each type
    # Feed type
    widget_data["type"] = "feed"
    widget_data["feed_url"] = "http://example.com/feed"
    with patch(
        "app.models.feed.Feed", MagicMock(return_value="feed_instance")
    ) as mock_feed:
        result = Widget.from_dict(widget_data)
        assert result == "feed_instance"
        mock_feed.assert_called_once_with(widget_data)

    # Bookmarks type
    widget_data["type"] = "bookmarks"
    widget_data.pop("feed_url", None)
    widget_data["bookmarks"] = []
    with patch(
        "app.models.bookmarks.Bookmarks", MagicMock(return_value="bookmarks_instance")
    ) as mock_bookmarks:
        result = Widget.from_dict(widget_data)
        assert result == "bookmarks_instance"
        mock_bookmarks.assert_called_once_with(widget_data)

    # Iframe type
    widget_data["type"] = "iframe"
    widget_data.pop("bookmarks", None)
    widget_data["src"] = "https://example.com"
    with patch(
        "app.models.iframe.Iframe", MagicMock(return_value="iframe_instance")
    ) as mock_iframe:
        result = Widget.from_dict(widget_data)
        assert result == "iframe_instance"
        mock_iframe.assert_called_once_with(widget_data)

    # Other type falls back to Widget
    widget_data["type"] = "other"
    widget_data.pop("src", None)
    assert isinstance(Widget.from_dict(widget_data), Widget)
