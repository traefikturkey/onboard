import logging
import os
import re
from services.favicon_utils import get_favicon_filename, normalize_domain
import requests
from bs4 import BeautifulSoup
from models.utils import pwd
from urllib.parse import urljoin

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class FaviconRetriever:
  def __init__(self, favicon_store, cache_dir: str):
    self.cache_dir = pwd.joinpath(cache_dir)
    self.cache_dir.mkdir(parents=True, exist_ok=True)
    self.request_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    self.favicon_store = favicon_store

  def make_request(self, url):
    return requests.get(url, headers=self.request_headers, allow_redirects=True)

  def favicon_path(self, url):
    favicon_filename = get_favicon_filename(url)
    return os.path.join(self.cache_dir, favicon_filename)

  def find_favicon_url(self, url):
    normalized_domain = normalize_domain(url)
    for try_url in [url, normalized_domain]:
      try:
        response = self.make_request(try_url)
        if response.status_code == 200:
          soup = BeautifulSoup(response.text, 'html.parser')
          icon_link = soup.find('link', rel=['icon', 'shortcut icon'])
          if icon_link:
            icon_url = icon_link['href']
            if not icon_url.startswith('http'):
              icon_url = urljoin(url, icon_url)
            return icon_url
      except Exception as ex:
        logger.error(f"Error: find_favicon_url({try_url}): {ex}")

    # if we made it here we have not found a favicon url
    # lets check google

    icon_url = f'http://www.google.com/s2/favicons?domain={normalized_domain}'
    response = self.make_request(icon_url)
    if response.status_code == 200 and response.headers.get('Content-Type', '').startswith('image'):
      with open(self.favicon_path(normalized_domain), 'wb') as file:
        file.write(response.content)
      self.favicon_store.save_processed_domain(normalized_domain, reason='found in google')

    return None

  def download_favicon(self, url):
    logger.debug(f"download_favicon({url}) called")
    icon_url = self.find_favicon_url(url)
    if not icon_url:
      logger.debug(f"Could not download_favicon({url}) no icon url found!")
      return

    normalized_domain = normalize_domain(icon_url)
    favicon_path = self.favicon_path(normalized_domain)

    try:
      response = self.make_request(icon_url)
      if response.status_code == 200 and response.headers.get('content-type', '').lower().startswith('image/'):
        with open(favicon_path, 'wb') as file:
          file.write(response.content)
        self.favicon_store.save_processed_domain(normalized_domain, reason='success')
      else:
        self.favicon_store.save_processed_domain(
          normalized_domain,
          reason=f'response_code: {response.status_code} content-type: {response.headers.get("content-type", "")}'
        )
    except Exception as ex:
      self.favicon_store.save_processed_domain(normalized_domain, reason=f'{ex}')
