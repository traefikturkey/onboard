import json
import logging
import os
import time
from pathlib import Path
from typing import Any

from app.models.utils import pwd
from app.services.favicon_store import FaviconStore

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class BookmarkBarManager:
    def __init__(self, bookmark_bar_file: str = "configs/bookmarks.json", favicon_store=None):
        self.bookmark_bar_path = Path(pwd.joinpath(bookmark_bar_file))
        # Allow injection for testing
        self.favicon_store = favicon_store or FaviconStore()

        self.last_reload = 0
        self.reload()

    @property
    def bar(self):
        if not self._bar or self.is_modified():
            self.reload()
        return self._bar

    def get_section(self, section_key: str) -> dict[str, Any] | None:
        """Retrieve a bookmark section by its key from the consolidated schema."""
        if not hasattr(self, "_sections"):
            return None
        return self._sections.get(section_key)

    def is_modified(self):
        logger.info(f"Bookmark Bar modified?: {self.mtime > self.last_reload}")
        return self.mtime > self.last_reload

    @property
    def mtime(self):
        return os.path.getmtime(self.bookmark_bar_path)

    def bookmarks_list(self, bookmarks, urls=[]):
        for bookmark in bookmarks:
            if "contents" in bookmark:
                self.bookmarks_list(bookmark["contents"], urls)
            elif "href" in bookmark:
                urls.append(bookmark["href"])
        return urls

    def reload(self):
        logger.debug("Beginning Bookmark Bar reload...")

        try:
            # Read file content first so we can back it up if parsing fails
            with open(self.bookmark_bar_path, "r", encoding="utf-8") as file:
                content = file.read()

            try:
                data = json.loads(content)
                # Consolidated schema requires dict with "bar" key
                if not isinstance(data, dict) or "bar" not in data:
                    raise ValueError(
                        "Invalid bookmarks.json format. Expected consolidated schema "
                        "with 'bar' key. Run scripts/migrate_bookmarks.py to convert "
                        "legacy format."
                    )
                new_bar = data.get("bar", [])
                self._sections = data.get("sections", {})
            except (json.JSONDecodeError, ValueError) as e:
                # Backup the corrupt file for inspection and keep previous bar in memory
                logger.error("Failed to parse bookmark bar JSON: %s", e)
                try:
                    backup_path = f"{self.bookmark_bar_path}.corrupt.{int(time.time())}"
                    with open(backup_path, "w", encoding="utf-8") as bf:
                        bf.write(content)
                    logger.warning(
                        "Backed up corrupt bookmarks file to %s", backup_path
                    )
                except Exception as be:
                    logger.exception("Failed to write corrupt backup file: %s", be)

                if hasattr(self, "_bar") and self._bar:
                    logger.info(
                        "Keeping previous bookmark bar in memory after parse failure."
                    )
                    # Don't update last_reload so is_modified remains True until a valid file is present
                    return
                else:
                    logger.info(
                        "No previous bookmark bar available; falling back to empty list."
                    )
                    new_bar = []
                    self._sections = {}

            # Assign the parsed content and update mtime
            self._bar = new_bar
            self.last_reload = self.mtime

            # Fetch favicons but don't let favicon failures crash the app
            try:
                self.favicon_store.fetch_favicons_from(self.bookmarks_list(self._bar))
            except Exception:
                logger.exception("Failed to fetch favicons during bookmark bar reload")

            logger.debug("Completed Bookmark Bar reload!")

        except FileNotFoundError:
            logger.warning(
                "Bookmark bar file not found at %s; using empty bar",
                self.bookmark_bar_path,
            )
            # Ensure we have a bar to render
            if not hasattr(self, "_bar") or self._bar is None:
                self._bar = []
            if not hasattr(self, "_sections"):
                self._sections = {}
            self.last_reload = 0
        except Exception:
            # Catch-all to prevent reload failures from bubbling up into requests
            logger.exception("Unexpected error while reloading bookmark bar")
            if not hasattr(self, "_bar") or self._bar is None:
                self._bar = []
            if not hasattr(self, "_sections"):
                self._sections = {}
