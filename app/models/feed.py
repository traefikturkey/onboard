import time
import dateutil
import feedparser
import importlib
import json
import os
import re

from datetime import datetime, timedelta, timezone
from email.utils import formatdate
from email import utils
from functools import cached_property
from pathlib import Path

from models.noop_feed_processor import NoOpFeedProcessor
from models.feed_article import FeedArticle
from models.scheduler_widget import SchedulerWidget
from models.utils import calculate_sha1_hash, to_snake_case, pwd


class Feed(SchedulerWidget):
	feed_url: str
	id: str = None
	display_limit: int = 10
	summary_enabled: bool = True
	hx_get: str = None
	
	def __init__(self, widget) -> None:
		super().__init__(widget)
		self._last_updated = None
	
		self.feed_url = widget['feed_url']
		self.display_limit = widget.get('display_limit', 10)
		self.summary_enabled = widget.get('summary_enabled', True)
		self.hx_get = f"/feed/{self.id}"
	
		if not self.cache_path.parent.exists():
			self.cache_path.parent.mkdir(parents=True, exist_ok=True)
	
		items = self.load_cache(self.cache_path)
		self.items = items[:self.display_limit]
		if self.items:
			self._last_updated = datetime.fromtimestamp(os.path.getmtime(self.cache_path))
	
		self.scheduler.add_job(self.update, 'cron', name=self.id, hour='*', jitter=20)

		if self.needs_update or self.old_cache_path.exists():
			# schedule job to run right now
			print(f'[{datetime.now()}] {self.name} scheduled for immediate update now!')
			self.scheduler.add_job(self.update, 'date', run_date=datetime.now())
 
	@property
	def needs_update(self):
		force_update = os.getenv("ONBOARD_FEED_FORCE_UPDATE", "False") == "True"
		# if there is no last_updated time, or if it's more than an hour ago
		return force_update or self._last_updated is None or self._last_updated < datetime.now() - timedelta(hours=1)

	@property
	def old_cache_path(self):
		return self.cache_path.parent.joinpath(f"{to_snake_case(self.name)}.json")

	def __iter__(self):
		for item in self.items:
			yield item
 	
	@cached_property
	def cache_path(self):
		return pwd.joinpath(os.getenv("ONBOARD_FEED_CACHE_DIR", "../cache"), f"{self.id}.json").resolve()
	
	@property
	def feed_url(self) -> str:
		return self._url
	
	@feed_url.setter
	def feed_url(self, url: str):
		self._url = url
		self.id = calculate_sha1_hash(url)

	def update(self):
		articles = self.download(self.feed_url)
		articles = self.save_articles(articles)
		self.items = articles[:self.display_limit]
		self._last_updated = datetime.now()
		print(f"[{datetime.now()}] Updated {self.name}")

	def load_cache(self, cache_path: Path) -> list[FeedArticle]:
		articles = []
		if cache_path.exists():
			with open(cache_path, 'r') as f:
				json_articles = json.load(f)['articles']
			
				for article in json_articles:
					articles.append(
						FeedArticle(
							original_title = article.get('original_title', article['title']),
							title = article['title'],
							link = article['link'],
							description = article['description'],
							pub_date = dateutil.parser.parse(article['pub_date']) 
						)
					)
			print(f"[{datetime.now()}] Loaded {len(articles)} cached articles for {self.name} : file {self.cache_path}")
		else:
			print(f"[{datetime.now()}] Failed to load cached articles for {self.name} : file {self.cache_path} does not exist")
		
		articles.sort(key=lambda a: a.pub_date, reverse=True)
		return articles


	def apply_filters(self, articles: list[FeedArticle]) -> list[FeedArticle]:
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
		
		return articles

	def download(self, feed_url: str) -> list[FeedArticle]:
		articles = []
		feed = feedparser.parse(feed_url)
		for entry in feed.entries:
			pub_date = dateutil.parser.parse(entry.get('published', entry.get('updated', formatdate())))
			articles.append(
				FeedArticle(
					original_title = entry.title,
					title = entry.title,
					link = entry.link,
					description = entry.description,
					pub_date = pub_date
				)
			)
			
		return articles 

	def processors(self, articles: list[FeedArticle]) -> list[FeedArticle]:
		if 'process' in self.widget:
			for processor in self.widget['process']:
				processor_name = processor['processor']
				processor_path = pwd.joinpath("processors", processor_name + ".py")
				if processor_path.exists():
					module = importlib.import_module(f"processors.{processor_name}")
					processor_class = getattr(module, ''.join(word.title() for word in processor_name.split('_')))
					processor_instance = processor_class()
				else:
					processor_instance = NoOpFeedProcessor()

				articles = processor_instance.process(articles)
		
		return articles

	def save_articles(self, articles: list[FeedArticle]):
		#print(f"[{datetime.now()}] Starting cache save for {self.name} to file {self.cache_path}")
	
		if self.old_cache_path.exists():
			articles += self.load_cache(self.old_cache_path)
			self.old_cache_path.unlink()
	
		# load all existing articles from the json file, and add the new ones
		# then apply the filters
		all_articles = self.load_cache(self.cache_path) + articles
	
		# using article.id remove duplicates from articles
		all_articles = list(dict((article.id, article) for article in all_articles).values())

		all_articles = self.apply_filters(all_articles)	
 
		all_articles = self.processors(all_articles)
		
		# sort articles in place by pub_date newest to oldest
		all_articles.sort(key=lambda a: a.pub_date, reverse=True)
		
		
		data = {
			'name': self.name,
			'link': self.link,
			'articles': [
				{
					'original_title': article.original_title,
					'title': article.title,
					'link': article.link,
					'description': article.description,
					'pub_date': utils.format_datetime(article.pub_date),
					'id': article.id
				} for article in all_articles
			]
		}
		with open(self.cache_path, 'w') as f:
			json.dump(data, f, indent=2)
	 
		print(f"[{datetime.now()}] Saved {len(all_articles)} articles for {self.name} to cache file {self.cache_path}")
		return all_articles
	