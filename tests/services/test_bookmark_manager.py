"""Tests for BookmarkManager service."""

import json
import tempfile
from pathlib import Path

import pytest

from app.services.bookmark_manager import (
    BookmarkManager,
    BookmarkNotFoundError,
    InvalidIndexError,
    SectionNotFoundError,
)


@pytest.fixture
def temp_bookmark_file():
    """Create a temporary bookmark file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        initial_data = {
            "bar": [
                {
                    "name": "Gmail",
                    "href": "https://mail.google.com/",
                    "favicon": "/static/icons/gmail.ico",
                    "add_date": "1587496250",
                },
                {
                    "name": "YouTube",
                    "href": "https://youtube.com/",
                    "add_date": "1587496260",
                },
            ],
            "sections": {
                "shopping": {
                    "displayName": "Shopping",
                    "bookmarks": [
                        {"name": "Amazon", "link": "https://amazon.com/"},
                        {"name": "eBay", "link": "https://ebay.com/"},
                    ],
                },
                "tools": {
                    "displayName": "Tools",
                    "bookmarks": [{"name": "GitHub", "link": "https://github.com/"}],
                },
            },
        }
        json.dump(initial_data, f)
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def bookmark_manager(temp_bookmark_file, monkeypatch):
    """Create a BookmarkManager instance with a temporary file."""
    # Create manager with absolute path to temp file
    manager = BookmarkManager(temp_bookmark_file)
    return manager


class TestBarBookmarks:
    """Tests for bar bookmark operations."""

    def test_get_bar_bookmarks(self, bookmark_manager):
        """Test getting all bar bookmarks."""
        bookmarks = bookmark_manager.get_bar_bookmarks()
        assert len(bookmarks) == 2
        assert bookmarks[0]["name"] == "Gmail"
        assert bookmarks[1]["name"] == "YouTube"

    def test_get_bar_bookmark(self, bookmark_manager):
        """Test getting a specific bar bookmark."""
        bookmark = bookmark_manager.get_bar_bookmark(0)
        assert bookmark["name"] == "Gmail"
        assert bookmark["href"] == "https://mail.google.com/"

    def test_get_bar_bookmark_invalid_index(self, bookmark_manager):
        """Test getting bookmark with invalid index."""
        with pytest.raises(InvalidIndexError):
            bookmark_manager.get_bar_bookmark(10)

        with pytest.raises(InvalidIndexError):
            bookmark_manager.get_bar_bookmark(-1)

    def test_add_bar_bookmark(self, bookmark_manager):
        """Test adding a bookmark to the bar."""
        new_bookmark = {"name": "Reddit", "href": "https://reddit.com/"}
        result = bookmark_manager.add_bar_bookmark(new_bookmark)

        assert "add_date" in result
        assert result["name"] == "Reddit"

        bookmarks = bookmark_manager.get_bar_bookmarks()
        assert len(bookmarks) == 3
        assert bookmarks[2]["name"] == "Reddit"

    def test_add_bar_bookmark_preserves_add_date(self, bookmark_manager):
        """Test that provided add_date is preserved."""
        new_bookmark = {
            "name": "Twitter",
            "href": "https://twitter.com/",
            "add_date": "1234567890",
        }
        result = bookmark_manager.add_bar_bookmark(new_bookmark)

        assert result["add_date"] == "1234567890"

    def test_update_bar_bookmark(self, bookmark_manager):
        """Test updating a bar bookmark."""
        updated = {
            "name": "Gmail Updated",
            "href": "https://mail.google.com/mail/u/1/",
            "favicon": "/static/icons/gmail-new.ico",
        }
        result = bookmark_manager.update_bar_bookmark(0, updated)

        assert result["name"] == "Gmail Updated"
        assert result["href"] == "https://mail.google.com/mail/u/1/"
        assert result["add_date"] == "1587496250"  # Preserved

        bookmark = bookmark_manager.get_bar_bookmark(0)
        assert bookmark["name"] == "Gmail Updated"

    def test_update_bar_bookmark_invalid_index(self, bookmark_manager):
        """Test updating with invalid index."""
        with pytest.raises(InvalidIndexError):
            bookmark_manager.update_bar_bookmark(10, {"name": "Test"})

    def test_delete_bar_bookmark(self, bookmark_manager):
        """Test deleting a bar bookmark."""
        bookmark_manager.delete_bar_bookmark(0)

        bookmarks = bookmark_manager.get_bar_bookmarks()
        assert len(bookmarks) == 1
        assert bookmarks[0]["name"] == "YouTube"

    def test_delete_bar_bookmark_invalid_index(self, bookmark_manager):
        """Test deleting with invalid index."""
        with pytest.raises(InvalidIndexError):
            bookmark_manager.delete_bar_bookmark(10)

    def test_reorder_bar_bookmarks(self, bookmark_manager):
        """Test reordering bar bookmarks."""
        # Reverse the order
        result = bookmark_manager.reorder_bar_bookmarks([1, 0])

        assert result[0]["name"] == "YouTube"
        assert result[1]["name"] == "Gmail"

        bookmarks = bookmark_manager.get_bar_bookmarks()
        assert bookmarks[0]["name"] == "YouTube"

    def test_reorder_bar_bookmarks_invalid_length(self, bookmark_manager):
        """Test reordering with wrong number of indices."""
        with pytest.raises(ValueError, match="length"):
            bookmark_manager.reorder_bar_bookmarks([0])

    def test_reorder_bar_bookmarks_invalid_indices(self, bookmark_manager):
        """Test reordering with invalid indices."""
        with pytest.raises(ValueError, match="permutation"):
            bookmark_manager.reorder_bar_bookmarks([0, 0])


class TestSections:
    """Tests for section operations."""

    def test_get_all_sections(self, bookmark_manager):
        """Test getting all sections."""
        sections = bookmark_manager.get_all_sections()
        assert len(sections) == 2
        assert "shopping" in sections
        assert "tools" in sections
        assert sections["shopping"]["displayName"] == "Shopping"

    def test_get_section(self, bookmark_manager):
        """Test getting a specific section."""
        section = bookmark_manager.get_section("shopping")
        assert section["displayName"] == "Shopping"
        assert len(section["bookmarks"]) == 2

    def test_get_section_not_found(self, bookmark_manager):
        """Test getting non-existent section."""
        with pytest.raises(SectionNotFoundError):
            bookmark_manager.get_section("nonexistent")

    def test_create_section(self, bookmark_manager):
        """Test creating a new section."""
        result = bookmark_manager.create_section("ai", "AI Tools")

        assert result["displayName"] == "AI Tools"
        assert result["bookmarks"] == []

        section = bookmark_manager.get_section("ai")
        assert section["displayName"] == "AI Tools"

    def test_create_section_duplicate(self, bookmark_manager):
        """Test creating a section that already exists."""
        with pytest.raises(ValueError, match="already exists"):
            bookmark_manager.create_section("shopping", "Shopping 2")

    def test_update_section(self, bookmark_manager):
        """Test updating a section."""
        result = bookmark_manager.update_section(
            "shopping", {"displayName": "Online Shopping"}
        )

        assert result["displayName"] == "Online Shopping"
        assert len(result["bookmarks"]) == 2  # Bookmarks preserved

        section = bookmark_manager.get_section("shopping")
        assert section["displayName"] == "Online Shopping"

    def test_update_section_not_found(self, bookmark_manager):
        """Test updating non-existent section."""
        with pytest.raises(SectionNotFoundError):
            bookmark_manager.update_section("nonexistent", {"displayName": "Test"})

    def test_delete_section(self, bookmark_manager):
        """Test deleting a section."""
        bookmark_manager.delete_section("tools")

        sections = bookmark_manager.get_all_sections()
        assert len(sections) == 1
        assert "tools" not in sections

    def test_delete_section_not_found(self, bookmark_manager):
        """Test deleting non-existent section."""
        with pytest.raises(SectionNotFoundError):
            bookmark_manager.delete_section("nonexistent")


class TestSectionBookmarks:
    """Tests for section bookmark operations."""

    def test_get_section_bookmarks(self, bookmark_manager):
        """Test getting bookmarks from a section."""
        bookmarks = bookmark_manager.get_section_bookmarks("shopping")
        assert len(bookmarks) == 2
        assert bookmarks[0]["name"] == "Amazon"
        assert bookmarks[0]["link"] == "https://amazon.com/"

    def test_get_section_bookmarks_not_found(self, bookmark_manager):
        """Test getting bookmarks from non-existent section."""
        with pytest.raises(SectionNotFoundError):
            bookmark_manager.get_section_bookmarks("nonexistent")

    def test_add_section_bookmark(self, bookmark_manager):
        """Test adding a bookmark to a section."""
        new_bookmark = {"name": "Etsy", "link": "https://etsy.com/"}
        result = bookmark_manager.add_section_bookmark("shopping", new_bookmark)

        assert result["name"] == "Etsy"
        assert result["link"] == "https://etsy.com/"

        bookmarks = bookmark_manager.get_section_bookmarks("shopping")
        assert len(bookmarks) == 3
        assert bookmarks[2]["name"] == "Etsy"

    def test_add_section_bookmark_converts_href_to_link(self, bookmark_manager):
        """Test that href is converted to link for sections."""
        new_bookmark = {"name": "AliExpress", "href": "https://aliexpress.com/"}
        result = bookmark_manager.add_section_bookmark("shopping", new_bookmark)

        assert "link" in result
        assert result["link"] == "https://aliexpress.com/"
        assert "href" not in result

    def test_add_section_bookmark_not_found(self, bookmark_manager):
        """Test adding bookmark to non-existent section."""
        with pytest.raises(SectionNotFoundError):
            bookmark_manager.add_section_bookmark(
                "nonexistent", {"name": "Test", "link": "https://test.com"}
            )

    def test_update_section_bookmark(self, bookmark_manager):
        """Test updating a section bookmark."""
        updated = {"name": "Amazon Prime", "link": "https://amazon.com/prime"}
        result = bookmark_manager.update_section_bookmark("shopping", 0, updated)

        assert result["name"] == "Amazon Prime"
        assert result["link"] == "https://amazon.com/prime"

        bookmarks = bookmark_manager.get_section_bookmarks("shopping")
        assert bookmarks[0]["name"] == "Amazon Prime"

    def test_update_section_bookmark_invalid_index(self, bookmark_manager):
        """Test updating with invalid index."""
        with pytest.raises(InvalidIndexError):
            bookmark_manager.update_section_bookmark(
                "shopping", 10, {"name": "Test", "link": "https://test.com"}
            )

    def test_delete_section_bookmark(self, bookmark_manager):
        """Test deleting a section bookmark."""
        bookmark_manager.delete_section_bookmark("shopping", 0)

        bookmarks = bookmark_manager.get_section_bookmarks("shopping")
        assert len(bookmarks) == 1
        assert bookmarks[0]["name"] == "eBay"

    def test_delete_section_bookmark_invalid_index(self, bookmark_manager):
        """Test deleting with invalid index."""
        with pytest.raises(InvalidIndexError):
            bookmark_manager.delete_section_bookmark("shopping", 10)

    def test_reorder_section_bookmarks(self, bookmark_manager):
        """Test reordering section bookmarks."""
        result = bookmark_manager.reorder_section_bookmarks("shopping", [1, 0])

        assert result[0]["name"] == "eBay"
        assert result[1]["name"] == "Amazon"

        bookmarks = bookmark_manager.get_section_bookmarks("shopping")
        assert bookmarks[0]["name"] == "eBay"


class TestAdvancedOperations:
    """Tests for advanced bookmark operations."""

    def test_move_bookmark_bar_to_section(self, bookmark_manager):
        """Test moving a bookmark from bar to section."""
        source = {"type": "bar", "section_id": None, "index": 0}
        destination = {"type": "section", "section_id": "shopping", "index": 0}

        result = bookmark_manager.move_bookmark(source, destination)

        assert result["name"] == "Gmail"
        assert "link" in result  # Converted to link for section

        # Check bar reduced by 1
        bar = bookmark_manager.get_bar_bookmarks()
        assert len(bar) == 1
        assert bar[0]["name"] == "YouTube"

        # Check section increased by 1
        bookmarks = bookmark_manager.get_section_bookmarks("shopping")
        assert len(bookmarks) == 3
        assert bookmarks[0]["name"] == "Gmail"

    def test_move_bookmark_section_to_bar(self, bookmark_manager):
        """Test moving a bookmark from section to bar."""
        source = {"type": "section", "section_id": "shopping", "index": 0}
        destination = {"type": "bar", "section_id": None, "index": 1}

        result = bookmark_manager.move_bookmark(source, destination)

        assert result["name"] == "Amazon"
        assert "href" in result  # Converted to href for bar

        # Check section reduced by 1
        bookmarks = bookmark_manager.get_section_bookmarks("shopping")
        assert len(bookmarks) == 1
        assert bookmarks[0]["name"] == "eBay"

        # Check bar increased by 1
        bar = bookmark_manager.get_bar_bookmarks()
        assert len(bar) == 3
        assert bar[1]["name"] == "Amazon"

    def test_move_bookmark_section_to_section(self, bookmark_manager):
        """Test moving a bookmark between sections."""
        source = {"type": "section", "section_id": "shopping", "index": 0}
        destination = {"type": "section", "section_id": "tools", "index": 0}

        result = bookmark_manager.move_bookmark(source, destination)

        assert result["name"] == "Amazon"

        # Check source section
        shopping_bookmarks = bookmark_manager.get_section_bookmarks("shopping")
        assert len(shopping_bookmarks) == 1

        # Check destination section
        tools_bookmarks = bookmark_manager.get_section_bookmarks("tools")
        assert len(tools_bookmarks) == 2
        assert tools_bookmarks[0]["name"] == "Amazon"

    def test_export_bookmarks(self, bookmark_manager):
        """Test exporting all bookmarks."""
        data = bookmark_manager.export_bookmarks()

        assert "bar" in data
        assert "sections" in data
        assert len(data["bar"]) == 2
        assert len(data["sections"]) == 2
        assert data["bar"][0]["name"] == "Gmail"
        assert data["sections"]["shopping"]["displayName"] == "Shopping"

    def test_import_bookmarks_replace(self, bookmark_manager):
        """Test importing bookmarks in replace mode."""
        new_data = {
            "bar": [{"name": "New Bookmark", "href": "https://new.com/"}],
            "sections": {
                "new_section": {
                    "displayName": "New Section",
                    "bookmarks": [{"name": "Link", "link": "https://link.com/"}],
                }
            },
        }

        bookmark_manager.import_bookmarks(new_data, merge=False)

        bar = bookmark_manager.get_bar_bookmarks()
        assert len(bar) == 1
        assert bar[0]["name"] == "New Bookmark"

        sections = bookmark_manager.get_all_sections()
        assert len(sections) == 1
        assert "new_section" in sections

    def test_import_bookmarks_merge(self, bookmark_manager):
        """Test importing bookmarks in merge mode."""
        new_data = {
            "bar": [{"name": "New Bookmark", "href": "https://new.com/"}],
            "sections": {
                "shopping": {
                    "displayName": "Shopping",
                    "bookmarks": [{"name": "Walmart", "link": "https://walmart.com/"}],
                },
                "new_section": {"displayName": "New Section", "bookmarks": []},
            },
        }

        bookmark_manager.import_bookmarks(new_data, merge=True)

        bar = bookmark_manager.get_bar_bookmarks()
        assert len(bar) == 3  # 2 original + 1 new

        sections = bookmark_manager.get_all_sections()
        assert len(sections) == 3  # 2 original + 1 new

        shopping_bookmarks = bookmark_manager.get_section_bookmarks("shopping")
        assert len(shopping_bookmarks) == 3  # 2 original + 1 merged

    def test_import_bookmarks_invalid_structure(self, bookmark_manager):
        """Test importing invalid bookmark data."""
        with pytest.raises(ValueError, match="dictionary"):
            bookmark_manager.import_bookmarks([], merge=False)

        with pytest.raises(ValueError, match="bar"):
            bookmark_manager.import_bookmarks({"sections": {}}, merge=False)

        with pytest.raises(ValueError, match="list"):
            bookmark_manager.import_bookmarks({"bar": "invalid"}, merge=False)


class TestBookmarkManagerDependencyInjection:
    """Tests for BookmarkManager dependency injection."""

    def test_bookmark_manager_with_injected_file_store(self, temp_bookmark_file):
        """BookmarkManager uses provided file_store instead of creating its own."""
        from unittest.mock import MagicMock, patch

        # Create mock file store
        mock_file_store = MagicMock()
        mock_file_store.read_json.return_value = {"bar": [], "sections": {}}

        # Mock BookmarkBarManager to avoid file I/O
        mock_bar_manager = MagicMock()

        manager = BookmarkManager(
            temp_bookmark_file,
            file_store=mock_file_store,
            bar_manager=mock_bar_manager,
        )

        # Verify our mock was used
        assert manager.file_store is mock_file_store
        mock_file_store.read_json.assert_called()

    def test_bookmark_manager_with_injected_bar_manager(self, temp_bookmark_file):
        """BookmarkManager uses provided bar_manager instead of creating its own."""
        from unittest.mock import MagicMock

        mock_bar_manager = MagicMock()

        manager = BookmarkManager(
            temp_bookmark_file, bar_manager=mock_bar_manager
        )

        assert manager.bar_manager is mock_bar_manager

    def test_bookmark_manager_save_triggers_bar_manager_reload(self, temp_bookmark_file):
        """When bookmarks are saved, bar_manager.reload() is called."""
        from unittest.mock import MagicMock

        mock_bar_manager = MagicMock()

        manager = BookmarkManager(
            temp_bookmark_file, bar_manager=mock_bar_manager
        )

        # Add a bookmark (triggers save)
        manager.add_bar_bookmark({"name": "Test", "href": "http://test.com"})

        # Verify reload was called
        mock_bar_manager.reload.assert_called()
