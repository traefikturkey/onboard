from dataclasses import dataclass
import html
import re
import warnings
import unidecode
import datetime

from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
from models.utils import calculate_sha1_hash
from url_normalize import url_normalize
from w3lib.url import url_query_cleaner


warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

class FeedArticle:
	original_title: str
	title: str
	description: str
	pub_date: datetime
	link: str
	feed: 'Feed'
	summary: str = None
	id: str = None
	removed: bool = False
	processed: str = None
 
	def __init__(self, original_title: str, title: str, link: str, description: str, pub_date: datetime, processed: str, feed: 'Feed'):
		self.original_title = unidecode.unidecode(original_title)
		self.original_title = re.sub(r'\s+', ' ', self.original_title).strip()
		self.title = title
		self.link = link
		self.description = description
		self.pub_date = pub_date
		self.processed = processed
		self.feed = feed
  
	
		if not self.title:
			self.title = self.original_title
	 
		summary = self.description.replace('\n', ' ').replace('\r', ' ').strip()
		summary = BeautifulSoup(html.unescape(summary), 'lxml').text
		summary = re.sub(r'\[[\.+|…\]].*$', '', summary)

		if summary == self.original_title or summary in self.original_title:
			self.summary = None
		elif (self.original_title in summary and len(self.original_title)/len(summary) > 0.64):
			self.title = summary
			self.summary = None
		else:
			self.summary = summary
	 
		for filter in self.feed.filters:
			if not hasattr(self, filter['attribute']):
				next
			match filter['type']:
				case 'remove':
					if re.search(filter['text'], getattr(self, filter['attribute']), re.IGNORECASE):
						self.removed = True
				case 'strip':
					pattern = re.compile(filter['text'])
					result = re.sub(pattern, '', getattr(self, filter['attribute']))
					setattr(self, filter['attribute'], result)
				case _:
					pass
		

	@property
	def link(self):
		return self._link



	@link.setter
	def link(self, url: str):
		cleaned_url = url_normalize(url)
		cleaned_url = url_query_cleaner(
			cleaned_url, parameterlist=['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content'], remove=True
		)
		self._link = cleaned_url
		self.id = calculate_sha1_hash(self._link)
