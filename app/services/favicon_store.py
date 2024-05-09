import os
import re
import sqlite3
import logging
from services.favicon_utils import get_favicon_filename, normalize_domain
from services.favicon_retriever import FaviconRetriever
from models.scheduler import Scheduler
from models.utils import pwd

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class FaviconStore:
  def __init__(self, cache_dir='static/assets/icons', db_path='configs/favicons.db'):
    self.relative_cache_dir = cache_dir

    self.retriever = FaviconRetriever(self, cache_dir)
    self.ip_pattern = re.compile(
      r"^(?:(?:https?://)?(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
      r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(?::\d{1,5})?(?:\/)?$"
    )

    self.db_path = pwd.joinpath(db_path)
    self.initializing_database()

  def icon_path(self, url):
    if not url:
      return None

    favicon_filename = get_favicon_filename(url)
    favicon_relative_path = f"{self.relative_cache_dir}/{favicon_filename}"

    if os.path.exists(favicon_relative_path):
      return f"/{favicon_relative_path}"
    else:
      return None

  def fetch_favicons_from(self, urls):
    self.scheduler.add_job(
      self._process_urls_for_favicons,
      args=[urls],
      id='fetch_favicons',
      name='fetch_favicons',
      misfire_grace_time=None,
      replace_existing=False,
      max_instances=1,
      coalesce=True,
      executor='processpool'
    )

  def _process_urls_for_favicons(self, urls):
    processable_urls = set(filter(lambda url: self.should_processed(url), urls))
    logger.debug(f"============================ {len(processable_urls)} processable urls")
    for url in processable_urls:
      name = f'_get_favicon_({url})'
      self.scheduler.add_job(
        self.retriever.download_favicon,
        args=[url],
        id=name,
        name=name,
        misfire_grace_time=None,
        executor='processpool'
      )

  def should_processed(self, url):
    result = not (
      not url
      or bool(self.ip_pattern.match(url))
      or self.icon_path(url)
      or self.is_domain_processed(url)
    )
    # logger.debug(f"==============================================================")
    # logger.debug(f"should_processed: {url}")
    # logger.debug(f"ip: {bool(self.ip_pattern.match(url))}")
    # logger.debug(f"path: {self.icon_path(url)}")
    # logger.debug(f"processed: {self.is_domain_processed(url)}")
    # logger.debug(f"result: {result}")
    return result

  @property
  def scheduler(self):
    return Scheduler.getScheduler()

  def initializing_database(self):
    try:
      conn = sqlite3.connect(self.db_path)
      c = conn.cursor()
      c.execute('''CREATE TABLE IF NOT EXISTS processed_domains
                         (domain TEXT PRIMARY KEY, reason TEXT)''')
      conn.commit()
      conn.close()
    except Exception as ex:
      logger.error(f"Error initializing database {self.db_path}: {e}")

  def processed_domain_count(self):
    try:
      conn = sqlite3.connect(self.db_path)
      c = conn.cursor()
      c.execute("SELECT COUNT(*) FROM processed_domains")
      result = c.fetchone()
      conn.close()
      return result[0]
    except Exception as ex:
      logger.error(f"Error in get_processed_domain_count_from_db(): {ex}")
      return 0

  def save_processed_domain(self, url, reason='completed'):
    nomalized_domain = normalize_domain(url)
    try:
      conn = sqlite3.connect(self.db_path, check_same_thread=False)
      c = conn.cursor()
      c.execute("INSERT OR REPLACE INTO processed_domains (domain, reason) VALUES (?, ?)", (nomalized_domain, reason))
      conn.commit()
      conn.close()
      logger.info(f"Saved processed domain {nomalized_domain} with reason {reason}")
    except Exception as ex:
      logger.error(f"Error in save_processed_domain({nomalized_domain}): {ex}")

  def is_domain_processed(self, url):
    nomalized_domain = normalize_domain(url)
    try:
      conn = sqlite3.connect(self.db_path)
      c = conn.cursor()
      c.execute("SELECT 1 FROM processed_domains WHERE domain = ?", [nomalized_domain])
      result = c.fetchone()
      conn.close()
      return bool(result)
    except Exception as ex:
      logger.error(f"Error checking is_domain_processed({nomalized_domain}): {ex}")
      return False
