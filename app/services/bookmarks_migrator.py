from __future__ import annotations

import json
import logging
import os
import re
import tempfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class DirectoryReport:
    scope: str
    old_bookmarks: Path
    new_bookmarks: Path
    layout: Path
    created: bool
    updated: bool
    skipped: bool
    reason: str | None = None


@dataclass(slots=True)
class MigrationReport:
    directories: list[DirectoryReport]

    @property
    def changed(self) -> bool:
        return any(report.created or report.updated for report in self.directories)


CURRENT_SCHEMA_VERSION = 2


class BookmarksMigrator:
    """Migrate legacy bookmark configuration into the consolidated schema."""

    def __init__(
        self,
        app_root: Path,
        *,
        layout_filename: str = "layout.yml",
        old_filename: str = "bookmarks_bar.json",
        new_filename: str = "bookmarks.json",
        dry_run: bool = False,
    ) -> None:
        self.app_root = app_root
        self.layout_filename = layout_filename
        self.old_filename = old_filename
        self.new_filename = new_filename
        self.dry_run = dry_run

    def migrate(self) -> MigrationReport:
        directories = []
        for scope in ("defaults", "configs"):
            base_dir = self.app_root / scope
            directories.append(self._migrate_directory(scope, base_dir))
        return MigrationReport(directories)

    def _migrate_directory(self, scope: str, base_dir: Path) -> DirectoryReport:
        old_file = base_dir / self.old_filename
        new_file = base_dir / self.new_filename
        layout_file = base_dir / self.layout_filename

        # Check schema version first - skip if already at current version
        if self._get_layout_schema_version(layout_file) >= CURRENT_SCHEMA_VERSION:
            return DirectoryReport(
                scope=scope,
                old_bookmarks=old_file,
                new_bookmarks=new_file,
                layout=layout_file,
                created=False,
                updated=False,
                skipped=True,
                reason="already at schema version %d" % CURRENT_SCHEMA_VERSION,
            )

        if not old_file.exists():
            return DirectoryReport(
                scope=scope,
                old_bookmarks=old_file,
                new_bookmarks=new_file,
                layout=layout_file,
                created=False,
                updated=False,
                skipped=True,
                reason="missing legacy bookmarks file",
            )

        try:
            bar_data = self._load_json(old_file) or []
        except json.JSONDecodeError as error:
            logger.error(
                "Failed to parse legacy bookmarks file %s", old_file, exc_info=error
            )
            return DirectoryReport(
                scope=scope,
                old_bookmarks=old_file,
                new_bookmarks=new_file,
                layout=layout_file,
                created=False,
                updated=False,
                skipped=True,
                reason="invalid legacy bookmarks JSON",
            )

        sections = self._extract_sections(layout_file)
        payload = {"bar": bar_data, "sections": sections}

        # Check if layout.yml still has inline bookmarks that need migration
        layout_needs_update = self._layout_has_inline_bookmarks(layout_file)

        if new_file.exists() and not layout_needs_update:
            try:
                existing = self._load_json(new_file)
            except json.JSONDecodeError:
                existing = None
            if existing == payload:
                return DirectoryReport(
                    scope=scope,
                    old_bookmarks=old_file,
                    new_bookmarks=new_file,
                    layout=layout_file,
                    created=False,
                    updated=False,
                    skipped=True,
                    reason="already up to date",
                )

        if self.dry_run:
            action = "update" if new_file.exists() else "create"
            logger.info("[dry-run] Would %s %s", action, new_file)
            return DirectoryReport(
                scope=scope,
                old_bookmarks=old_file,
                new_bookmarks=new_file,
                layout=layout_file,
                created=not new_file.exists(),
                updated=new_file.exists(),
                skipped=False,
                reason="dry-run",
            )

        created = not new_file.exists()
        try:
            self._write_json(new_file, payload)
            # Also update layout.yml to use section references instead of inline bookmarks
            if layout_file.exists() and sections:
                self._update_layout_with_sections(layout_file, sections)
            return DirectoryReport(
                scope=scope,
                old_bookmarks=old_file,
                new_bookmarks=new_file,
                layout=layout_file,
                created=created,
                updated=not created,
                skipped=False,
            )
        except OSError as error:
            logger.error(
                "Failed to write consolidated bookmarks file %s",
                new_file,
                exc_info=error,
            )
            return DirectoryReport(
                scope=scope,
                old_bookmarks=old_file,
                new_bookmarks=new_file,
                layout=layout_file,
                created=False,
                updated=False,
                skipped=True,
                reason="write failure",
            )

    def _get_layout_schema_version(self, layout_path: Path) -> int:
        """Get the schema_version from a layout file, defaulting to 1 if not present."""
        if not layout_path.exists():
            return 1

        try:
            with layout_path.open("r", encoding="utf-8") as handle:
                layout = yaml.safe_load(handle) or {}
        except yaml.YAMLError:
            return 1

        return layout.get("schema_version", 1)

    def _layout_has_inline_bookmarks(self, layout_path: Path) -> bool:
        """Check if layout.yml still has inline bookmarks that need migration."""
        if not layout_path.exists():
            return False

        try:
            with layout_path.open("r", encoding="utf-8") as handle:
                layout = yaml.safe_load(handle) or {}
        except yaml.YAMLError:
            return False

        def has_inline(node: Any) -> bool:
            if isinstance(node, dict):
                if node.get("type") == "bookmarks" and "bookmarks" in node:
                    return True
                for value in node.values():
                    if has_inline(value):
                        return True
            elif isinstance(node, list):
                for item in node:
                    if has_inline(item):
                        return True
            return False

        return has_inline(layout)

    def _extract_sections(self, layout_path: Path) -> dict[str, Any]:
        if not layout_path.exists():
            logger.debug("Layout file %s missing; sections will be empty", layout_path)
            return {}

        try:
            with layout_path.open("r", encoding="utf-8") as handle:
                layout = yaml.safe_load(handle) or {}
        except yaml.YAMLError as error:
            logger.error("Failed to parse layout file %s", layout_path, exc_info=error)
            return {}

        sections: dict[str, dict[str, Any]] = {}
        counters: defaultdict[str, int] = defaultdict(int)

        def traverse(node: Any) -> None:
            if isinstance(node, dict):
                if node.get("type") == "bookmarks" and isinstance(
                    node.get("bookmarks"), list
                ):
                    name = str(node.get("name", "Bookmarks"))
                    slug, count = self._unique_slug(name, counters)
                    section = sections.setdefault(
                        slug,
                        {
                            "displayName": self._display_name(name, count),
                            "bookmarks": [],
                        },
                    )
                    bookmarks = node.get("bookmarks", [])
                    for bookmark in bookmarks:
                        entry = self._normalise_bookmark(bookmark)
                        if entry:
                            section["bookmarks"].append(entry)
                for value in node.values():
                    traverse(value)
            elif isinstance(node, list):
                for item in node:
                    traverse(item)

        traverse(layout)
        return sections

    @staticmethod
    def _display_name(name: str, count: int) -> str:
        if count <= 1:
            return name
        return f"{name} ({count})"

    @staticmethod
    def _unique_slug(name: str, counters: defaultdict[str, int]) -> tuple[str, int]:
        base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "section"
        counters[base] += 1
        count = counters[base]
        if count == 1:
            return base, count
        slug = f"{base}-{count}"
        return slug, count

    @staticmethod
    def _normalise_bookmark(bookmark: Any) -> dict[str, Any]:
        if not isinstance(bookmark, dict):
            return {}
        entry: dict[str, Any] = {}
        if "name" in bookmark:
            entry["name"] = bookmark["name"]
        link = bookmark.get("link") or bookmark.get("href")
        if link:
            entry["link"] = link
        if "favicon" in bookmark:
            entry["favicon"] = bookmark["favicon"]
        if "add_date" in bookmark:
            entry["add_date"] = bookmark["add_date"]
        return entry

    def _update_layout_with_sections(
        self, layout_path: Path, sections: dict[str, Any]
    ) -> None:
        """Update layout.yml to replace inline bookmarks with section references."""
        with layout_path.open("r", encoding="utf-8") as handle:
            content = handle.read()
            layout = yaml.safe_load(content) or {}

        counters: defaultdict[str, int] = defaultdict(int)

        def update_widget(node: Any) -> None:
            if isinstance(node, dict):
                if node.get("type") == "bookmarks" and "bookmarks" in node:
                    # Generate the same slug that was used when extracting
                    name = str(node.get("name", "Bookmarks"))
                    slug, _ = self._unique_slug(name, counters)
                    # Replace inline bookmarks with section reference
                    del node["bookmarks"]
                    node["bookmarks_section"] = slug
                for value in node.values():
                    update_widget(value)
            elif isinstance(node, list):
                for item in node:
                    update_widget(item)

        update_widget(layout)

        # Set schema_version to mark as migrated
        layout["schema_version"] = CURRENT_SCHEMA_VERSION

        if not self.dry_run:
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", delete=False, dir=layout_path.parent
            ) as tmp:
                yaml.dump(layout, tmp, default_flow_style=False, allow_unicode=True)
                tmp.flush()
                os.fsync(tmp.fileno())
            os.replace(Path(tmp.name), layout_path)
            logger.info("Updated layout file %s with section references", layout_path)

    @staticmethod
    def _load_json(path: Path) -> Any:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    @staticmethod
    def _write_json(path: Path, payload: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", delete=False, dir=path.parent
        ) as tmp:
            json.dump(payload, tmp, ensure_ascii=False, indent=2)
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(Path(tmp.name), path)
