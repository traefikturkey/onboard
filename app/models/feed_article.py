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

@dataclass
class FeedArticle:
	original_title: str
	title: str
	description: str
	pub_date: datetime
	link: str
	summary: str = None
	id: str = None

	def __post_init__(self):
		self.id = calculate_sha1_hash(self.link)

		self.original_title = unidecode.unidecode(self.original_title)
		self.original_title = re.sub(r'\s+', ' ', self.original_title).strip()
  
		if not self.title:
			self.title = self.original_title
		
		summary = self.description.replace('\n', ' ').replace('\r', ' ').strip()
		summary = BeautifulSoup(html.unescape(summary), 'lxml').text
		summary = re.sub(r'\[[\.+|…\]].*$', '', summary)

		if summary == self.title or summary in self.title:
			self.summary = None
		elif (self.title in summary and len(self.title)/len(summary) > 0.64):
			self.title = summary
			self.summary = None
		else:
			self.summary = summary


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
