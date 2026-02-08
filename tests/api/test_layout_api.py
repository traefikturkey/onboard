"""Tests for layout API endpoints."""

import json
from unittest.mock import MagicMock

import pytest

from app.api.layout import create_layout_blueprint
from app.factory import create_app


@pytest.fixture
def mock_widget_order_manager():
    """Create a mock WidgetOrderManager."""
    manager = MagicMock()
    manager.update_columns.return_value = None
    return manager


@pytest.fixture
def mock_layout_config_manager():
    """Create a mock LayoutConfigManager."""
    manager = MagicMock()
    manager.get_tab_names.return_value = ["Home", "Tech"]
    manager.add_tab.return_value = {"tab": "New Tab", "columns": []}
    manager.delete_tab.return_value = None
    manager.add_widget.return_value = "abc123"
    manager.move_widget.return_value = None
    return manager


@pytest.fixture
def app(mock_widget_order_manager, mock_layout_config_manager):
    """Create test Flask app with mock widget order manager."""
    app = create_app(
        layout=MagicMock(),
        bookmark_manager=MagicMock(),
        link_tracker=MagicMock(),
        widget_order_manager=mock_widget_order_manager,
        layout_config_manager=mock_layout_config_manager,
        testing=True,
    )
    return app


@pytest.fixture
def client(app):
    return app.test_client()


