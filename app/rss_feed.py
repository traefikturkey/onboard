from itertools import islice
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
	
 
	def __post_init__(self):
		self.title = self.widget['name']
		self.summary_enabled = self.widget.get('summary_enabled', True)
		self.feed_url = self.widget['url']
		self._articles = []
		self._last_updated = None
  
		default_article_display_limit = int(os.environ.get("ONBOARD_DEFAULT_ARTICLE_DISPLAY_LIMIT", 10))
		self.display_limit = self.widget.get('display_limit', default_article_display_limit)
  
		self.update()
		
		
	@property
	def articles(self) -> List[RssArticle]:
		return self._articles

	@articles.setter
	def articles(self, articles:  List[RssArticle]):
		# filter articles
		filtered_articles = self.apply_filters(articles)
		# limit articles to display_limit
		self._articles = [article for article in islice(filtered_articles, self.display_limit)] 
	
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

	@staticmethod
	def load_articles(filename: Path) -> list[RssArticle]:
		articles =[]
		if filename.exists():
			with open(filename, 'r') as f:
				json_articles = json.load(f)['articles']
			
				for article in json_articles:
					articles.append(
						RssArticle(
							original_title = article['title'],
							link = article['link'],
							description = article['description'],
							pub_date = article['pub_date']
						)
					)
		
		return articles

	def apply_filters(self, articles: list[RssArticle]) -> list[RssArticle]:
		# using article.id remove duplicates from articles
		articles = list(dict((article.id, article) for article in articles).values())
	
		if 'filters' in self.widget:
			for article in articles[:]:
				for filter_type in self.widget['filters']:
					for filter in self.widget['filters'][filter_type]:
						for attribute in filter:
							filter_text = filter[attribute]
							if not hasattr(article, attribute):
								next
							match filter_type:
								case 'remove':
									if re.search(filter_text, getattr(article, attribute), re.IGNORECASE):
										articles.remove(article)
								case 'strip':
										pattern = re.compile(filter_text)
										result = re.sub(pattern, '', getattr(article, attribute))
										setattr(article, attribute, result)
								case _:
									pass
			
		# sort articles in place by pub_date newest to oldest
		articles.sort(key=lambda a: a.pub_date, reverse=True)
		
		return articles
	
	@staticmethod
	def download(feed_url: str) -> list[RssArticle]:
		articles = []
		feed = feedparser.parse(feed_url)
		for entry in feed.entries:
			articles.append(
				RssArticle(
					original_title = entry.title,
					link = entry.link,
					description = entry.description,
					pub_date = entry.get('published', entry.get('updated', formatdate()))
				)
			)
			
		return articles
			

	def update(self):
		if len(self.articles) == 0 and self.json_file.exists():
			self.articles = self.load_articles(self.json_file)
			self._last_updated = datetime.fromtimestamp(os.path.getmtime(self.json_file))

		if len(self.articles) == 0 or not self.updated_recently():
			downloaded_articles = self.download(self.feed_url)
			self.articles += downloaded_articles
			self._last_updated = datetime.now()
			self.save_articles(downloaded_articles)
			print(f"[{datetime.now()}] Updated {self.title}")
   
		else:
			print(f"[{datetime.now()}] Not updating {self.title}")

	def save_articles(self, articles: list[RssArticle]):
		# load all existing articles from the json file, and add the new ones
		# then apply the filters
		all_articles = self.load_articles(self.json_file) + articles
		all_articles = self.apply_filters(all_articles)
		
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
				} for article in all_articles
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