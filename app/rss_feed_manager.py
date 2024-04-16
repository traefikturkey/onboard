import importlib
from datetime import datetime
from rss_feed import RssFeed
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler

class NoOpClass:
	def process(self, data):
		return data

class RssFeedManager:
  def __init__(self, layout, cache_dir: str = 'data'):
    self.feeds = {}
    self.layout = layout
    self.data_dir = Path(cache_dir)
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
 
  def save_articles(self):
    for feed in self.feeds.values():
      feed.save()
 
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
 
  def process(self):
    if 'processor' in self.widget:
      for processor in self.widget['processor']:
        processor_name = processor['name']
        processor_path = Path(os.path.join("app","processors", processor_name + ".py"))
        if processor_path.exists():
          module = importlib.import_module(f"processors.{processor_name}")
          processor_class = getattr(module, ''.join(word.title() for word in processor_name.split('_')))
          processor_instance = processor_class()
        else:
          processor_instance = NoOpClass()

        articles = processor_instance.process(articles)
