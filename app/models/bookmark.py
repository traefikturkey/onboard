from .presentation import BookmarkPresentation, favicon_url
from .widget_item import WidgetItem

LEGACY_HEADER_FAVICONS = {
    "Gmail": "/static/img/gmail.ico",
    "Docs": "/static/img/docs.ico",
    "Photos": "/static/img/photos.ico",
    "Maps": "/static/img/maps.ico",
    "Amazon": "/static/img/amazon.ico",
    "eBay": "/static/img/ebay.ico",
    "Youtube": "/static/img/youtube.ico",
}


class Bookmark(WidgetItem):
    @staticmethod
    def from_dict(*args) -> "Bookmark":
        # Accept either (dict, parent) or ((dict, parent),)
        if len(args) == 1 and isinstance(args[0], tuple) and len(args[0]) == 2:
            dictionary, parent = args[0]
        elif len(args) == 2:
            dictionary, parent = args
        else:
            raise TypeError("from_dict expects (dict, parent) or ((dict, parent),)")
        name = dictionary.get("name")
        link = dictionary.get("link")
        bookmark = Bookmark(name, link, parent)
        presentation = BookmarkPresentation.model_validate(dictionary)
        bookmark.contents = dictionary.get("contents", [])
        bookmark.favicon = presentation.favicon
        bookmark.bookmarks_section = presentation.bookmarks_section
        bookmark.multi_column = presentation.multiColumn
        bookmark.hover_delay_ms = presentation.hover_delay_ms
        bookmark.open_in_new_tab = presentation.openInNewTab
        return bookmark

    from .widget import Widget

    def __init__(self, name: str, link: str, parent: Widget) -> None:
        super().__init__(name, link, parent)
        self._contents: list[dict] = []
        self.favicon: str | None = None
        self.bookmarks_section: str | None = None
        self.multi_column: int = 2
        self.hover_delay_ms: int = 2000
        self.open_in_new_tab: bool = True

    @property
    def contents(self) -> list[dict]:
        if self.bookmarks_section:
            section = self.parent.bar_manager.get_section(self.bookmarks_section)
            return section.get("bookmarks", []) if section else []
        return self._contents

    @contents.setter
    def contents(self, value: list[dict]):
        self._contents = value

    @property
    def favicon_url(self) -> str | None:
        return favicon_url(self.favicon)

    @property
    def header_favicon(self) -> str | None:
        return self.favicon_url or LEGACY_HEADER_FAVICONS.get(self.name)
