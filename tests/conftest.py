"""Shared pytest fixtures for test isolation and dependency injection."""

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_layout():
    """Create a mock Layout for testing."""
    mock = MagicMock()
    mock.is_modified.return_value = False
    mock.favicon_path = lambda x: None
    return mock


@pytest.fixture
def mock_bookmark_manager():
    """Create a mock BookmarkManager for testing."""
    return MagicMock()


@pytest.fixture
def mock_link_tracker():
    """Create a mock LinkTracker for testing."""
    mock = MagicMock()
    import pandas as pd

    mock.get_click_events.return_value = pd.DataFrame(
        columns=["TIMESTAMP", "LINK"]
    )
    return mock


@pytest.fixture
def test_app(mock_layout, mock_bookmark_manager, mock_link_tracker):
    """Create a test app with injected mock dependencies."""
    from app.factory import create_app

    app = create_app(
        layout=mock_layout,
        bookmark_manager=mock_bookmark_manager,
        link_tracker=mock_link_tracker,
        testing=True,
    )
    app.config["TESTING"] = True
    return app


@pytest.fixture
def test_client(test_app):
    """Create a test client for the test app."""
    with test_app.test_client() as client:
        yield client
