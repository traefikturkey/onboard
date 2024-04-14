from bs4 import BeautifulSoup
import feedparser
import html
import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from email.utils import formatdate
from pathlib import Path
from typing import List
from rss_article import RssArticle

@dataclass
class RssFeed:
	widget: dict
	data_dir: Path
	articles: List[RssArticle] = field(default_factory=list)
 
	def __post_init__(self):
		self.title = self.widget['name']
		self.summary_enabled = self.widget.get('summary_enabled', True)
		self.feed_url = self.widget['url']
		self._last_updated = None
		self.update()
	
	def __getattr__(self, key):
		if key in self.widget:
				return self.widget[key]
		else:
				return None
	
	def get(self, key, default=None):
		return self.widget.get(key, default)

	@property
	def json_file(self):
		filename = f"{self.to_snake_case(self.title)}.json"
		json_file = os.path.join(self.data_dir, filename)
		return Path(json_file)

	@property
	def loaded(self):
		return len(self.articles) > 0

	def updated_recently(self):
		return (datetime.now() - self._last_updated).total_seconds() <= 60 * 45

	def update(self):
		if len(self.articles) == 0 and self.json_file.exists():
			with open(self.json_file, 'r') as f:
				data = json.load(f)
				for article in data['articles']:
					self.articles.append(
						RssArticle(
							title = article['title'],
							link = article['link'],
							description = article['description'],
							pub_date = article['pub_date']
						)
					)
			
			self._last_updated = datetime.fromtimestamp(os.path.getmtime(self.json_file))
		elif len(self.articles) == 0:
			self.download()
		
		if self.updated_recently():
			print(f"[{datetime.now()}] Not updating {self.title}, too soon.")
			return
		else:
			self.download()
			print(f"[{datetime.now()}] Updated {self.title}")

	def download(self):
		feed = feedparser.parse(self.feed_url)
		self.title = feed.feed.title
		self.link = feed.feed.link
		for entry in feed.entries:
			self.articles.append(
				RssArticle(
					title = entry.title,
					link = entry.link,
					description = entry.description,
					pub_date = entry.get('published', entry.get('updated', formatdate()))
				)
			)

		self._last_updated = datetime.now()
  
		# sort articles in place by pub_date newest to oldest
		self.articles.sort(key=lambda a: a.pub_date, reverse=True)
  
		# using article.id remove duplicates from self.articles
		self.articles = list(dict((article.id, article) for article in self.articles).values())
		
		data = {
			'title': self.title,
			'link': self.link,
			'articles': [
				{
					'title': article.title,
					'link': article.link,
					'description': article.description,
					'pub_date': article.pub_date,
					'id': article.id
				} for article in self.articles
			]
		}
		with open(self.json_file, 'w') as f:
			json.dump(data, f, indent=2)
	
	@staticmethod
	def to_snake_case(input_string):
		# Replace non-alphanumeric characters and apostrophes with spaces and split the string into words
		words = re.findall(r"[a-zA-Z0-9]+(?:'[a-zA-Z0-9]+)?", input_string)

		# Remove apostrophes from the words
		words = [word.replace("'", "") for word in words]

		# Convert words to lowercase and join them with underscores
		snake_case_string = '_'.join(word.lower() for word in words)

		return snake_case_string