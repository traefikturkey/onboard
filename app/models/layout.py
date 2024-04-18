
import logging
import os
from models.scheduler_widget import SchedulerWidget
from models.utils import pwd

import yaml
from models.utils import from_list

class Layout:
	headers: list['Bookmark'] = []
	tabs: list['Tab'] = []
 
	def __init__(self, config_file: str = "configs/layout.yml"):
		self.config_path = pwd.joinpath(config_file) 
		self.reload()
	
	def stop_scheduler(self):
		scheduler = SchedulerWidget.getScheduler()
		if scheduler and scheduler.running:
			scheduler.shutdown()

	def is_modified(self):
		return self.mtime > self.last_reload
	
 
	def reload(self):
		from models.tab import Tab
		from models.Bookmark import Bookmark
		scheduler = SchedulerWidget.getScheduler()
		scheduler.remove_all_jobs()
	
		with open(self.config_path, 'r') as file:
			content = yaml.safe_load(file)
			self.tabs = from_list(Tab.from_dict, content.get('tabs', []))
			self.headers = from_list(Bookmark.from_dict, content.get('headers', []))

		self.last_reload = self.mtime
		self.feed_hash = {}
		logging.debug("Layout reloaded!")


	@property
	def mtime(self):
		return os.path.getmtime(self.config_path)


	def tab(self, name: str) -> 'Tab':
		if name is None:
			return self.tabs[0]
		
		return next((tab for tab in self.tabs if tab.name.lower() == name.lower()), self.tabs[0])
 
 
	def get_feeds(self, columns: 'Column') -> list['Feed']:
		feeds = []
		if columns.has_rows:
			for row in columns.rows:
				for column in row.columns:
					feeds += self.process_rows(column)
		 
		for widget in columns.widgets:
			if widget.type == 'feed':
				feeds.append(widget)
		
		return feeds
		 
	 
	def get_feed(self, feed_id: str) -> 'Feed':
		if not self.feed_hash:
			feeds = []
			for tab in self.tabs:
				for row in tab.rows:
					for column in row.columns:
						feeds += self.get_feeds(column)
							
			for feed in feeds:
				self.feed_hash[feed.id] = feed
	
		return self.feed_hash[feed_id]
	
layout = Layout()