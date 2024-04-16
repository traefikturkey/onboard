from dataclasses import field
import hashlib
import os
from pathlib import Path

class Widget:
	widget: dict
	template: str = field(init=False)
	
	def __init__(self, widget):
		self.widget = widget

		template_path = Path(os.path.join('templates', self.__class__.__name__.lower() + '.html'))
		if template_path.exists():
			self.template = template_path.name
		else:
			self.template = 'widget.html'

	@property
	def name(self):
		return self.widget.get('name', '')

	@property
	def type(self):
		return self.widget.get('type', '')

	@property
	def link(self):
		return self.widget.get('link', '')

	@property
	def display_limit(self):
		return self.widget.get('display_limit', 10)

	@staticmethod
	def calculate_sha1_hash(value: str) -> str:
		sha1 = hashlib.sha1()
		sha1.update(value.encode('utf-8'))
		return sha1.hexdigest()

	@staticmethod
	def from_dict(widget: dict) -> 'Widget':
		from models.bookmarks import Bookmarks
		from models.feed import Feed
		match widget['type']:
			case 'feed':
				return Feed(widget)
			case 'bookmarks':
				return Bookmarks(widget)
			case _:
				return Widget(widget)