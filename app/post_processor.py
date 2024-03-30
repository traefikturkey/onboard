import html
import importlib
import re
import os

from bs4 import BeautifulSoup

class NoOpClass:
	def process(self, data):
		return data

class PostProcessor:
	def __init__(self):
		self.loaded_classes = {}
		self.pwd = os.path.dirname(os.path.abspath(__file__))

	def to_snake_case(self, input_string):
		# Replace non-alphanumeric characters and apostrophes with spaces and split the string into words
		words = re.findall(r"[a-zA-Z0-9]+(?:'[a-zA-Z0-9]+)?", input_string)

		# Remove apostrophes from the words
		words = [word.replace("'", "") for word in words]

		# Convert words to lowercase and join them with underscores
		snake_case_string = '_'.join(word.lower() for word in words)

		return snake_case_string

	def process(self, widget):
		# if 'processed' in widget and widget['processed'] and not bool(os.environ.get('FLASK_DEBUG')):
		# 	print (f"Widget {widget['name']} already processed.")
		# 	return widget

		self.normalize(widget)

		# Check if the class has already been loaded
		class_name = self.to_snake_case(widget['name'])
		if class_name in self.loaded_classes:
			instance = self.loaded_classes[class_name]
		else:
			# Construct file path to the "processors" subdirectory
			file_path = os.path.join(self.pwd, "processors", class_name + ".py")
			if os.path.exists(file_path):
				module = importlib.import_module(f"processors.{class_name}")
				cls = getattr(module, ''.join(word.title() for word in class_name.split('_')))
				instance = cls()
			else:
				instance = NoOpClass()

			self.loaded_classes[class_name] = instance

		# Call process() method of the instance with the provided data
		widget = instance.process(widget)
		widget['processed'] = True
		return widget

	def normalize(self, widget):
		for article in widget['articles']:
			article['title'] = article['original_title'].strip()
			article['title'] = re.sub(r'\s+', ' ', article['title'])

			if not article['original_summary']:
				continue
			else:
				article['summary'] = article['original_summary']

			article['summary'] = article['summary'].replace('\n', ' ').replace('\r', ' ').strip()
			article['summary'] = BeautifulSoup(html.unescape(article['summary']), 'lxml').text
			# strip [...] from the end of the summary
			article['summary'] = re.sub(r'\[[\.+|…\]].*$', '', article['summary'])

			if article['summary'] == article['title']:
				article['summary'] = None
			elif (article['title'] in article['summary'] and len(article['title'])/len(article['summary']) > 0.64):
				article['title'] = article['summary']
				article['summary'] = None
			elif (article['summary'] in article['title']):
				article['summary'] = article['title']
				article['title'] = None

# Instantiate loader when the module is imported
post_processor = PostProcessor()
