import json
import logging
import os

from app.models.utils import pwd
from services.favicon_store import FaviconStore

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class BookmarkBarManager:
    def __init__(self, bookmark_bar_file: str = "configs/bookmarks_bar.json"):
        self.bookmark_bar_path = pwd.joinpath(bookmark_bar_file)

        self.favicon_store = FaviconStore()

        self.last_reload = 0
        self.reload()

    @property
    def bar(self):
        if not self._bar or self.is_modified():
            self.reload()
        return self._bar

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
        with open(self.bookmark_bar_path, "r") as file:
            self._bar = json.load(file)
        self.last_reload = self.mtime

        self.favicon_store.fetch_favicons_from(self.bookmarks_list(self._bar))

        logger.debug("Completed Bookmark Bar reload!")
