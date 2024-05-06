from datetime import datetime
import logging
import os
from pathlib import Path
from models.scheduler import Scheduler
from models.exceptions import IDException
from models.utils import calculate_sha1_hash, pwd

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class Widget:
	widget: dict
	display_limit: int = None
	template: str = 'widget.html'
	link: str = None
	id: str = None
	
	def __init__(self, widget):
		self.widget = widget

		self.display_limit = widget.get('display_limit', None)	

		template_path = pwd.joinpath('templates', self.__class__.__name__.lower() + '.html')
		if template_path.exists():
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
	
	@property
	def last_updated(self):
		return self._last_updated or None

	@property
	def items(self):
		return self._items or []
	
	@items.setter
	def items(self, items):
		self._items = items
		self._last_updated = datetime.now()
	 
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
	