from .bookmark import Bookmark
from .utils import from_list
from .widget import Widget


class Bookmarks(Widget):
    def __init__(self, widget):
        super().__init__(widget)
        self.items = from_list(Bookmark.from_dict, widget["bookmarks"], self)

    @staticmethod
    def from_dict(widget: dict) -> "Bookmarks":
        return Bookmarks(widget)
