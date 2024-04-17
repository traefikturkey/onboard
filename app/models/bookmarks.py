from models.Bookmark import Bookmark
from models.utils import from_list
from models.widget import Widget

class Bookmarks(Widget):
	def __init__(self, widget):
		super().__init__(widget)
		self.items = from_list(Bookmark.from_dict, widget['bookmarks'])
		

	@staticmethod
	def from_dict(widget: dict) -> 'Bookmarks':
		return Bookmarks(widget)
