from unittest.mock import MagicMock

import pytest

from app.models.bookmarks import Bookmarks


@pytest.fixture
def base_widget_data():
    """Base widget data that includes required bookmarks_section key."""
    return {
        "name": "TestBookmarks",
        "type": "bookmarks",
        "link": "http://example.com",
        "bookmarks_section": "test_section",
    }


@pytest.fixture
def mock_bookmark_manager():
    """Create a mock bookmark manager."""
    manager = MagicMock()
    manager.get_section.return_value = {
        "displayName": "Test Section",
        "bookmarks": [
            {"name": "Bookmark 1", "link": "http://example.com/1"},
            {"name": "Bookmark 2", "link": "http://example.com/2"},
        ],
    }
    return manager


class TestBookmarksInit:
    def test_init_without_bookmark_manager_raises(self, base_widget_data):
        """ValueError is raised when bookmark_manager is None."""
        with pytest.raises(ValueError) as exc_info:
            Bookmarks(base_widget_data, bookmark_manager=None)
        assert "bookmark_manager is required" in str(exc_info.value)

    def test_init_without_bookmarks_section_raises(self, mock_bookmark_manager):
        """ValueError is raised when widget lacks bookmarks_section key."""
        widget_data = {
            "name": "TestBookmarks",
            "type": "bookmarks",
            "link": "http://example.com",
        }
        with pytest.raises(ValueError) as exc_info:
            Bookmarks(widget_data, bookmark_manager=mock_bookmark_manager)
        assert "bookmarks_section" in str(exc_info.value)

    def test_section_not_found_returns_empty_items(self, base_widget_data):
        """When section is not found, items should be empty list."""
        manager = MagicMock()
        manager.get_section.return_value = None

        bookmarks = Bookmarks(base_widget_data, bookmark_manager=manager)
        assert list(bookmarks.items) == []

    def test_section_loads_bookmarks(self, base_widget_data, mock_bookmark_manager):
        """Bookmarks are loaded from the section."""
        bookmarks = Bookmarks(base_widget_data, bookmark_manager=mock_bookmark_manager)
        assert len(list(bookmarks.items)) == 2

    def test_merges_section_metadata_when_not_set(self, base_widget_data):
        """Section metadata like openInNewTab is merged into widget when not set."""
        manager = MagicMock()
        manager.get_section.return_value = {
            "displayName": "Test Section",
            "bookmarks": [],
            "openInNewTab": True,
        }

        bookmarks = Bookmarks(base_widget_data, bookmark_manager=manager)
        # Access the internal widget data through the widget's get method
        assert bookmarks.get("openInNewTab") is True

    def test_does_not_override_existing_metadata(self, base_widget_data):
        """Section metadata does not override existing widget settings."""
        manager = MagicMock()
        manager.get_section.return_value = {
            "displayName": "Test Section",
            "bookmarks": [],
            "openInNewTab": True,
        }
        base_widget_data["openInNewTab"] = False

        bookmarks = Bookmarks(base_widget_data, bookmark_manager=manager)
        # Existing setting should be preserved
        assert bookmarks.get("openInNewTab") is False
