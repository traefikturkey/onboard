"""Tests for WidgetOrderManager service."""

import json
import os
from unittest.mock import MagicMock

import pytest

from app.services.widget_order_manager import WidgetOrderManager


@pytest.fixture
def tmp_config(tmp_path):
    """Provide a temporary config file path."""
    return tmp_path / "widget_order.json"


@pytest.fixture
def mock_file_store(tmp_config):
    """Create a mock file store that reads/writes to temp path."""
    store = MagicMock()

    def read_json(path):
        with open(path, "r") as f:
            return json.load(f)

    def write_json_atomic(path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    store.read_json.side_effect = read_json
    store.write_json_atomic.side_effect = write_json_atomic
    return store


def make_manager(tmp_config, mock_file_store, initial_data=None):
    """Helper to create a WidgetOrderManager with optional initial data."""
    if initial_data is not None:
        tmp_config.parent.mkdir(parents=True, exist_ok=True)
        with open(tmp_config, "w") as f:
            json.dump(initial_data, f)

    # Patch pwd to point to tmp_path parent
    manager = object.__new__(WidgetOrderManager)
    manager.config_path = tmp_config
    manager.file_store = mock_file_store
    manager._data = {"tabs": {}}
    manager._load()
    return manager


class TestWidgetOrderManagerLoad:
    def test_load_missing_file(self, tmp_config, mock_file_store):
        """Missing file initializes empty structure."""
        manager = make_manager(tmp_config, mock_file_store)
        assert manager._data == {"tabs": {}}

    def test_load_valid_overlay(self, tmp_config, mock_file_store):
        """Valid file loads correctly."""
        data = {"tabs": {"Home": {"0.0": ["a", "b"]}}}
        manager = make_manager(tmp_config, mock_file_store, initial_data=data)
        assert manager._data == data


class TestWidgetOrderManagerGetColumnOrder:
    def test_existing_column(self, tmp_config, mock_file_store):
        data = {"tabs": {"Home": {"0.0": ["a", "b"]}}}
        manager = make_manager(tmp_config, mock_file_store, initial_data=data)
        assert manager.get_column_order("Home", "0.0") == ["a", "b"]

    def test_missing_column(self, tmp_config, mock_file_store):
        data = {"tabs": {"Home": {"0.0": ["a"]}}}
        manager = make_manager(tmp_config, mock_file_store, initial_data=data)
        assert manager.get_column_order("Home", "1.0") == []

    def test_missing_tab(self, tmp_config, mock_file_store):
        manager = make_manager(tmp_config, mock_file_store)
        assert manager.get_column_order("Missing", "0.0") == []


class TestWidgetOrderManagerUpdateColumns:
    def test_update_writes_correctly(self, tmp_config, mock_file_store):
        manager = make_manager(tmp_config, mock_file_store)
        manager.update_columns("Home", [
            {"col_key": "0.0", "widget_ids": ["x", "y"]},
            {"col_key": "0.1", "widget_ids": ["z"]},
        ])
        assert manager.get_column_order("Home", "0.0") == ["x", "y"]
        assert manager.get_column_order("Home", "0.1") == ["z"]
        mock_file_store.write_json_atomic.assert_called()

    def test_update_preserves_other_tabs(self, tmp_config, mock_file_store):
        data = {"tabs": {"Other": {"0.0": ["a"]}}}
        manager = make_manager(tmp_config, mock_file_store, initial_data=data)
        manager.update_columns("Home", [{"col_key": "0.0", "widget_ids": ["b"]}])
        assert manager.get_column_order("Other", "0.0") == ["a"]
        assert manager.get_column_order("Home", "0.0") == ["b"]


class TestWidgetOrderManagerReconcile:
    def test_drops_removed_widgets(self, tmp_config, mock_file_store):
        data = {"tabs": {"Home": {"0.0": ["a", "b", "c"]}}}
        manager = make_manager(tmp_config, mock_file_store, initial_data=data)
        manager.reconcile("Home", {"0.0": ["a", "c"]})
        assert manager.get_column_order("Home", "0.0") == ["a", "c"]

    def test_appends_new_widgets(self, tmp_config, mock_file_store):
        data = {"tabs": {"Home": {"0.0": ["a"]}}}
        manager = make_manager(tmp_config, mock_file_store, initial_data=data)
        manager.reconcile("Home", {"0.0": ["a", "b", "c"]})
        assert manager.get_column_order("Home", "0.0") == ["a", "b", "c"]

    def test_preserves_order(self, tmp_config, mock_file_store):
        data = {"tabs": {"Home": {"0.0": ["c", "a", "b"]}}}
        manager = make_manager(tmp_config, mock_file_store, initial_data=data)
        manager.reconcile("Home", {"0.0": ["a", "b", "c"]})
        # Saved order: c, a, b — all exist, so order preserved
        assert manager.get_column_order("Home", "0.0") == ["c", "a", "b"]

    def test_reconcile_empty_saved(self, tmp_config, mock_file_store):
        manager = make_manager(tmp_config, mock_file_store)
        manager.reconcile("Home", {"0.0": ["a", "b"]})
        assert manager.get_column_order("Home", "0.0") == ["a", "b"]


class TestWidgetOrderManagerMtime:
    def test_mtime_missing_file(self, tmp_config, mock_file_store):
        manager = make_manager(tmp_config, mock_file_store)
        # File doesn't exist after empty init
        if tmp_config.exists():
            os.unlink(tmp_config)
        assert manager.mtime == 0

    def test_mtime_existing_file(self, tmp_config, mock_file_store):
        data = {"tabs": {}}
        manager = make_manager(tmp_config, mock_file_store, initial_data=data)
        assert manager.mtime > 0


class TestRemoveWidget:
    def test_removes_from_column(self, tmp_config, mock_file_store):
        data = {"tabs": {"Home": {"0.0": ["a", "b", "c"]}}}
        manager = make_manager(tmp_config, mock_file_store, initial_data=data)
        manager.remove_widget("Home", "b")
        assert manager.get_column_order("Home", "0.0") == ["a", "c"]

    def test_removes_from_multiple_columns(self, tmp_config, mock_file_store):
        data = {"tabs": {"Home": {"0.0": ["a", "b"], "0.1": ["b", "c"]}}}
        manager = make_manager(tmp_config, mock_file_store, initial_data=data)
        manager.remove_widget("Home", "b")
        assert manager.get_column_order("Home", "0.0") == ["a"]
        assert manager.get_column_order("Home", "0.1") == ["c"]

    def test_noop_when_not_found(self, tmp_config, mock_file_store):
        data = {"tabs": {"Home": {"0.0": ["a", "b"]}}}
        manager = make_manager(tmp_config, mock_file_store, initial_data=data)
        manager.remove_widget("Home", "z")
        assert manager.get_column_order("Home", "0.0") == ["a", "b"]
