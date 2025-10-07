import logging

from .bookmark import Bookmark
from .utils import from_list
from .widget import Widget

logger = logging.getLogger(__name__)


class Bookmarks(Widget):
    def __init__(self, widget, bookmark_manager=None):
        super().__init__(widget)

        # Support section references from consolidated bookmarks.json
        if "bookmarks_section" in widget and bookmark_manager:
            section_key = widget["bookmarks_section"]
            section = bookmark_manager.get_section(section_key)
            if section and isinstance(section, dict):
                bookmarks_data = section.get("bookmarks", [])
                # Merge section metadata into widget if not already set
                if "openInNewTab" in section and "openInNewTab" not in widget:
                    widget["openInNewTab"] = section["openInNewTab"]
                logger.debug(
                    "Loaded %d bookmarks from section '%s'",
                    len(bookmarks_data),
                    section_key,
                )
            else:
                logger.warning(
                    "Section '%s' not found; falling back to empty list", section_key
                )
                bookmarks_data = []
        elif "bookmarks" in widget:
            # Legacy inline bookmarks
            bookmarks_data = widget["bookmarks"]
        else:
            bookmarks_data = []

        self.items = from_list(Bookmark.from_dict, bookmarks_data, self)

    @staticmethod
    def from_dict(widget: dict) -> "Bookmarks":
        return Bookmarks(widget)