class TestReorderEndpoint:
    def test_valid_reorder_returns_success(self, client, mock_widget_order_manager):
        """Valid reorder request returns success."""
        response = client.post(
            "/api/layout/reorder",
            data=json.dumps(
                {
                    "tab": "Home",
                    "columns": [
                        {"col_key": "0.0", "widget_ids": ["a", "b"]},
                        {"col_key": "0.1", "widget_ids": ["c"]},
                    ],
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "updated" in data["message"].lower()
        mock_widget_order_manager.update_columns.assert_called_once_with(
            "Home",
            [
                {"col_key": "0.0", "widget_ids": ["a", "b"]},
                {"col_key": "0.1", "widget_ids": ["c"]},
            ],
        )

    def test_missing_body_returns_400(self, client):
        """Missing request body returns 400."""
        response = client.post(
            "/api/layout/reorder",
            data=json.dumps(None),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_empty_tab_returns_400(self, client):
        """Empty tab name returns 400."""
        response = client.post(
            "/api/layout/reorder",
            data=json.dumps(
                {
                    "tab": "",
                    "columns": [{"col_key": "0.0", "widget_ids": ["a"]}],
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_missing_tab_returns_400(self, client):
        """Missing tab field returns 400."""
        response = client.post(
            "/api/layout/reorder",
            data=json.dumps(
                {
                    "columns": [{"col_key": "0.0", "widget_ids": ["a"]}],
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_empty_columns_returns_400(self, client):
        """Empty columns list returns 400."""
        response = client.post(
            "/api/layout/reorder",
            data=json.dumps(
                {
                    "tab": "Home",
                    "columns": [],
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_missing_columns_returns_400(self, client):
        """Missing columns field returns 400."""
        response = client.post(
            "/api/layout/reorder",
            data=json.dumps({"tab": "Home"}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_empty_col_key_returns_400(self, client):
        """Empty col_key returns 400."""
        response = client.post(
            "/api/layout/reorder",
            data=json.dumps(
                {
                    "tab": "Home",
                    "columns": [{"col_key": "", "widget_ids": ["a"]}],
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_manager_exception_returns_500(self, client, mock_widget_order_manager):
        """Exception from manager returns 500."""
        mock_widget_order_manager.update_columns.side_effect = RuntimeError("disk full")
        response = client.post(
            "/api/layout/reorder",
            data=json.dumps(
                {
                    "tab": "Home",
                    "columns": [{"col_key": "0.0", "widget_ids": ["a"]}],
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 500
        data = response.get_json()
        assert data["success"] is False


class TestBlueprintInjection:
    def test_injected_manager_is_used(self):
        """Blueprint uses injected manager instead of app extensions."""
        mock_mgr = MagicMock()
        mock_mgr.update_columns.return_value = None

        # Inject the mock manager directly via the app extensions
        app = create_app(
            layout=MagicMock(),
            bookmark_manager=MagicMock(),
            link_tracker=MagicMock(),
            widget_order_manager=mock_mgr,
            testing=True,
        )

        client = app.test_client()
        response = client.post(
            "/api/layout/reorder",
            data=json.dumps(
                {
                    "tab": "Test",
                    "columns": [{"col_key": "0.0", "widget_ids": ["x"]}],
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 200
        mock_mgr.update_columns.assert_called_once()


class TestGetTabsEndpoint:
    def test_returns_tab_names(self, client, mock_layout_config_manager):
        """GET /api/layout/tabs returns tab names."""
        response = client.get("/api/layout/tabs")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"] == ["Home", "Tech"]
        mock_layout_config_manager.get_tab_names.assert_called_once()


class TestAddTabEndpoint:
    def test_valid_returns_201(self, client, mock_layout_config_manager):
        """Valid tab creation returns 201."""
        response = client.post(
            "/api/layout/tabs",
            data=json.dumps({"name": "New Tab"}),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["success"] is True
        assert data["message"] == "Tab 'New Tab' created"
        mock_layout_config_manager.add_tab.assert_called_once_with("New Tab")

    def test_empty_name_returns_400(self, client):
        """Empty tab name returns 400."""
        response = client.post(
            "/api/layout/tabs",
            data=json.dumps({"name": ""}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_duplicate_returns_409(self, client, mock_layout_config_manager):
        """Duplicate tab name returns 409."""
        mock_layout_config_manager.add_tab.side_effect = ValueError("Tab already exists")
        response = client.post(
            "/api/layout/tabs",
            data=json.dumps({"name": "Home"}),
            content_type="application/json",
        )
        assert response.status_code == 409


class TestDeleteTabEndpoint:
    def test_valid_returns_200(self, client, mock_layout_config_manager):
        """Valid tab deletion returns 200."""
        response = client.delete("/api/layout/tabs/Home")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        mock_layout_config_manager.delete_tab.assert_called_once_with("Home")

    def test_not_found_returns_404(self, client, mock_layout_config_manager):
        """Tab not found returns 404."""
        mock_layout_config_manager.delete_tab.side_effect = ValueError("Tab not found")
        response = client.delete("/api/layout/tabs/NonExistent")
        assert response.status_code == 404

    def test_last_tab_returns_400(self, client, mock_layout_config_manager):
        """Cannot delete the last tab returns 400."""
        mock_layout_config_manager.delete_tab.side_effect = ValueError(
            "Cannot delete the last tab"
        )
        response = client.delete("/api/layout/tabs/Home")
        assert response.status_code == 400


class TestAddWidgetEndpoint:
    def test_valid_returns_201(self, client, mock_layout_config_manager):
        """Valid widget creation returns 201."""
        response = client.post(
            "/api/layout/widgets",
            data=json.dumps(
                {
                    "tab": "Home",
                    "name": "My Widget",
                    "feed_url": "https://example.com/feed",
                    "link": "https://example.com",
                    "col_index": 0,
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["widget_id"] == "abc123"
        mock_layout_config_manager.add_widget.assert_called_once_with(
            "Home",
            {
                "name": "My Widget",
                "type": "feed",
                "feed_url": "https://example.com/feed",
                "link": "https://example.com",
            },
            0,
        )

    def test_missing_feed_url_returns_400(self, client):
        """Missing feed_url returns 400."""
        response = client.post(
            "/api/layout/widgets",
            data=json.dumps(
                {
                    "tab": "Home",
                    "name": "My Widget",
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_invalid_url_returns_400(self, client):
        """Invalid URL returns 400."""
        response = client.post(
            "/api/layout/widgets",
            data=json.dumps(
                {
                    "tab": "Home",
                    "name": "My Widget",
                    "feed_url": "not-a-url",
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_nonexistent_tab_returns_404(self, client, mock_layout_config_manager):
        """Nonexistent tab returns 404."""
        mock_layout_config_manager.add_widget.side_effect = ValueError("Tab not found")
        response = client.post(
            "/api/layout/widgets",
            data=json.dumps(
                {
                    "tab": "NonExistent",
                    "name": "My Widget",
                    "feed_url": "https://example.com/feed",
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 404


class TestMoveWidgetEndpoint:
    def test_valid_returns_200(self, client, mock_layout_config_manager, mock_widget_order_manager):
        """Valid widget move returns 200."""
        response = client.post(
            "/api/layout/move-widget",
            data=json.dumps(
                {
                    "widget_id": "widget123",
                    "source_tab": "Home",
                    "dest_tab": "Tech",
                    "dest_col_index": 1,
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        mock_layout_config_manager.move_widget.assert_called_once_with(
            "widget123",
            "Home",
            "Tech",
            1,
        )
        mock_widget_order_manager.remove_widget.assert_called_once_with("Home", "widget123")

    def test_missing_fields_returns_400(self, client):
        """Missing required fields returns 400."""
        response = client.post(
            "/api/layout/move-widget",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_not_found_returns_404(self, client, mock_layout_config_manager):
        """Widget not found returns 404."""
        mock_layout_config_manager.move_widget.side_effect = ValueError("Widget not found")
        response = client.post(
            "/api/layout/move-widget",
            data=json.dumps(
                {
                    "widget_id": "nonexistent",
                    "source_tab": "Home",
                    "dest_tab": "Tech",
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 404
