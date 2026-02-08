"""Service for managing widget display order with JSON overlay persistence."""

import logging
import os
from pathlib import Path
from typing import Any

from app.models.local_file_store import LocalFileStore
from app.models.utils import pwd

logger = logging.getLogger(__name__)


class WidgetOrderManager:
    """Manages widget ordering overlay stored in a JSON file."""

    def __init__(
        self,
        config_file: str = "configs/widget_order.json",
        file_store=None,
    ):
        self.config_path = Path(pwd.joinpath(config_file))
        self.file_store = file_store or LocalFileStore()
        self._data: dict[str, Any] = {"tabs": {}}
        self._load()

    def _load(self):
        """Load the overlay file, or initialize empty if missing."""
        try:
            if self.config_path.exists():
                self._data = self.file_store.read_json(self.config_path)
            else:
                self._data = {"tabs": {}}
        except Exception:
            logger.exception("Failed to load widget order overlay")
            self._data = {"tabs": {}}

    def _save(self):
        """Atomically write overlay to disk."""
        self.file_store.write_json_atomic(self.config_path, self._data)

    @property
    def mtime(self) -> float:
        """Return modification time of overlay file, or 0 if missing."""
        try:
            return os.path.getmtime(self.config_path)
        except OSError:
            return 0

    def get_column_order(self, tab: str, col_key: str) -> list[str]:
        """Return ordered widget ID list for a column, or empty list."""
        return self._data.get("tabs", {}).get(tab, {}).get(col_key, [])

    def update_columns(self, tab: str, columns_data: list[dict]) -> None:
        """Update widget ordering for multiple columns in a tab.

        Args:
            tab: Tab name
            columns_data: List of dicts with 'col_key' and 'widget_ids' keys
        """
        if "tabs" not in self._data:
            self._data["tabs"] = {}
        if tab not in self._data["tabs"]:
            self._data["tabs"][tab] = {}

        for col in columns_data:
            col_key = col["col_key"]
            widget_ids = col["widget_ids"]
            self._data["tabs"][tab][col_key] = widget_ids

        self._save()

    def reconcile(self, tab: str, actual_widgets_by_column: dict[str, list[str]]) -> None:
        """Reconcile overlay with actual layout widgets.

        Drops widget IDs no longer in layout, appends new ones, preserves order.

        Args:
            tab: Tab name
            actual_widgets_by_column: Dict of {col_key: [widget_id, ...]} from live layout
        """
        tab_data = self._data.get("tabs", {}).get(tab, {})
        new_tab_data = {}

        for col_key, actual_ids in actual_widgets_by_column.items():
            actual_set = set(actual_ids)
            saved_ids = tab_data.get(col_key, [])

            # Keep saved order for widgets that still exist
            ordered = [wid for wid in saved_ids if wid in actual_set]
            # Append new widgets not in saved order
            ordered_set = set(ordered)
            for wid in actual_ids:
                if wid not in ordered_set:
                    ordered.append(wid)

            new_tab_data[col_key] = ordered

        if "tabs" not in self._data:
            self._data["tabs"] = {}
        self._data["tabs"][tab] = new_tab_data
        self._save()
