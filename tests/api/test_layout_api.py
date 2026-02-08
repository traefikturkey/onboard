"""Tests for layout API endpoints."""

import json
from unittest.mock import MagicMock

import pytest

from app.api.layout import create_layout_blueprint
from app.factory import create_app

# All POST/DELETE/PUT/PATCH requests need Origin header for CSRF check
ORIGIN_HEADER = {"Origin": "http://localhost"}


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
            headers=ORIGIN_HEADER,
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
            headers=ORIGIN_HEADER,
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
            headers=ORIGIN_HEADER,
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
            headers=ORIGIN_HEADER,
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
            headers=ORIGIN_HEADER,
        )
        assert response.status_code == 400

    def test_missing_columns_returns_400(self, client):
        """Missing columns field returns 400."""
        response = client.post(
            "/api/layout/reorder",
            data=json.dumps({"tab": "Home"}),
            content_type="application/json",
            headers=ORIGIN_HEADER,
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
            headers=ORIGIN_HEADER,
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
            headers=ORIGIN_HEADER,
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
            headers=ORIGIN_HEADER,
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
            headers=ORIGIN_HEADER,
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
            headers=ORIGIN_HEADER,
        )
        assert response.status_code == 400

    def test_duplicate_returns_409(self, client, mock_layout_config_manager):
        """Duplicate tab name returns 409."""
        mock_layout_config_manager.add_tab.side_effect = ValueError("Tab already exists")
        response = client.post(
            "/api/layout/tabs",
            data=json.dumps({"name": "Home"}),
            content_type="application/json",
            headers=ORIGIN_HEADER,
        )
        assert response.status_code == 409


class TestDeleteTabEndpoint:
    def test_valid_returns_200(self, client, mock_layout_config_manager):
        """Valid tab deletion returns 200."""
        response = client.delete("/api/layout/tabs/Home", headers=ORIGIN_HEADER)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        mock_layout_config_manager.delete_tab.assert_called_once_with("Home")

    def test_not_found_returns_404(self, client, mock_layout_config_manager):
        """Tab not found returns 404."""
        mock_layout_config_manager.delete_tab.side_effect = ValueError("Tab not found")
        response = client.delete("/api/layout/tabs/NonExistent", headers=ORIGIN_HEADER)
        assert response.status_code == 404

    def test_last_tab_returns_400(self, client, mock_layout_config_manager):
        """Cannot delete the last tab returns 400."""
        mock_layout_config_manager.delete_tab.side_effect = ValueError(
            "Cannot delete the last tab"
        )
        response = client.delete("/api/layout/tabs/Home", headers=ORIGIN_HEADER)
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
            headers=ORIGIN_HEADER,
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
            headers=ORIGIN_HEADER,
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
            headers=ORIGIN_HEADER,
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
            headers=ORIGIN_HEADER,
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
            headers=ORIGIN_HEADER,
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
            headers=ORIGIN_HEADER,
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
            headers=ORIGIN_HEADER,
        )
        assert response.status_code == 404


