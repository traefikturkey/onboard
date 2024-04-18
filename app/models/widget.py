import os
from pathlib import Path
from models.utils import pwd


class Widget:
	widget: dict
	template: str
	items: list = []
	
	def __init__(self, widget):
		self.widget = widget
		
		template_path = pwd.joinpath('templates', self.__class__.__name__.lower() + '.html')
		if template_path.exists():
			self.template = template_path.name
		else:
			self.template = 'widget.html'
   
	@property 
	def loaded(self):
		return self.items and len(self.items) > 0
	 
	def __iter__(self):
		for item in self.items:
			yield item

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

	def hasattr(self, name):
		return hasattr(self, name) or name in self.widget

	def get(self, key, default=None):
		if hasattr(self, key):
			return getattr(self, key) or default
 
		return self.widget.get(key, default)

	@staticmethod
	def from_dict(widget: dict) -> 'Widget':
		from models.bookmarks import Bookmarks
		from models.iframe import Iframe
		from models.feed import Feed
  
		match widget['type']:
			case 'feed':
				return Feed(widget)
			case 'bookmarks':
				return Bookmarks(widget)
			case 'iframe':
				return Iframe(widget)
			case _:
				return Widget(widget)