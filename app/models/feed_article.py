from dataclasses import dataclass, field
import hashlib
import html
import re
import warnings

from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
from url_normalize import url_normalize
from w3lib.url import url_query_cleaner

warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

@dataclass
class FeedArticle:
	original_title: str
	description: str
	pub_date: str
	link: str
	summary: str = None
	id: str = field(init=False)

	def __post_init__(self):
		self.id = self.calculate_sha1_hash(self.link)
	
		self.title = re.sub(r'\s+', ' ', self.original_title.strip())
		
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
		self.id = self.calculate_sha1_hash(self._link)
	
	@staticmethod
	def calculate_sha1_hash(url: str) -> str:
		sha1 = hashlib.sha1()
		sha1.update(url.encode('utf-8'))
		return sha1.hexdigest()