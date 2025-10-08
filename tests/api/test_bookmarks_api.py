"""Tests for bookmark management API endpoints."""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.main import app
from app.services.bookmark_manager import (
    BookmarkNotFoundError,
    InvalidIndexError,
    SectionNotFoundError,
)


@pytest.fixture
def client():
    """Create test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_bookmark_manager():
    """Mock BookmarkManager for isolated testing."""
    with patch("app.api.bookmarks.bookmark_manager") as mock:
        yield mock


class TestBarBookmarkRoutes:
    """Test bar bookmark API endpoints."""

    def test_get_bar_bookmarks_success(self, client, mock_bookmark_manager):
        """Test getting bar bookmarks."""
        mock_bookmark_manager.get_bar_bookmarks.return_value = [
            {"name": "Google", "href": "https://google.com"},
            {"name": "GitHub", "href": "https://github.com"},
        ]

        response = client.get("/api/bookmarks/bar")
        data = json.loads(response.data)

        assert response.status_code == 200
        assert data["success"] is True
        assert len(data["data"]) == 2
        assert data["data"][0]["name"] == "Google"

    def test_add_bar_bookmark_success(self, client, mock_bookmark_manager):
        """Test adding a bar bookmark."""
        new_bookmark = {
            "name": "Test",
            "href": "https://test.com",
            "favicon": "https://test.com/favicon.ico",
        }
        mock_bookmark_manager.add_bar_bookmark.return_value = new_bookmark

        response = client.post(
            "/api/bookmarks/bar",
            data=json.dumps(new_bookmark),
            content_type="application/json",
        )
        data = json.loads(response.data)

        assert response.status_code == 201
        assert data["success"] is True
        assert data["data"]["name"] == "Test"

    def test_add_bar_bookmark_folder(self, client, mock_bookmark_manager):
        """Test adding a folder to bar."""
        folder = {
            "name": "Folder",
            "contents": [],
            "multiColumn": 1,  # Must be >= 1 per Pydantic validation
            "openInNewTab": False,
        }
        mock_bookmark_manager.add_bar_bookmark.return_value = folder

        response = client.post(
            "/api/bookmarks/bar",
            data=json.dumps(folder),
            content_type="application/json",
        )
        data = json.loads(response.data)

        assert response.status_code == 201
        assert data["success"] is True
        assert "contents" in data["data"]

    def test_add_bar_bookmark_missing_name(self, client):
        """Test adding bookmark without required name."""
        response = client.post(
            "/api/bookmarks/bar",
            data=json.dumps({"href": "https://test.com"}),
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_update_bar_bookmark_success(self, client, mock_bookmark_manager):
        """Test updating a bar bookmark."""
        updated = {"name": "Updated", "href": "https://updated.com"}
        mock_bookmark_manager.update_bar_bookmark.return_value = updated

        response = client.put(
            "/api/bookmarks/bar/0",
            data=json.dumps(updated),
            content_type="application/json",
        )
        data = json.loads(response.data)

        assert response.status_code == 200
        assert data["success"] is True
        assert data["data"]["name"] == "Updated"

    def test_update_bar_bookmark_invalid_index(self, client, mock_bookmark_manager):
        """Test updating with invalid index."""
        mock_bookmark_manager.update_bar_bookmark.side_effect = InvalidIndexError(
            "Invalid index"
        )

        response = client.put(
            "/api/bookmarks/bar/999",
            data=json.dumps({"name": "Test"}),
            content_type="application/json",
        )

        assert response.status_code == 404

    def test_delete_bar_bookmark_success(self, client, mock_bookmark_manager):
        """Test deleting a bar bookmark."""
        mock_bookmark_manager.delete_bar_bookmark.return_value = None

        response = client.delete("/api/bookmarks/bar/0")
        data = json.loads(response.data)

        assert response.status_code == 200
        assert data["success"] is True

    def test_delete_bar_bookmark_not_found(self, client, mock_bookmark_manager):
        """Test deleting non-existent bookmark."""
        mock_bookmark_manager.delete_bar_bookmark.side_effect = BookmarkNotFoundError(
            "Not found"
        )

        response = client.delete("/api/bookmarks/bar/999")

        assert response.status_code == 500


class TestSectionRoutes:
    """Test section API endpoints."""

    def test_get_all_sections_success(self, client, mock_bookmark_manager):
        """Test getting all sections."""
        mock_bookmark_manager.get_all_sections.return_value = {
            "work": {"displayName": "Work", "bookmarks": []},
            "personal": {"displayName": "Personal", "bookmarks": []},
        }

        response = client.get("/api/bookmarks/sections")
        data = json.loads(response.data)

        assert response.status_code == 200
        assert data["success"] is True
        assert "work" in data["data"]
        assert "personal" in data["data"]

    def test_create_section_success(self, client, mock_bookmark_manager):
        """Test creating a new section."""
        section_data = {"displayName": "New Section", "bookmarks": []}
        mock_bookmark_manager.create_section.return_value = section_data

        response = client.post(
            "/api/bookmarks/sections",
            data=json.dumps(
                {"section_id": "new_section", "displayName": "New Section"}
            ),
            content_type="application/json",
        )
        data = json.loads(response.data)

        assert response.status_code == 201
        assert data["success"] is True
        assert data["data"]["displayName"] == "New Section"

    def test_create_section_duplicate(self, client, mock_bookmark_manager):
        """Test creating duplicate section."""
        mock_bookmark_manager.create_section.side_effect = ValueError(
            "Section already exists"
        )

        response = client.post(
            "/api/bookmarks/sections",
            data=json.dumps({"id": "work", "displayName": "Work"}),
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_delete_section_success(self, client, mock_bookmark_manager):
        """Test deleting a section."""
        mock_bookmark_manager.delete_section.return_value = None

        response = client.delete("/api/bookmarks/sections/work")
        data = json.loads(response.data)

        assert response.status_code == 200
        assert data["success"] is True

    def test_delete_section_not_found(self, client, mock_bookmark_manager):
        """Test deleting non-existent section."""
        mock_bookmark_manager.delete_section.side_effect = SectionNotFoundError(
            "Not found"
        )

        response = client.delete("/api/bookmarks/sections/nonexistent")

        assert response.status_code == 404


class TestSectionBookmarkRoutes:
    """Test section bookmark API endpoints."""

    def test_get_section_bookmarks_success(self, client, mock_bookmark_manager):
        """Test getting bookmarks from a section."""
        mock_bookmark_manager.get_section_bookmarks.return_value = [
            {"name": "Link1", "link": "https://link1.com"},
            {"name": "Link2", "link": "https://link2.com"},
        ]

        response = client.get("/api/bookmarks/sections/work/bookmarks")
        data = json.loads(response.data)

        assert response.status_code == 200
        assert data["success"] is True
        assert len(data["data"]) == 2

    def test_add_section_bookmark_success(self, client, mock_bookmark_manager):
        """Test adding bookmark to section."""
        new_bookmark = {"name": "Test", "link": "https://test.com"}
        mock_bookmark_manager.add_section_bookmark.return_value = new_bookmark

        response = client.post(
            "/api/bookmarks/sections/work/bookmarks",
            data=json.dumps(new_bookmark),
            content_type="application/json",
        )
        data = json.loads(response.data)

        assert response.status_code == 201
        assert data["success"] is True
        assert data["data"]["name"] == "Test"

    def test_update_section_bookmark_success(self, client, mock_bookmark_manager):
        """Test updating section bookmark."""
        updated = {"name": "Updated", "link": "https://updated.com"}
        mock_bookmark_manager.update_section_bookmark.return_value = updated

        response = client.put(
            "/api/bookmarks/sections/work/bookmarks/0",
            data=json.dumps(updated),
            content_type="application/json",
        )
        data = json.loads(response.data)

        assert response.status_code == 200
        assert data["success"] is True

    def test_delete_section_bookmark_success(self, client, mock_bookmark_manager):
        """Test deleting section bookmark."""
        mock_bookmark_manager.delete_section_bookmark.return_value = None

        response = client.delete("/api/bookmarks/sections/work/bookmarks/0")
        data = json.loads(response.data)

        assert response.status_code == 200
        assert data["success"] is True


class TestAdvancedOperations:
    """Test advanced bookmark operations."""

    def test_reorder_bar_bookmarks_success(self, client, mock_bookmark_manager):
        """Test reordering bar bookmarks."""
        mock_bookmark_manager.reorder_bar_bookmarks.return_value = None

        response = client.post(
            "/api/bookmarks/bar/reorder",
            data=json.dumps({"indices": [2, 0, 1]}),
            content_type="application/json",
        )
        data = json.loads(response.data)

        assert response.status_code == 200
        assert data["success"] is True

    def test_move_bookmark_to_section_success(self, client, mock_bookmark_manager):
        """Test moving bookmark from bar to section."""
        mock_bookmark_manager.move_bookmark.return_value = None

        response = client.post(
            "/api/bookmarks/move",
            data=json.dumps(
                {
                    "source": {"type": "bar", "index": 0},
                    "destination": {
                        "type": "section",
                        "section_id": "work",
                        "index": 0,
                    },
                }
            ),
            content_type="application/json",
        )
        data = json.loads(response.data)

        assert response.status_code == 200
        assert data["success"] is True

    def test_import_bookmarks_success(self, client, mock_bookmark_manager):
        """Test importing bookmarks."""
        import_data = {
            "data": {
                "bar": [{"name": "Test", "href": "https://test.com"}],
                "sections": {"work": {"displayName": "Work", "bookmarks": []}},
            },
            "merge": False,
        }
        mock_bookmark_manager.import_bookmarks.return_value = None

        response = client.post(
            "/api/bookmarks/import",
            data=json.dumps(import_data),
            content_type="application/json",
        )
        data = json.loads(response.data)

        assert response.status_code == 200
        assert data["success"] is True

    def test_export_bookmarks_success(self, client, mock_bookmark_manager):
        """Test exporting bookmarks."""
        export_data = {
            "bar": [{"name": "Test", "href": "https://test.com"}],
            "sections": {},
        }
        mock_bookmark_manager.export_bookmarks.return_value = export_data

        response = client.get("/api/bookmarks/export")
        data = json.loads(response.data)

        assert response.status_code == 200
        assert data["success"] is True
        assert "bar" in data["data"]
        assert "sections" in data["data"]


class TestErrorHandling:
    """Test error handling across API."""

    def test_missing_request_body(self, client):
        """Test endpoints with missing request body."""
        response = client.post("/api/bookmarks/bar")

        assert response.status_code == 500  # Flask throws 415 which becomes 500

    def test_invalid_json(self, client):
        """Test endpoints with invalid JSON."""
        response = client.post(
            "/api/bookmarks/bar",
            data="invalid json",
            content_type="application/json",
        )

        assert response.status_code == 500  # Flask JSON decode error

    def test_validation_error(self, client):
        """Test Pydantic validation error."""
        response = client.post(
            "/api/bookmarks/bar",
            data=json.dumps({"name": 123}),  # name should be string
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_internal_server_error(self, client, mock_bookmark_manager):
        """Test handling of unexpected errors."""
        mock_bookmark_manager.get_bar_bookmarks.side_effect = Exception(
            "Unexpected error"
        )

        response = client.get("/api/bookmarks/bar")

        assert response.status_code == 500


class TestUIRoute:
    """Test bookmark manager UI route."""

    def test_bookmarks_manager_page_loads(self, client):
        """Test that the bookmark manager page loads."""
        response = client.get("/bookmarks/manage")

        assert response.status_code == 200
        assert b"Bookmark Manager" in response.data
        assert b"bookmarkManager()" in response.data