class TestAddRowEndpoint:
    """Tests for POST /api/layout/rows endpoint."""

    def test_valid_returns_201(self, client, mock_layout_config_manager):
        """Valid row addition returns 201."""
        mock_layout_config_manager.add_row.return_value = None
        response = client.post(
            "/api/layout/rows",
            data=json.dumps({"tab": "Home"}),
            content_type="application/json",
            headers=ORIGIN_HEADER,
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["success"] is True
        assert data["message"] == "Row added"
        mock_layout_config_manager.add_row.assert_called_once_with("Home", 3)

    def test_missing_tab_returns_400(self, client):
        """Missing tab returns 400."""
        response = client.post(
            "/api/layout/rows",
            data=json.dumps({}),
            content_type="application/json",
            headers=ORIGIN_HEADER,
        )
        assert response.status_code == 400

    def test_nonexistent_tab_returns_404(self, client, mock_layout_config_manager):
        """Nonexistent tab returns 404."""
        mock_layout_config_manager.add_row.side_effect = ValueError("Tab 'Missing' not found")
        response = client.post(
            "/api/layout/rows",
            data=json.dumps({"tab": "Missing"}),
            content_type="application/json",
            headers=ORIGIN_HEADER,
        )
        assert response.status_code == 404

    def test_custom_num_columns(self, client, mock_layout_config_manager):
        """Custom num_columns is passed through."""
        mock_layout_config_manager.add_row.return_value = None
        response = client.post(
            "/api/layout/rows",
            data=json.dumps({"tab": "Home", "num_columns": 5}),
            content_type="application/json",
            headers=ORIGIN_HEADER,
        )
        assert response.status_code == 201
        mock_layout_config_manager.add_row.assert_called_once_with("Home", 5)

    def test_invalid_num_columns_returns_400(self, client):
        """num_columns out of range returns 400."""
        response = client.post(
            "/api/layout/rows",
            data=json.dumps({"tab": "Home", "num_columns": 0}),
            content_type="application/json",
            headers=ORIGIN_HEADER,
        )
        assert response.status_code == 400

        response = client.post(
            "/api/layout/rows",
            data=json.dumps({"tab": "Home", "num_columns": 13}),
            content_type="application/json",
            headers=ORIGIN_HEADER,
        )
        assert response.status_code == 400


class TestSSRFProtection:
    """Tests for SSRF protection in feed URL validation."""

    def test_localhost_rejected(self, client):
        """Feed URL pointing to localhost should be rejected."""
        response = client.post(
            "/api/layout/widgets",
            data=json.dumps({
                "tab": "Home",
                "name": "Test",
                "feed_url": "http://localhost/feed",
            }),
            content_type="application/json",
            headers=ORIGIN_HEADER,
        )
        assert response.status_code == 400

    def test_loopback_ip_rejected(self, client):
        """Feed URL pointing to 127.0.0.1 should be rejected."""
        response = client.post(
            "/api/layout/widgets",
            data=json.dumps({
                "tab": "Home",
                "name": "Test",
                "feed_url": "http://127.0.0.1/feed",
            }),
            content_type="application/json",
            headers=ORIGIN_HEADER,
        )
        assert response.status_code == 400

    def test_private_ip_rejected(self, client):
        """Feed URL pointing to private IP should be rejected."""
        response = client.post(
            "/api/layout/widgets",
            data=json.dumps({
                "tab": "Home",
                "name": "Test",
                "feed_url": "http://10.0.0.1/feed",
            }),
            content_type="application/json",
            headers=ORIGIN_HEADER,
        )
        assert response.status_code == 400

    def test_metadata_endpoint_rejected(self, client):
        """Feed URL pointing to cloud metadata endpoint should be rejected."""
        response = client.post(
            "/api/layout/widgets",
            data=json.dumps({
                "tab": "Home",
                "name": "Test",
                "feed_url": "http://169.254.169.254/latest/meta-data/",
            }),
            content_type="application/json",
            headers=ORIGIN_HEADER,
        )
        assert response.status_code == 400

    def test_valid_external_url_accepted(self, client, mock_layout_config_manager):
        """Valid external feed URL should be accepted."""
        mock_layout_config_manager.add_widget.return_value = "widget123"
        response = client.post(
            "/api/layout/widgets",
            data=json.dumps({
                "tab": "Home",
                "name": "Test",
                "feed_url": "https://example.com/feed.xml",
            }),
            content_type="application/json",
            headers=ORIGIN_HEADER,
        )
        assert response.status_code == 201


class TestYAMLInjection:
    """Tests for YAML injection protection in name validation."""

    def test_newline_in_tab_name_rejected(self, client):
        """Tab name with newline should be rejected."""
        response = client.post(
            "/api/layout/tabs",
            data=json.dumps({"name": "Test\nInjection"}),
            content_type="application/json",
            headers=ORIGIN_HEADER,
        )
        assert response.status_code == 400

    def test_null_byte_in_tab_name_rejected(self, client):
        """Tab name with null byte should be rejected."""
        response = client.post(
            "/api/layout/tabs",
            data=json.dumps({"name": "Test\x00Injection"}),
            content_type="application/json",
            headers=ORIGIN_HEADER,
        )
        assert response.status_code == 400

    def test_yaml_metachar_in_tab_name_rejected(self, client):
        """Tab name starting with YAML metacharacter should be rejected."""
        for char in ["{", "[", "&", "*", "!", "|", ">", "%", "@", "`"]:
            response = client.post(
                "/api/layout/tabs",
                data=json.dumps({"name": f"{char}injection"}),
                content_type="application/json",
                headers=ORIGIN_HEADER,
            )
            assert response.status_code == 400, f"Expected 400 for name starting with '{char}'"

    def test_newline_in_widget_name_rejected(self, client):
        """Widget name with newline should be rejected."""
        response = client.post(
            "/api/layout/widgets",
            data=json.dumps({
                "tab": "Home",
                "name": "Test\nInjection",
                "feed_url": "https://example.com/feed",
            }),
            content_type="application/json",
            headers=ORIGIN_HEADER,
        )
        assert response.status_code == 400


class TestErrorSanitization:
    """Tests for 500 error response sanitization."""

    def test_500_does_not_expose_internals(self, client, mock_widget_order_manager):
        """500 errors should not expose internal error details."""
        mock_widget_order_manager.update_columns.side_effect = RuntimeError(
            "SQLALCHEMY_DATABASE_URI=postgresql://secret:pass@db/mydb"
        )
        response = client.post(
            "/api/layout/reorder",
            data=json.dumps({
                "tab": "Home",
                "columns": [{"col_key": "0.0", "widget_ids": ["a"]}],
            }),
            content_type="application/json",
            headers=ORIGIN_HEADER,
        )
        assert response.status_code == 500
        data = response.get_json()
        assert "secret" not in str(data)
        assert "postgresql" not in str(data)
        assert data["details"] == "An internal error occurred"
        assert data["error"] == "InternalError"


class TestCSRFProtection:
    """Tests for CSRF protection."""

    def test_post_without_origin_returns_403(self, client):
        """POST without Origin header should be rejected."""
        response = client.post(
            "/api/layout/tabs",
            data=json.dumps({"name": "Test"}),
            content_type="application/json",
        )
        assert response.status_code == 403
        data = response.get_json()
        assert data["error"] == "Forbidden"

    def test_delete_without_origin_returns_403(self, client):
        """DELETE without Origin header should be rejected."""
        response = client.delete("/api/layout/tabs/Home")
        assert response.status_code == 403

    def test_get_without_origin_allowed(self, client, mock_layout_config_manager):
        """GET requests should not require Origin header."""
        response = client.get("/api/layout/tabs")
        assert response.status_code == 200

    def test_cross_origin_rejected(self, client):
        """Cross-origin POST should be rejected."""
        response = client.post(
            "/api/layout/tabs",
            data=json.dumps({"name": "Test"}),
            content_type="application/json",
            headers={"Origin": "http://evil.com"},
        )
        assert response.status_code == 403
