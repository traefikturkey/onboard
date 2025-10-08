"""Service for managing bookmarks with CRUD operations."""

import json
import logging
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

from app.models.local_file_store import LocalFileStore
from app.models.utils import pwd
from app.services.bookmark_bar_manager import BookmarkBarManager

logger = logging.getLogger(__name__)


class BookmarkNotFoundError(Exception):
    """Raised when a bookmark at a specific index is not found."""

    pass


class SectionNotFoundError(Exception):
    """Raised when a section with a specific ID is not found."""

    pass


class InvalidIndexError(Exception):
    """Raised when an index is out of bounds."""

    pass


class BookmarkManager:
    """Manages bookmark CRUD operations with atomic saves."""

    def __init__(self, bookmark_file: str = "configs/bookmarks.json"):
        self.bookmark_path = Path(pwd.joinpath(bookmark_file))
        self.file_store = LocalFileStore()
        self.bar_manager = BookmarkBarManager(bookmark_file)
        self._data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """Load bookmarks from file."""
        try:
            self._data = self.file_store.read_json(self.bookmark_path)
            # Ensure structure
            if "bar" not in self._data:
                self._data["bar"] = []
            if "sections" not in self._data:
                self._data["sections"] = {}
        except FileNotFoundError:
            logger.warning("Bookmarks file not found, starting with empty data")
            self._data = {"bar": [], "sections": {}}
        except Exception as e:
            logger.error(f"Failed to load bookmarks: {e}")
            self._data = {"bar": [], "sections": {}}

    def _save(self) -> None:
        """Atomically save bookmarks to file."""
        try:
            self.file_store.write_json_atomic(self.bookmark_path, self._data)
            # Trigger reload in BookmarkBarManager
            self.bar_manager.reload()
            logger.info("Bookmarks saved successfully")
        except Exception as e:
            logger.error(f"Failed to save bookmarks: {e}")
            raise

    def reload(self) -> None:
        """Reload bookmarks from file."""
        self._load()

    # Bar Bookmark Operations

    def get_bar_bookmarks(self) -> list[dict[str, Any]]:
        """Get all bar bookmarks."""
        return deepcopy(self._data.get("bar", []))

    def get_bar_bookmark(self, index: int) -> dict[str, Any]:
        """Get a specific bar bookmark by index."""
        bar = self._data.get("bar", [])
        if index < 0 or index >= len(bar):
            raise InvalidIndexError(
                f"Index {index} out of bounds (bar has {len(bar)} bookmarks)"
            )
        return deepcopy(bar[index])

    def add_bar_bookmark(self, bookmark_data: dict[str, Any]) -> dict[str, Any]:
        """Add a bookmark to the bar."""
        # Add timestamp if not present
        if "add_date" not in bookmark_data:
            bookmark_data["add_date"] = str(int(time.time()))

        self._data["bar"].append(bookmark_data)
        self._save()
        return deepcopy(bookmark_data)

    def update_bar_bookmark(
        self, index: int, bookmark_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update a bar bookmark at a specific index."""
        bar = self._data.get("bar", [])
        if index < 0 or index >= len(bar):
            raise InvalidIndexError(
                f"Index {index} out of bounds (bar has {len(bar)} bookmarks)"
            )

        # Preserve add_date if not provided
        if "add_date" not in bookmark_data and "add_date" in bar[index]:
            bookmark_data["add_date"] = bar[index]["add_date"]

        self._data["bar"][index] = bookmark_data
        self._save()
        return deepcopy(bookmark_data)

    def delete_bar_bookmark(self, index: int) -> None:
        """Delete a bar bookmark at a specific index."""
        bar = self._data.get("bar", [])
        if index < 0 or index >= len(bar):
            raise InvalidIndexError(
                f"Index {index} out of bounds (bar has {len(bar)} bookmarks)"
            )

        del self._data["bar"][index]
        self._save()

    def reorder_bar_bookmarks(self, indices: list[int]) -> list[dict[str, Any]]:
        """Reorder bar bookmarks according to the provided index list."""
        bar = self._data.get("bar", [])

        # Validate indices
        if len(indices) != len(bar):
            raise ValueError(
                f"Indices list length ({len(indices)}) must match bar length ({len(bar)})"
            )

        if sorted(indices) != list(range(len(bar))):
            raise ValueError("Indices must be a permutation of 0 to len(bar)-1")

        # Reorder
        new_bar = [bar[i] for i in indices]
        self._data["bar"] = new_bar
        self._save()
        return deepcopy(new_bar)

    # Section Operations

    def get_all_sections(self) -> dict[str, dict[str, Any]]:
        """Get all sections."""
        return deepcopy(self._data.get("sections", {}))

    def get_section(self, section_id: str) -> dict[str, Any]:
        """Get a specific section by ID."""
        sections = self._data.get("sections", {})
        if section_id not in sections:
            raise SectionNotFoundError(f"Section '{section_id}' not found")
        return deepcopy(sections[section_id])

    def create_section(self, section_id: str, display_name: str) -> dict[str, Any]:
        """Create a new section."""
        sections = self._data.get("sections", {})
        if section_id in sections:
            raise ValueError(f"Section '{section_id}' already exists")

        section_data = {"displayName": display_name, "bookmarks": []}
        self._data["sections"][section_id] = section_data
        self._save()
        return deepcopy(section_data)

    def update_section(self, section_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Update a section's metadata (displayName)."""
        sections = self._data.get("sections", {})
        if section_id not in sections:
            raise SectionNotFoundError(f"Section '{section_id}' not found")

        # Only allow updating displayName, preserve bookmarks
        if "displayName" in data:
            self._data["sections"][section_id]["displayName"] = data["displayName"]

        self._save()
        return deepcopy(self._data["sections"][section_id])

    def delete_section(self, section_id: str) -> None:
        """Delete a section."""
        sections = self._data.get("sections", {})
        if section_id not in sections:
            raise SectionNotFoundError(f"Section '{section_id}' not found")

        del self._data["sections"][section_id]
        self._save()

    # Section Bookmark Operations

    def get_section_bookmarks(self, section_id: str) -> list[dict[str, Any]]:
        """Get all bookmarks in a section."""
        section = self.get_section(section_id)
        return deepcopy(section.get("bookmarks", []))

    def add_section_bookmark(
        self, section_id: str, bookmark_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Add a bookmark to a section."""
        sections = self._data.get("sections", {})
        if section_id not in sections:
            raise SectionNotFoundError(f"Section '{section_id}' not found")

        # Sections use 'link' instead of 'href'
        if "href" in bookmark_data and "link" not in bookmark_data:
            bookmark_data["link"] = bookmark_data.pop("href")

        self._data["sections"][section_id]["bookmarks"].append(bookmark_data)
        self._save()
        return deepcopy(bookmark_data)

    def update_section_bookmark(
        self, section_id: str, index: int, bookmark_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update a bookmark in a section at a specific index."""
        sections = self._data.get("sections", {})
        if section_id not in sections:
            raise SectionNotFoundError(f"Section '{section_id}' not found")

        bookmarks = sections[section_id].get("bookmarks", [])
        if index < 0 or index >= len(bookmarks):
            raise InvalidIndexError(
                f"Index {index} out of bounds (section has {len(bookmarks)} bookmarks)"
            )

        # Sections use 'link' instead of 'href'
        if "href" in bookmark_data and "link" not in bookmark_data:
            bookmark_data["link"] = bookmark_data.pop("href")

        self._data["sections"][section_id]["bookmarks"][index] = bookmark_data
        self._save()
        return deepcopy(bookmark_data)

    def delete_section_bookmark(self, section_id: str, index: int) -> None:
        """Delete a bookmark from a section at a specific index."""
        sections = self._data.get("sections", {})
        if section_id not in sections:
            raise SectionNotFoundError(f"Section '{section_id}' not found")

        bookmarks = sections[section_id].get("bookmarks", [])
        if index < 0 or index >= len(bookmarks):
            raise InvalidIndexError(
                f"Index {index} out of bounds (section has {len(bookmarks)} bookmarks)"
            )

        del self._data["sections"][section_id]["bookmarks"][index]
        self._save()

    def reorder_section_bookmarks(
        self, section_id: str, indices: list[int]
    ) -> list[dict[str, Any]]:
        """Reorder bookmarks in a section according to the provided index list."""
        sections = self._data.get("sections", {})
        if section_id not in sections:
            raise SectionNotFoundError(f"Section '{section_id}' not found")

        bookmarks = sections[section_id].get("bookmarks", [])

        # Validate indices
        if len(indices) != len(bookmarks):
            raise ValueError(
                f"Indices list length ({len(indices)}) must match bookmarks length ({len(bookmarks)})"
            )

        if sorted(indices) != list(range(len(bookmarks))):
            raise ValueError("Indices must be a permutation of 0 to len(bookmarks)-1")

        # Reorder
        new_bookmarks = [bookmarks[i] for i in indices]
        self._data["sections"][section_id]["bookmarks"] = new_bookmarks
        self._save()
        return deepcopy(new_bookmarks)

    # Advanced Operations

    def move_bookmark(
        self, source: dict[str, Any], destination: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Move a bookmark from source to destination.

        Args:
            source: {"type": "bar"|"section", "section_id": str|None, "index": int}
            destination: {"type": "bar"|"section", "section_id": str|None, "index": int}

        Returns:
            The moved bookmark data
        """
        # Get the bookmark from source
        if source["type"] == "bar":
            bookmark = self.get_bar_bookmark(source["index"])
            # Convert href to link for sections
            if "href" in bookmark:
                bookmark["link"] = bookmark["href"]
        elif source["type"] == "section":
            bookmark = self.get_section_bookmarks(source["section_id"])[source["index"]]
            # Convert link to href for bar
            if "link" in bookmark:
                bookmark["href"] = bookmark["link"]
        else:
            raise ValueError(f"Invalid source type: {source['type']}")

        # Delete from source
        if source["type"] == "bar":
            self.delete_bar_bookmark(source["index"])
        else:
            self.delete_section_bookmark(source["section_id"], source["index"])

        # Insert at destination
        try:
            if destination["type"] == "bar":
                # Ensure href is present
                if "link" in bookmark and "href" not in bookmark:
                    bookmark["href"] = bookmark.pop("link")

                # Insert at specific index
                dest_index = destination.get("index", len(self._data["bar"]))
                self._data["bar"].insert(dest_index, bookmark)
            elif destination["type"] == "section":
                # Ensure link is present
                if "href" in bookmark and "link" not in bookmark:
                    bookmark["link"] = bookmark.pop("href")

                if destination["section_id"] not in self._data.get("sections", {}):
                    raise SectionNotFoundError(
                        f"Section '{destination['section_id']}' not found"
                    )

                # Insert at specific index
                dest_index = destination.get(
                    "index",
                    len(self._data["sections"][destination["section_id"]]["bookmarks"]),
                )
                self._data["sections"][destination["section_id"]]["bookmarks"].insert(
                    dest_index, bookmark
                )
            else:
                raise ValueError(f"Invalid destination type: {destination['type']}")

            self._save()
            return deepcopy(bookmark)
        except Exception as e:
            # Rollback: reload from file
            logger.error(f"Failed to move bookmark, reloading: {e}")
            self._load()
            raise

    def export_bookmarks(self) -> dict[str, Any]:
        """Export all bookmarks as a dict."""
        return deepcopy(self._data)

    def import_bookmarks(self, data: dict[str, Any], merge: bool = False) -> None:
        """
        Import bookmarks from a dict.

        Args:
            data: Bookmark data with 'bar' and 'sections'
            merge: If True, merge with existing data; if False, replace
        """
        # Validate structure
        if not isinstance(data, dict):
            raise ValueError("Import data must be a dictionary")

        if "bar" not in data:
            raise ValueError("Import data must contain 'bar' key")

        if not isinstance(data["bar"], list):
            raise ValueError("'bar' must be a list")

        if "sections" in data and not isinstance(data["sections"], dict):
            raise ValueError("'sections' must be a dictionary")

        if merge:
            # Merge sections
            existing_sections = self._data.get("sections", {})
            new_sections = data.get("sections", {})
            for section_id, section_data in new_sections.items():
                if section_id in existing_sections:
                    # Merge bookmarks
                    existing_sections[section_id]["bookmarks"].extend(
                        section_data.get("bookmarks", [])
                    )
                else:
                    existing_sections[section_id] = section_data

            # Append to bar
            self._data["bar"].extend(data["bar"])
        else:
            # Replace
            self._data = {
                "bar": data.get("bar", []),
                "sections": data.get("sections", {}),
            }

        self._save()
