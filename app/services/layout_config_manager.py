"""Service for managing layout configuration (tabs, widgets) via layout.yml."""

import logging
import os
import tempfile
from pathlib import Path

import yaml

from app.models.utils import calculate_sha1_hash, pwd

logger = logging.getLogger(__name__)


class LayoutConfigManager:
    """Reads, mutates, and writes layout.yml for tab/widget management."""

    def __init__(self, config_path=None):
        self.config_path = Path(config_path) if config_path else pwd / "configs" / "layout.yml"

    def _read(self):
        """Load YAML from disk."""
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _write(self, data):
        """Atomic write: tempfile + os.replace."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=self.config_path.parent,
            delete=False,
            suffix=".tmp",
        ) as tmp:
            yaml.dump(data, tmp, default_flow_style=False, allow_unicode=True, sort_keys=False)
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp_path = tmp.name
        os.replace(tmp_path, self.config_path)

    def get_tab_names(self):
        """Return list of all tab names."""
        data = self._read()
        tabs = data.get("tabs", [])
        return [t["tab"] for t in tabs if "tab" in t]

    def add_tab(self, name):
        """Add an empty tab with one empty column. Returns the new tab dict.

        Raises ValueError if a tab with the same name (case-insensitive) exists.
        """
        data = self._read()
        tabs = data.get("tabs", [])
        existing_names = {t["tab"].lower() for t in tabs if "tab" in t}
        if name.strip().lower() in existing_names:
            raise ValueError(f"Tab '{name}' already exists")

        new_tab = {
            "tab": name.strip(),
            "columns": [{"column": None, "widgets": []}],
        }
        tabs.append(new_tab)
        data["tabs"] = tabs
        self._write(data)
        return new_tab

    def delete_tab(self, name):
        """Remove a tab by name.

        Raises ValueError if tab not found or if it's the last tab.
        """
        data = self._read()
        tabs = data.get("tabs", [])

        idx = None
        for i, t in enumerate(tabs):
            if t.get("tab", "").lower() == name.lower():
                idx = i
                break

        if idx is None:
            raise ValueError(f"Tab '{name}' not found")

        if len(tabs) <= 1:
            raise ValueError("Cannot delete the last tab")

        tabs.pop(idx)
        data["tabs"] = tabs
        self._write(data)

    def add_widget(self, tab, widget_data, col_index=0):
        """Add a feed widget to a tab's column. Returns the generated widget_id.

        Raises ValueError if tab not found or col_index out of range.
        """
        data = self._read()
        tabs = data.get("tabs", [])

        tab_dict = None
        for t in tabs:
            if t.get("tab", "").lower() == tab.lower():
                tab_dict = t
                break

        if tab_dict is None:
            raise ValueError(f"Tab '{tab}' not found")

        columns = self._get_columns(tab_dict)
        if col_index >= len(columns):
            raise ValueError(
                f"Column index {col_index} out of range (tab has {len(columns)} columns)"
            )

        col = columns[col_index]
        widgets_list = col.get("widgets", [])
        widgets_list.append(widget_data)
        col["widgets"] = widgets_list

        self._write(data)

        # Compute widget ID same way as Widget.__init__
        id_source = widget_data.get("link", widget_data.get("name", ""))
        return calculate_sha1_hash(id_source)

    def move_widget(self, widget_id, source_tab, dest_tab, dest_col_index=0):
        """Move a widget from source_tab to dest_tab.

        Raises ValueError if widget not found, tabs not found, or same tab.
        """
        if source_tab.lower() == dest_tab.lower():
            raise ValueError("Source and destination tabs are the same")

        data = self._read()
        tabs = data.get("tabs", [])

        source_dict = None
        dest_dict = None
        for t in tabs:
            name = t.get("tab", "")
            if name.lower() == source_tab.lower():
                source_dict = t
            if name.lower() == dest_tab.lower():
                dest_dict = t

        if source_dict is None:
            raise ValueError(f"Source tab '{source_tab}' not found")
        if dest_dict is None:
            raise ValueError(f"Destination tab '{dest_tab}' not found")

        # Find and remove widget from source
        widget_data = self._find_and_remove_widget(source_dict, widget_id)
        if widget_data is None:
            raise ValueError(f"Widget '{widget_id}' not found in tab '{source_tab}'")

        # Add to destination
        dest_columns = self._get_columns(dest_dict)
        if dest_col_index >= len(dest_columns):
            dest_col_index = 0

        col = dest_columns[dest_col_index]
        widgets_list = col.get("widgets", [])
        widgets_list.append(widget_data)
        col["widgets"] = widgets_list

        self._write(data)

    def _get_columns(self, tab_dict):
        """Get the flat list of leaf columns from a tab dict."""
        columns = []
        if "columns" in tab_dict:
            self._collect_leaf_columns(tab_dict["columns"], columns)
        elif "rows" in tab_dict:
            for row_data in tab_dict["rows"]:
                row = row_data.get("row", row_data) if isinstance(row_data, dict) else row_data
                if row and isinstance(row, dict) and "columns" in row:
                    self._collect_leaf_columns(row["columns"], columns)
                elif isinstance(row_data, dict) and "columns" in row_data:
                    self._collect_leaf_columns(row_data["columns"], columns)
        return columns

    def _collect_leaf_columns(self, columns_list, result):
        """Recursively collect leaf columns (those with widgets, not nested rows)."""
        for col_data in columns_list:
            col = col_data.get("column", col_data) if isinstance(col_data, dict) else col_data
            actual = col_data if isinstance(col_data, dict) else {}

            if "rows" in actual:
                for row_data in actual["rows"]:
                    row = row_data.get("row", row_data) if isinstance(row_data, dict) else row_data
                    if row and isinstance(row, dict) and "columns" in row:
                        self._collect_leaf_columns(row["columns"], result)
                    elif isinstance(row_data, dict) and "columns" in row_data:
                        self._collect_leaf_columns(row_data["columns"], result)
            else:
                result.append(actual)

    def _find_and_remove_widget(self, tab_dict, widget_id):
        """Find a widget by ID in a tab and remove it. Returns the widget dict or None."""
        if "columns" in tab_dict:
            return self._search_columns(tab_dict["columns"], widget_id)
        if "rows" in tab_dict:
            for row_data in tab_dict["rows"]:
                row = row_data.get("row", row_data) if isinstance(row_data, dict) else row_data
                if row and isinstance(row, dict) and "columns" in row:
                    result = self._search_columns(row["columns"], widget_id)
                    if result:
                        return result
                elif isinstance(row_data, dict) and "columns" in row_data:
                    result = self._search_columns(row_data["columns"], widget_id)
                    if result:
                        return result
        return None

    def _search_columns(self, columns_list, widget_id):
        """Search columns for a widget and remove it if found."""
        for col_data in columns_list:
            actual = col_data if isinstance(col_data, dict) else {}

            if "rows" in actual:
                for row_data in actual["rows"]:
                    row = row_data.get("row", row_data) if isinstance(row_data, dict) else row_data
                    if row and isinstance(row, dict) and "columns" in row:
                        result = self._search_columns(row["columns"], widget_id)
                        if result:
                            return result
                    elif isinstance(row_data, dict) and "columns" in row_data:
                        result = self._search_columns(row_data["columns"], widget_id)
                        if result:
                            return result
            elif "widgets" in actual:
                widgets = actual["widgets"]
                for i, w in enumerate(widgets):
                    w_id_source = w.get("link", w.get("name", ""))
                    w_id = calculate_sha1_hash(w_id_source)
                    if w_id == widget_id:
                        return widgets.pop(i)
        return None
