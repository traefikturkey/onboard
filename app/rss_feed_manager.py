from datetime import datetime
from rss_feed import RssFeed
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler

class RssFeedManager:
	def __init__(self, layout, data_dir: str = 'data'):
		self.feeds = {}
		self.layout = layout
		self.data_dir = Path(data_dir)
		self.data_dir.mkdir(parents=True, exist_ok=True)
		self.scheduler = BackgroundScheduler()
	 
	def initialize(self, feed_widgets: list):
		self.scheduler.remove_all_jobs()

		for widget in feed_widgets:
			feed = self.load(widget)
			self.scheduler.add_job(feed.update, 'cron', hour='*', jitter=20)
		
		if not self.scheduler.running:
			print('Starting scheduler...')
			self.scheduler.start()
   
		print('feed_manager initialized.')
 
	def find(self, widget_name: str) -> RssFeed:
		if widget_name in self.feeds:
			return self.feeds[widget_name]
		else:
			return None
 
	def load(self, widget: dict) -> RssFeed:
		# check if widget is dict
		if isinstance(widget, dict):
			widget_name = widget['name']
		else:
			widget_name = widget
			widget = self.layout.widget(widget_name)
   
		if widget_name in self.feeds:
			return self.feeds[widget_name]
		else:
			self.feeds[widget['name']] = RssFeed(widget, self.data_dir)
			return self.feeds[widget['name']]
