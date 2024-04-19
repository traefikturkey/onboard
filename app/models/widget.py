import os
from pathlib import Path
from models.scheduler import Scheduler
from models.exceptions import IDException
from models.utils import calculate_sha1_hash, pwd


class Widget:
	widget: dict
	display_limit: int = None
	template: str = 'widget.html'
	items: list = []
	link: str = None
	id: str = None
	
	def __init__(self, widget):
		self.widget = widget

		self.display_limit = widget.get('display_limit', None)	
 
		class_name = Path(os.path.basename(__file__)).stem
		template_path = pwd.joinpath('templates', class_name + '.html')
		if not self.template and template_path.exists():
			self.template = template_path.name
	 
		if not self.id:
			if 'link' in self.widget:
				id = self.widget['link']
			elif 'name' in self.widget:
				id = self.widget['name']
			else:
				raise IDException("No ID found for widget") 
			self.id = calculate_sha1_hash(id)
	 
	@property 
	def loaded(self):
		return self.items and len(self.items) > 0

	@property
	def scheduler(self):
		return Scheduler.getScheduler()
	 
	def __iter__(self):
		for item in self.items:
			yield item
	
	@property
	def display_items(self):
		if self.display_limit:
			for item in self.items[:self.display_limit]:
				yield item
		else:
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
	def display_header(self):
		return self.widget.get('display_header', True)

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
	