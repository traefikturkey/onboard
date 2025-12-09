import logging
import os
import shutil
from pathlib import Path

import yaml

from app.services.bookmark_bar_manager import BookmarkBarManager
from app.services.bookmarks_migrator import BookmarksMigrator

from .apscheduler import Scheduler
from .bookmark import Bookmark
from .column import Column
from .feed import Feed
from .row import Row
from .tab import Tab
from .utils import from_list, pwd

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Layout:
    id: str = "layout"
    tabs: list[Tab] = []
    headers: list[Bookmark] = []

    def __init__(self, config_file: str = "configs/layout.yml"):
        # Ensure default config files (including layout.yml) exist before
        # resolving the config path and loading the layout.
        try:
            _copy_default_to_configs()
        except Exception:
            # Don't raise on startup copy failure; let reload surface issues
            logger.exception("Failed to copy default configs")

        # Auto-migrate legacy inline bookmarks to bookmarks_section format
        try:
            _auto_migrate_bookmarks()
        except Exception:
            logger.exception("Failed to auto-migrate bookmarks")

        self.config_path = pwd.joinpath(config_file)

        self.bar_manager = BookmarkBarManager()

        self.reload()

    @property
    def bookmark_bar(self):
        return self.bar_manager.bar

    @property
    def favicon_store(self):
        return self.bar_manager.favicon_store

    def stop_scheduler(self):
        Scheduler.shutdown()

    def favicon_path(self, url):
        return self.favicon_store.icon_path(url)

    def is_modified(self):
        modified = self.mtime > self.last_reload
        logger.info(f"Layout modified?: {modified}")
        return modified

    @property
    def mtime(self):
        return os.path.getmtime(self.config_path)

    def bookmarks_list(self, bookmarks, urls=[]):
        for bookmark in bookmarks:
            if "contents" in bookmark:
                self.bookmarks_list(bookmark["contents"], urls)
            elif "href" in bookmark:
                urls.append(bookmark["href"])
        return urls

    def reload(self):
        logger.debug("Beginning Layout reload...")
        Scheduler.clear_jobs()
        content = self._load_layout_from_file()
        self.tabs = [
            Tab.from_dict(t, bookmark_manager=self.bar_manager)
            for t in content.get("tabs", [])
        ]
        self.headers = from_list(Bookmark.from_dict, content.get("headers", []), self)

        self.last_reload = self.mtime
        self.feed_hash = {}

        logger.debug("Completed Layout reload!")

    def _load_layout_from_file(self) -> dict:
        """Helper to load YAML layout content from the configured path.

        Extracted to a separate method so tests can patch it easily.
        Returns an empty dict on any read/parse error.
        """
        try:
            with open(self.config_path, "r") as file:
                content = yaml.safe_load(file) or {}
                # Return raw content. Keep Tab.from_dict strict and let tests
                # update fixtures to match canonical `tab` key when needed.
                return content
        except Exception:
            logger.exception("Failed to read layout config; returning empty content")
            return {}

    # NOTE: Legacy normalization removed. Parsing is strict and callers/tests
    # should provide canonical keys (e.g., `tab`).

    def tab(self, name: str) -> Tab:
        if name is None:
            return self.tabs[0]

        return next(
            (tab for tab in self.tabs if tab.name.lower() == name.lower()), self.tabs[0]
        )

    def get_feeds(self, columns: Column) -> list[Feed]:
        feeds = []
        if columns.rows:
            for row in columns.rows:
                for column in row.columns:
                    feeds += self.get_feeds(column)

        for widget in columns.widgets:
            if widget.type == "feed":
                feeds.append(widget)

        return feeds

    def process_rows(self, column: Column) -> list[Feed]:
        """Recursively walk a column's rows/columns/widgets and return any feed widgets.

        This helper complements get_feeds where nested structures can contain rows
        that in turn contain more columns. It returns a flat list of Feed objects.
        """
        feeds: list[Feed] = []
        # If this column contains nested rows, descend into them
        if getattr(column, "rows", None):
            for row in column.rows:
                for col in row.columns:
                    feeds += self.process_rows(col)

        # Collect feed widgets from this column
        for widget in getattr(column, "widgets", []):
            if getattr(widget, "type", None) == "feed":
                feeds.append(widget)

        return feeds

    def get_feed(self, feed_id: str) -> Feed:
        if not self.feed_hash:
            feeds = []
            for tab in self.tabs:
                for row in tab.rows:
                    for column in row.columns:
                        feeds += self.get_feeds(column)

            for feed in feeds:
                self.feed_hash[feed.id] = feed

        return self.feed_hash[feed_id]

    def refresh_feeds(self, feed_id: str):
        feed = self.get_feed(feed_id)
        feed.refresh()

    from typing import Optional

    def find_link(self, row: Row, widget_id: str, link_id: str) -> Optional[str]:
        for column in row.columns:
            if column.rows:
                for row in column.rows:
                    link = self.find_link(row, widget_id, link_id)
                    if link:
                        return link
            else:
                for widget in column.widgets:
                    if widget.id == widget_id:
                        for item in widget:
                            if item.id == link_id:
                                return item.link

        return None

    # TODO: Brute force is best force

    def get_link(self, feed_id: str, link_id: str):
        if feed_id == self.id:
            for header in self.headers:
                if header.id == link_id:
                    return header.link

        for tab in self.tabs:
            for row in tab.rows:
                link = self.find_link(row, feed_id, link_id)
                if link:
                    return link

        return None


def _copy_default_to_configs():
    """Private helper: copy files from `defaults/` into `configs/` when missing.

    Kept private to this module because it's only used by Layout initialization.
    """
    default_dir = os.path.join(pwd, "defaults")
    config_dir = os.path.join(pwd, "configs")

    Path(config_dir).mkdir(parents=True, exist_ok=True)

    files_copied = 0
    for file in os.listdir(default_dir):
        if file not in os.listdir(config_dir):
            src = os.path.join(default_dir, file)
            dst = os.path.join(config_dir, file)
            shutil.copy2(src, dst)
            files_copied += 1
            logger.info(
                f"File {file} copied successfully from {default_dir} to {config_dir}."
            )

    if files_copied == 0:
        logger.info(f"No files copied from {default_dir} to {config_dir}.")


def _auto_migrate_bookmarks():
    """Auto-migrate legacy inline bookmarks to bookmarks_section format.

    Runs the BookmarksMigrator against the app directory to convert any
    layout.yml files that still have inline 'bookmarks' arrays to use
    'bookmarks_section' references instead.
    """
    migrator = BookmarksMigrator(app_root=pwd)
    report = migrator.migrate()

    if report.changed:
        for directory_report in report.directories:
            if directory_report.created or directory_report.updated:
                logger.info(
                    "Auto-migrated bookmarks in %s: %s -> %s",
                    directory_report.scope,
                    directory_report.old_bookmarks,
                    directory_report.new_bookmarks,
                )
    else:
        logger.debug("No bookmark migration needed.")
