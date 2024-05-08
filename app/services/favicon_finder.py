import json
import logging
import os
import re
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from models.utils import pwd
from models.scheduler import Scheduler
from PIL import Image
from io import BytesIO

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class FaviconFinder:
  def __init__(self, cache_dir='static/assets/icons'):
    self.full_cache_path = pwd.joinpath(cache_dir)
    self.full_cache_path.mkdir(parents=True, exist_ok=True)
    self.relative_cache_path = f"/{cache_dir}"
    self.processed_domains = set()
    self.processed_domains_file = pwd.joinpath('configs/processed_domains.json')
    self.load_processed_domains()

  def add_processed_domain(self, url, reason='completed'):
    normalized_domain = self.normalize_domain(url)
    self.processed_domains.append((normalized_domain, reason))
    self.save_processed_domains()

  def save_processed_domains(self):
    try:
      with open(self.processed_domains_file, 'w') as f:
        json.dump(list(self.processed_domains), f, ensure_ascii=True, indent=2)
    except Exception as ex:
      logger.error(f"Error saving processed domains to disk: {ex}")

  def load_processed_domains(self):
    try:
      if os.path.exists(self.processed_domains_file):
        with open(self.processed_domains_file, 'r') as f:
          self.processed_domains = json.load(f)
    except Exception as ex:
      logger.error(f"Error loading processed domains from disk: {ex}")

  @property
  def scheduler(self):
    return Scheduler.getScheduler()

  def normalize_domain(self, url):
    parsed_url = urlparse(url)
    domain_parts = parsed_url.netloc.split('.')
    if domain_parts[0].startswith("www"):
      domain_parts.pop(0)
    return '.'.join(domain_parts)

  def make_request(self, url):
    headers = {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}
    response = requests.get(url, headers=headers, allow_redirects=True)
    return response

  def favicon_exists(self, url):
    if not url:
      return False
    try:
      normalized_domain = self.normalize_domain(url)
      favicon_filename = self.get_favicon_filename(normalized_domain)
      favicon_path = os.path.join(self.full_cache_path, favicon_filename)
      if os.path.exists(favicon_path):
        return f"{self.relative_cache_path}/{favicon_filename}"
      return None
    except Exception as ex:
      logger.error(f"Error checking if favicon exists for {url}: {ex}")
      return None

  def get_favicon_filename(self, domain):
    return domain + '.favicon.ico'

  def is_ip_address(self, url):
    ip_pattern = re.compile(
        r"^(?:(?:https?://)?(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
        r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(?::\d{1,5})?(?:\/)?$"
    )
    return bool(ip_pattern.match(url))

  def is_domain_processed(self, url):
    normalized_domain = self.normalize_domain(url)
    domains = [domain for domain, _ in self.processed_domains]
    return (
      normalized_domain in domains
      or self.is_ip_address(url)
      or self.favicon_exists(url)
      or 'trivantis' in normalized_domain
      or not url
    )

  def get_base(self, url):
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    return base_url

  def fetch_from_iterator(self, urls):
    for url in urls:
      if not self.is_domain_processed(url):
        self.add_processed_domain(url)
        self.scheduler.add_job(
          self._get_favicon,
          args=[url],
          misfire_grace_time=None,
          executor='processpool'
        )

  def _get_favicon(self, url):
    normalized_domain = self.normalize_domain(url)
    favicon_filename = self.get_favicon_filename(normalized_domain)
    favicon_path = os.path.join(self.full_cache_path, favicon_filename)

    if os.path.exists(favicon_path):
      return

    icon_url = self.find_favicon_url(url)

    if not icon_url:
      # If favicon URL is not found for the original URL, try the base URL
      base_url = self.get_base(url)
      icon_url = self.find_favicon_url(base_url)

    if icon_url:
      self.download_favicon(icon_url)
    else:
      logger.warn(f'Favicon not found for {normalized_domain}')
      self.add_processed_domain(normalized_domain, reason='not found')

  def find_favicon_url(self, url):
    try:
      response = self.make_request(url)
      if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        icon_link = soup.find('link', rel=['icon', 'shortcut icon'])
        if icon_link:
          icon_url = icon_link['href']
          if not icon_url.startswith('http'):
            icon_url = urljoin(url, icon_url)
          return icon_url
        else:
          icon_url = f'http://www.google.com/s2/favicons?domain={self.normalize_domain(url)}'
          response = self.make_request(icon_url)
          if response.status_code == 200 and response.headers.get('Content-Type', '').startswith('image'):
            return icon_url
          return None
      else:
        return None
    except Exception as ex:
      logger.error(f'Error finding favicon with url: {url}: {ex}')
      self.add_processed_domain(self.normalize_domain(url), reason=f'Error downloading favicon: {ex}')
      return None

  def download_favicon(self, icon_url):
    if icon_url.startswith('http://www.google.com/s2/favicons?domain='):
      # strip 'http://www.google.com/s2/favicons?domain=' from the URL
      normalized_domain = icon_url[len('http://www.google.com/s2/favicons?domain='):]
    else:
      normalized_domain = self.normalize_domain(icon_url)
    favicon_filename = self.get_favicon_filename(normalized_domain)
    favicon_path = os.path.join(self.full_cache_path, favicon_filename)

    try:
      response = self.make_request(icon_url)
      if response.status_code == 200:
        content_type = response.headers.get('content-type', '').lower()
        if content_type.startswith('image/'):

          with open(favicon_path, 'wb') as file:
            file.write(response.content)
          logger.debug(f'Favicon for {normalized_domain} downloaded and saved as {favicon_path}')
        else:
          logger.warn(f'The downloaded file from {icon_url} is not a valid image')
          self.add_processed_domain(normalized_domain, reason='not an image')
      else:
        logger.warn(f'Failed to download the favicon for {self.get_base(icon_url)}')
        self.add_processed_domain(normalized_domain, reason='not an image')
    except Exception as ex:
      logger.error(f'Error downloading favicon for {normalized_domain} with url: {icon_url}: {ex}')
      self.add_processed_domain(normalized_domain, reason=f'Error downloading favicon: {ex}')
