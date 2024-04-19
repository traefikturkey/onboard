import functools
import re
from models.utils import calculate_sha1_hash
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

class WidgetItem:
	from models.widget import Widget
	id: str
	name: str
	parent: Widget
	tracking_link: str = None
 

	def __init__(self, name: str, link: str, parent: Widget) -> None:
		# the order here matters
		self.parent = parent
	
		self.name = name
		self.link = link
		

	@property
	def link(self):
		return self._link


	@link.setter
	def link(self, url: str):
		self._link = self.clean_url(url)
		self.id = calculate_sha1_hash(self._link)
		self.tracking_link = f"/redirect/{self.parent.id}/{self.id}"
	
 
	@staticmethod
	def from_dict(dictionary: dict, parent) -> 'WidgetItem':
		name = dictionary.get("name")
		link = dictionary.get("link")

		return WidgetItem(name, link, parent)

	def __str__(self):
		return self.to_dict()

	def to_dict(self) -> dict:
		return {
			'name': self.name,
			'link': self.link
		}
 
	# statically compiled url cleaning patterns
	UTM_PATTERN = re.compile(r'^utm_')
	GA_PATTERN = re.compile(r'^_ga')
	VX_PATTERN = re.compile(r'^vx')
	OTHER_PATTERNS = re.compile(r'^(fbclid|gclid|msclkid|yclid)$')
	
	@staticmethod
	@functools.lru_cache(maxsize=128)
	def clean_url(url):
			# Parse the URL
		parsed_url = urlparse(url)

		# Check if the URL has query parameters
		if parsed_url.query:
			# Remove tracking parameters from the query string
			cleaned_query = [
				(key, value) for key, value in parse_qsl(parsed_url.query)
				if not (WidgetItem.UTM_PATTERN.match(key.lower()) or
								WidgetItem.GA_PATTERN.match(key.lower()) or
								WidgetItem.VX_PATTERN.match(key.lower()) or
								WidgetItem.OTHER_PATTERNS.match(key.lower()))
			]

			# Rebuild the URL with the cleaned query string
			cleaned_url = urlunparse((
				parsed_url.scheme,
				parsed_url.netloc,
				parsed_url.path,
				parsed_url.params,
				urlencode(cleaned_query),
				parsed_url.fragment
			))
		else:
			# If the URL has no query parameters, return the original URL
			cleaned_url = url

		return cleaned_url
