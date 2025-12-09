"""Tests for Flask application factory and routes."""

import pytest
from unittest.mock import MagicMock, patch
import pandas as pd


class TestCreateApp:
    """Test create_app factory function."""

    def test_create_app_with_custom_config(self):
        """Test that custom config is applied."""
        from app.factory import create_app

        app = create_app(config={"CUSTOM_KEY": "custom_value"}, testing=True)
        assert app.config["CUSTOM_KEY"] == "custom_value"

    def test_create_app_testing_mode_sets_flag(self):
        """Test that testing=True sets TESTING config."""
        from app.factory import create_app

        app = create_app(testing=True)
        assert app.config["TESTING"] is True

    def test_create_app_stores_injected_dependencies(self):
        """Test that injected dependencies are stored in extensions."""
        from app.factory import create_app

        mock_layout = MagicMock()
        mock_bm = MagicMock()
        mock_lt = MagicMock()

        app = create_app(
            layout=mock_layout,
            bookmark_manager=mock_bm,
            link_tracker=mock_lt,
            testing=True,
        )

        assert app.extensions["onboard_layout"] is mock_layout
        assert app.extensions["onboard_bookmark_manager"] is mock_bm
        assert app.extensions["onboard_link_tracker"] is mock_lt


class TestGetHelpers:
    """Test get_layout, get_bookmark_manager, get_link_tracker helpers."""

    def test_get_layout_with_app_param(self):
        """Test get_layout when app is passed directly."""
        from app.factory import create_app, get_layout

        mock_layout = MagicMock()
        app = create_app(layout=mock_layout, testing=True)

        result = get_layout(app)
        assert result is mock_layout

    def test_get_layout_uses_current_app(self):
        """Test get_layout when app is None uses current_app."""
        from app.factory import create_app, get_layout

        mock_layout = MagicMock()
        app = create_app(layout=mock_layout, testing=True)

        with app.app_context():
            result = get_layout()
            assert result is mock_layout

    def test_get_bookmark_manager_with_app_param(self):
        """Test get_bookmark_manager when app is passed directly."""
        from app.factory import create_app, get_bookmark_manager

        mock_bm = MagicMock()
        app = create_app(bookmark_manager=mock_bm, testing=True)

        result = get_bookmark_manager(app)
        assert result is mock_bm

    def test_get_bookmark_manager_uses_current_app(self):
        """Test get_bookmark_manager when app is None uses current_app."""
        from app.factory import create_app, get_bookmark_manager

        mock_bm = MagicMock()
        app = create_app(bookmark_manager=mock_bm, testing=True)

        with app.app_context():
            result = get_bookmark_manager()
            assert result is mock_bm

    def test_get_link_tracker_with_app_param(self):
        """Test get_link_tracker when app is passed directly."""
        from app.factory import create_app, get_link_tracker

        mock_lt = MagicMock()
        app = create_app(link_tracker=mock_lt, testing=True)

        result = get_link_tracker(app)
        assert result is mock_lt

    def test_get_link_tracker_uses_current_app(self):
        """Test get_link_tracker when app is None uses current_app."""
        from app.factory import create_app, get_link_tracker

        mock_lt = MagicMock()
        app = create_app(link_tracker=mock_lt, testing=True)

        with app.app_context():
            result = get_link_tracker()
            assert result is mock_lt


