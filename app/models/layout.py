
import logging
import os
import yaml
from models.bookmark import Bookmark
from models.row import Row
from models.column import Column
from models.scheduler import Scheduler
from models.tab import Tab
from models.feed import Feed
from models.utils import from_list, pwd

logger = logging.getLogger(__name__)

class Layout:
	id: str = 'layout'
	headers: list[Bookmark] = []
	tabs: list[Tab] = []
 
	def __init__(self, config_file: str = "configs/layout.yml"):
		logger.setLevel(logging.DEBUG)
		self.config_path = pwd.joinpath(config_file) 
		self.reload()
	
 
	def stop_scheduler(self):
		Scheduler.shutdown()


	def is_modified(self):
		modified = self.mtime > self.last_reload
		logger.debug(f"Layout modified: {modified} mtime: {self.mtime} last_reload: {self.last_reload}")
		return modified
	
 
	@property
	def mtime(self):
		return os.path.getmtime(self.config_path)
 
 
	def reload(self):
		Scheduler.clear_jobs()
	
		with open(self.config_path, 'r') as file:
			content = yaml.safe_load(file)
			self.tabs = from_list(Tab.from_dict, content.get('tabs', []))
			self.headers = from_list(Bookmark.from_dict, content.get('headers', []), self)

		self.last_reload = self.mtime
		self.feed_hash = {}
		logging.debug("Layout reloaded!")



	def tab(self, name: str) -> Tab:
		if name is None:
			return self.tabs[0]
		
		return next((tab for tab in self.tabs if tab.name.lower() == name.lower()), self.tabs[0])
 
 
	def get_feeds(self, columns: Column) -> list[Feed]:
		feeds = []
		if columns.rows:
			for row in columns.rows:
				for column in row.columns:
					feeds += self.process_rows(column)
		 
		for widget in columns.widgets:
			if widget.type == 'feed':
				feeds.append(widget)
		
		return feeds
		 
	 
	def get_feed(self, feed_id: str) -> Feed:
		if not self.feed_hash:
			feeds = []
			for tab in self.tabs:
				for row in tab.rows:
					for column in row.columns:
						feeds += self.get_feeds(column)
							
			for feed in feeds:
				self.feed_hash[feed.id] = feed
	
		return self.feed_hash[feed_id]

	def find_link(self, row: Row, widget_id: str, link_id: str) -> str:
		for column in row.columns:
			if column.rows:
				for row in column.rows:
					link = self.find_link(column, widget_id, link_id)
					if link:
						return link
			else:
				for widget in column.widgets:
					if widget.id == widget_id:
						for item in widget:
							if item.id == link_id:
								return item.link

		return None 	
						
		
	# TODO: Brute force is best force
	def get_link(self, feed_id: str, link_id: str):
		if feed_id == self.id:
			for header in self.headers:
				if header.id == link_id:
					return header.link

		for tab in self.tabs:
			for row in tab.rows:
				link = self.find_link(row, feed_id, link_id)
				if link:
						return link
    
		return None

	
layout = Layout()