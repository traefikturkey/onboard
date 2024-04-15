import os
from rss_feed_manager import RssFeedManager
import yaml

class Layout:
	def __init__(self, file_path="configs/layout.yml"):
		pwd = os.path.dirname(os.path.realpath(__file__))
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
	
	def reload(self):
		print("Reloading layout")
		with open(self.file_path, 'r') as file:
			self.contents = yaml.safe_load(file)
		self.mtime = os.path.getmtime(self.file_path)
		
		feed_widgets = []
		for tab in self.tabs:
			for widget in tab['widgets']:
				if widget['type'] == 'feed':
					feed_widgets.append(widget)
  
		print('Initializing feed manager with {} feeds'.format(len(feed_widgets)))
		self.feed_manager.initialize(feed_widgets)
	 
		for tab in self.tabs:
			column_count = tab.get('columns', 1)
			columns = [[] for _ in range(column_count)]
			tab['columns'] = columns
			if not tab['widgets']:
				next
		
			for widget in tab['widgets']:
				widget['summary_enabled'] = widget.get('summary_enabled', True)
				column_index = (widget.get('column', 1) - 1) % column_count
				
				match widget['type']:
					case 'bookmarks':
						widget['articles'] = [{'title': entry['title'], 'link': entry['url']} for entry in widget['bookmarks']]
						columns[column_index].append(widget)
					case 'feed':
						widget['hx-get'] = '/rss/' + widget['name']
						feed = self.feed_manager.load(widget)
						columns[column_index].append(feed)
					case 'docker_events':
						widget['template'] = 'docker_events.html'
						columns[column_index].append(widget)
					case 'docker_containers':
						widget['hx-get'] = '/docker_containers'
						widget['template'] = 'docker_containers.html'
						columns[column_index].append(widget)
					case 'iframe':
						widget['template'] = 'iframe.html'
						columns[column_index].append(widget)
					case _:
						columns[column_index].append(widget)
						pass
		print("========== Layout reloaded")

	def is_modified(self):
		result = os.path.getmtime(self.file_path) > self.mtime
		print("========== Layout modified: " + str(result))
		return result

	def current_tab(self, tab_name):
		current_tab = self.tabs[0] if tab_name is None else next((tab for tab in self.tabs if tab['name'].lower() == tab_name.lower()), self.tabs[0])
		return current_tab

layout = Layout()