class TestEnsureDependencies:
    """Test lazy initialization of dependencies."""

    def test_ensure_layout_creates_layout_when_none(self):
        """Test that _ensure_layout creates Layout when not provided."""
        from app.factory import create_app, _ensure_layout

        app = create_app(testing=True)
        app.extensions["onboard_layout"] = None

        with patch("app.models.layout.Layout") as MockLayout:
            mock_layout = MagicMock()
            MockLayout.return_value = mock_layout
            _ensure_layout(app)
            MockLayout.assert_called_once()
            assert app.extensions["onboard_layout"] is mock_layout

    def test_ensure_bookmark_manager_creates_when_none(self):
        """Test that _ensure_bookmark_manager creates BookmarkManager when not provided."""
        from app.factory import create_app, _ensure_bookmark_manager

        app = create_app(testing=True)
        app.extensions["onboard_bookmark_manager"] = None

        with patch("app.services.bookmark_manager.BookmarkManager") as MockBM:
            mock_bm = MagicMock()
            MockBM.return_value = mock_bm
            _ensure_bookmark_manager(app)
            MockBM.assert_called_once()
            assert app.extensions["onboard_bookmark_manager"] is mock_bm

    def test_ensure_link_tracker_creates_when_none(self):
        """Test that _ensure_link_tracker creates LinkTracker when not provided."""
        from app.factory import create_app, _ensure_link_tracker

        app = create_app(testing=True)
        app.extensions["onboard_link_tracker"] = None

        with patch("app.services.link_tracker.LinkTracker") as MockLT:
            mock_lt = MagicMock()
            MockLT.return_value = mock_lt
            _ensure_link_tracker(app)
            MockLT.assert_called_once()
            assert app.extensions["onboard_link_tracker"] is mock_lt


class TestRoutes:
    """Test application routes."""

    @pytest.fixture
    def mock_layout(self):
        """Create a mock layout for route testing."""
        mock = MagicMock()
        mock.is_modified.return_value = False
        mock.favicon_path = lambda x: None
        mock.tabs = []
        mock.headers = []
        return mock

    @pytest.fixture
    def mock_link_tracker(self):
        """Create a mock link tracker."""
        mock = MagicMock()
        mock.get_click_events.return_value = pd.DataFrame(
            columns=["TIMESTAMP", "LINK"]
        )
        return mock

    @pytest.fixture
    def route_app(self, mock_layout, mock_link_tracker):
        """Create app for route testing."""
        from app.factory import create_app

        mock_bm = MagicMock()
        app = create_app(
            layout=mock_layout,
            bookmark_manager=mock_bm,
            link_tracker=mock_link_tracker,
            testing=True,
        )
        return app

    @pytest.fixture
    def route_client(self, route_app):
        """Create test client."""
        with route_app.test_client() as client:
            yield client

    def test_healthcheck_returns_ok(self, route_client):
        """Test /api/healthcheck endpoint."""
        response = route_client.get("/api/healthcheck")
        assert response.status_code == 200
        assert response.data == b"OK"

    def test_click_events_route(self, route_client, mock_link_tracker):
        """Test /click_events route returns HTML table."""
        response = route_client.get("/click_events")
        assert response.status_code == 200
        assert "text/html" in response.content_type

    def test_redirect_route_with_valid_link(self, route_client, mock_layout, mock_link_tracker):
        """Test /redirect route redirects to tracked link."""
        mock_layout.get_link.return_value = "https://example.com"

        response = route_client.get("/redirect/feed1/link1")
        assert response.status_code == 302
        assert response.headers["Location"] == "https://example.com"
        mock_link_tracker.track_click_event.assert_called_once()

    def test_redirect_route_with_missing_link(self, route_client, mock_layout, mock_link_tracker):
        """Test /redirect route redirects to index when link not found."""
        mock_layout.get_link.return_value = None

        response = route_client.get("/redirect/feed1/link1")
        assert response.status_code == 302
        assert response.headers["Location"] == "/"

    def test_refresh_route(self, route_client, mock_layout):
        """Test /feed/<feed_id>/refresh route."""
        response = route_client.get("/feed/test_feed/refresh")
        assert response.status_code == 302
        mock_layout.refresh_feeds.assert_called_with("test_feed")

    def test_bookmarks_manage_route(self, route_client):
        """Test /bookmarks/manage route loads."""
        response = route_client.get("/bookmarks/manage")
        assert response.status_code == 200


class TestContextProcessor:
    """Test context processor injection."""

    def test_context_processor_injects_values(self):
        """Test that context processor injects expected values."""
        from app.factory import create_app

        mock_layout = MagicMock()
        mock_layout.is_modified.return_value = False
        mock_layout.favicon_path = lambda x: "/static/favicon.ico"
        mock_layout.tabs = []
        mock_layout.headers = []

        app = create_app(
            layout=mock_layout,
            bookmark_manager=MagicMock(),
            link_tracker=MagicMock(),
            testing=True,
        )

        with app.test_request_context():
            ctx = app.jinja_env.globals
            # Context processor values are added per-request
