import logging
import os
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from models.utils import pwd
from models.scheduler import Scheduler

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class FaviconFinder:
  def __init__(self, cache_dir='static/assets/icons'):
    self.full_cache_path = pwd.joinpath(cache_dir)
    self.full_cache_path.mkdir(parents=True, exist_ok=True)
    self.relative_cache_path = f"/{cache_dir}"

  def favicon_exists(self, url):
    if not url:
      return False
    favicon_filename = self.get_favicon_filename(url)
    favicon_path = os.path.join(self.full_cache_path, favicon_filename)
    return os.path.exists(favicon_path)

  def favicon_relative_path(self, url):
    return f"{self.relative_cache_path}/{self.get_favicon_filename(url)}"

  def get_favicon_filename(self, url):
    domain_parts = urlparse(url).netloc.split('.')[-2:]
    return '.'.join(domain_parts) + '.favicon.ico'

  @property
  def scheduler(self):
    return Scheduler.getScheduler()

  def fetch_from_iterator(self, urls):
    for url in urls:
      self.scheduler.add_job(self._get_favicon, args=[url], misfire_grace_time=None, executor='processpool')

  def _get_favicon(self, url):
    favicon_filename = self.get_favicon_filename(url)
    favicon_path = os.path.join(self.full_cache_path, favicon_filename)

    if not os.path.exists(favicon_path):
      icon_url = self.find_favicon_url(url)

      if not icon_url:
        # If favicon URL is not found for the original URL, try the base URL
        base_url = self.get_base(url)
        icon_url = self.find_favicon_url(base_url)

      if icon_url:
        self.download_favicon(url, icon_url)
      else:
        logger.warn(f'Favicon not found for {url} or {self.get_base(url)}')

  def get_base(self, url):
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    return base_url

  def find_favicon_url(self, url):
    try:
      response = requests.get(url)
      if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        icon_link = soup.find('link', rel=['icon', 'shortcut icon'])
        if icon_link:
          icon_url = icon_link['href']
          if not icon_url.startswith('http'):
            icon_url = urljoin(url, icon_url)
          return icon_url
        else:
          return None
      else:
        return None
    except requests.exceptions.RequestException:
      return None

  def download_favicon(self, url, icon_url):
    try:
      response = requests.get(icon_url)
      if response.status_code == 200:
        favicon_filename = self.get_favicon_filename(url)
        favicon_path = os.path.join(self.full_cache_path, favicon_filename)
        with open(favicon_path, 'wb') as file:
          file.write(response.content)
        logger.debug(f'Favicon for {self.get_base(url)} downloaded and saved as {favicon_path}')
      else:
        logger.warn(f'Failed to download the favicon for {self.get_base(url)}')
    except requests.exceptions.RequestException as ex:
      logger.error(f'An error occurred while downloading the favicon for {self.get_base(url)}', ex)
