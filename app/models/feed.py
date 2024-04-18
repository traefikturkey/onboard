from collections import defaultdict
import time
import dateutil
import feedparser
import importlib
import json
import logging
import os

from datetime import datetime, timedelta, timezone
from email.utils import formatdate
from email import utils
from functools import cached_property
from pathlib import Path

from models.noop_feed_processor import NoOpFeedProcessor
from models.feed_article import FeedArticle
from models.scheduler_widget import SchedulerWidget
from models.utils import calculate_sha1_hash, to_snake_case, pwd

logger = logging.getLogger(__name__)
class Feed(SchedulerWidget):
	feed_url: str
	id: str = None
	display_limit: int = 10
	summary_enabled: bool = True
	hx_get: str = None
	
	def __init__(self, widget) -> None:
		super().__init__(widget)
		self._last_updated = None
		logger.setLevel(logging.DEBUG)
	
		self.feed_url = widget['feed_url']
		self.display_limit = widget.get('display_limit', 10)
		self.summary_enabled = widget.get('summary_enabled', True)
		self.hx_get = f"/feed/{self.id}"
	
		self._filters = []
		if 'filters' in widget:
			for filter_type in self.widget['filters']:
				for filter in self.widget['filters'][filter_type]:
					for attribute in filter:
						filter_text = filter[attribute]
						self.filters.append({
							"type": filter_type,
							"text": filter_text,
							"attribute": attribute
						})
	
		if not self.cache_path.parent.exists():
			self.cache_path.parent.mkdir(parents=True, exist_ok=True)
	
		items = self.load_cache(self.cache_path)
		self.items = items[:self.display_limit] if items else []
		if self.items:
			self._last_updated = datetime.fromtimestamp(os.path.getmtime(self.cache_path))
	
		logger.debug(f"creating cron job for {self.name}")
		self.scheduler.add_job(self.update, 'cron', name=f'{self.id} - {self.name} - cron', hour='*', jitter=20, max_instances=1)
		
		if self.needs_update or self.old_cache_path.exists() or self.name == "Instapundit":
			# schedule job to run right now
			logging.debug(f"{self.name} scheduled {self.name} for immediate update now!")
			self.scheduler.add_job(self.update, 'date', name=f'{self.id} - {self.name} - update', run_date=datetime.now(), max_instances=1)
		#else:
			# logger.debug(f"scheduled for {self.name} immediate processing now")
			# self.scheduler.add_job(self.process, 'date', name=f'{self.id} - {self.name} - process', run_date=datetime.now(), max_instances=1)
 
	@property
	def needs_update(self):
		force_update = os.getenv("ONBOARD_FEED_FORCE_UPDATE", "False") == "True"
		# if there is no last_updated time, or if it's more than an hour ago
		return force_update or self._last_updated is None or self._last_updated < datetime.now() - timedelta(hours=1)

	@property
	def filters(self):
		return self._filters

	@property
	def old_cache_path(self):
		return self.cache_path.parent.joinpath(f"{to_snake_case(self.name)}.json")

	def __iter__(self):
		for item in self.items:
			yield item
	 
	@property
	def all_items(self):
		for item in self.load_cache(self.cache_path):
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
		logging.debug(f"Updated {self.name}")

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
							pub_date = dateutil.parser.parse(article['pub_date']),
							processed = article.get('processed', None),
							feed = self
						)
					)
			logging.debug(f"Loaded {len(articles)} cached articles for {self.name} : file {self.cache_path}")
		else:
			logging.debug(f"Failed to load cached articles for {self.name} : file {self.cache_path} does not exist")

		articles.sort(key=lambda a: a.pub_date, reverse=True)
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
					pub_date = pub_date,
					processed = None,
					feed = self
				)
			)
			
		return articles 

	def process(self):
		self.items = self.processors(self.items)

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



	def remove_duplicate_articles(self, articles):
			"""
			Removes articles with duplicate IDs, keeping the one with the 'processed' attribute set if it exists.
			
			Parameters:
			articles (list): A list of article objects, each with 'id' and 'processed' properties.
			
			Returns:
			list: A new list with articles where duplicate IDs have been removed, keeping the one with 'processed' set.
			"""
   
			# Filters a list of objects and returns a new list with objects where 'removed' is False.
			articles = list(filter(lambda obj: not obj.removed, articles))
   
			# Create a dictionary to group articles by their ID
			article_dict = defaultdict(list)
			for article in articles:
					article_dict[article.id].append(article)
			
			# Filter the articles, keeping the one with 'processed' set if it exists
			return [
					next((a for a in articles_list if a.processed is not None), articles_list[0])
					for articles_list in article_dict.values()
			]

	def save_articles(self, articles: list[FeedArticle]):

		if self.old_cache_path.exists():
			articles += self.load_cache(self.old_cache_path)
			self.old_cache_path.unlink()
	
		# load all existing articles from the json file, and add the new ones
		# then apply the filters
		all_articles = self.load_cache(self.cache_path) + articles
	
		# using article.id remove duplicates from articles
		all_articles = self.remove_duplicate_articles(all_articles)
 
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
					'id': article.id,
					'processed': article.processed
				} for article in all_articles
			]
		}
		with open(self.cache_path, 'w') as f:
			json.dump(data, f, indent=2)
	 
		logger.debug(f"Saved {len(all_articles)} articles for {self.name} to cache file {self.cache_path}")
		return all_articles
	