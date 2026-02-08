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
def app(mock_widget_order_manager):
    """Create test Flask app with mock widget order manager."""
    app = create_app(
        layout=MagicMock(),
        bookmark_manager=MagicMock(),
        link_tracker=MagicMock(),
        widget_order_manager=mock_widget_order_manager,
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
