
from dataclasses import field
from models.utils import from_list
from models.widget import Widget

class Bookmark:
	name: str
	link: str

	def __init__(self, name: str, link: str) -> None:
		self.name = name
		self.link = link

	@staticmethod
	def from_dict(dictionary: dict) -> 'Bookmark':
		return Bookmark(
			dictionary.get("name"), 
			dictionary.get("link"))

	def to_dict(self) -> dict:
		return {
			'name': self.name,
			'link': self.link
		}

class Bookmarks(Widget):
	bookmarks: list[Bookmark] = field(default_factory=list)
	def __init__(self, widget):
		self.bookmarks = from_list(Bookmark.from_dict, widget['bookmarks'])
		super().__init__(widget)

		@staticmethod
		def from_dict(widget: dict) -> 'Bookmarks':
			return Bookmarks(widget)
