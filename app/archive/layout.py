import os
from pathlib import Path
from rss_feed_manager import RssFeedManager
import yaml
from models.utils import pwd

class Layout:
	def __init__(self, file_path="configs/layout.yml"):
		self.file_path = os.path.join(pwd, file_path)
		self.mtime = os.path.getmtime(self.file_path)
		self.feed_manager = RssFeedManager(self, cache_dir='cache')
		self.reload()
		
	@property
	def tabs(self):
		return self.contents['tabs']

	@property
	def headers(self):
		return self.contents['headers']

	def feed(self, feed_name):
		return self.feed_manager.find(feed_name)

	def columns(self, tab_name):
		current_tab = self.tabs[0] if tab_name is None else next((tab for tab in self.tabs if tab['name'].lower() == tab_name.lower()), self.tabs[0])
		return current_tab['columns']

	def save_articles(self):
		self.feed_manager.save_articles()
 
	def reload(self):
		print("Reloading layout")
		with open(self.file_path, 'r') as file:
			self.contents = yaml.safe_load(file)
		self.mtime = os.path.getmtime(self.file_path)
		
		feed_widgets = []
		for tab in self.tabs:
			for column in tab['columns']:
				for widget in column['widgets']:
					if widget['type'] == 'feed':
						feed_widgets.append(widget)
  
		print('Initializing feed manager with {} feeds'.format(len(feed_widgets)))
		self.feed_manager.initialize(feed_widgets)
	 
		for tab in self.tabs:
			for column in tab['columns']:
				if not column['widgets']:
					next
				for widget in column['widgets']:
					widget['summary_enabled'] = widget.get('summary_enabled', True)
					match widget['type']:
						case 'bookmarks':
							widget['articles'] = [{'title': entry['title'], 'link': entry['url']} for entry in widget['bookmarks']]
						case 'feed':
							widget['hx-get'] = '/rss/' + widget['name']
							self.feed_manager.load(widget)
						case 'docker_containers':
							widget['hx-get'] = '/docker_containers'
							widget['template'] = 'docker_containers.html'
						case _:
							if (template_path := Path('templates', f'{widget["type"]}.html')).exists():
								widget['template'] = template_path.name
				
		print("========== Layout reloaded")

	def is_modified(self):
		result = os.path.getmtime(self.file_path) > self.mtime
		print("========== Layout modified: " + str(result))
		return result

	def current_tab(self, tab_name):
		current_tab = self.tabs[0] if tab_name is None else next((tab for tab in self.tabs if tab['name'].lower() == tab_name.lower()), self.tabs[0])
		return current_tab

layout = Layout()