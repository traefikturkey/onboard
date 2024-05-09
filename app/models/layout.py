import json
import logging
import os
import yaml
from services.favicon_store import FaviconStore
from models.bookmark import Bookmark
from models.row import Row
from models.column import Column
from models.scheduler import Scheduler
from models.tab import Tab
from models.feed import Feed
from models.utils import from_list, pwd

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Layout:
  id: str = 'layout'
  tabs: list[Tab] = []
  headers: list[Bookmark] = []
  bookmark_bar: list[dict] = []

  def __init__(self, config_file: str = "configs/layout.yml", bookmarks_bar_file: str = "configs/bookmarks_bar.json"):
    self.config_path = pwd.joinpath(config_file)
    self.bookmark_bar_path = pwd.joinpath(bookmarks_bar_file)

    try:
      if not os.path.exists(pwd.joinpath(self.bookmark_bar_path)):
        with open(pwd.joinpath(self.bookmark_bar_path), 'w', encoding='utf-8') as f:
          json.dump([], f)
    except Exception as ex:
      logger.error(f"Error: {ex} creating empty bookmark bar file at {self.bookmark_bar_path}")

    self.favicon_store = FaviconStore()
    self.reload()

  def load_bookmarks(self):
    try:
      with open(pwd.joinpath(self.bookmark_bar_path), 'r', encoding='utf-8') as f:
        return json.load(f)
    except Exception as ex:
      logger.error(f"Error: Loading bookmark bar file from {self.bookmark_bar_path}", ex)
      return None

  def stop_scheduler(self):
    Scheduler.shutdown()

  def is_modified(self):
    modified = self.mtime > self.last_reload
    logger.info(f"Layout modified?: {modified}")
    return modified

  @property
  def mtime(self):
    return os.path.getmtime(self.config_path)

  def bookmarks_list(self, bookmarks, urls=[]):
    for bookmark in bookmarks:
      if 'contents' in bookmark:
        self.bookmarks_list(bookmark['contents'], urls)
      elif 'href' in bookmark:
        urls.append(bookmark['href'])
    return urls

  def reload(self):
    logger.debug("Beginning Layout reload...")
    Scheduler.clear_jobs()

    with open(self.config_path, 'r') as file:
      content = yaml.safe_load(file)
      self.tabs = from_list(Tab.from_dict, content.get('tabs', []))
      self.headers = from_list(Bookmark.from_dict, content.get('headers', []), self)

    self.last_reload = self.mtime
    self.feed_hash = {}

    self.bookmark_bar = self.load_bookmarks()
    bookmarks = self.bookmarks_list(self.bookmark_bar)
    logger.debug("====== Layout calling fetch favicons!")
    self.favicon_store.fetch_favicons_from(bookmarks)

    logger.debug("Completed Layout reload!")

  def tab(self, name: str) -> Tab:
    if name is None:
      return self.tabs[0]

    return next((tab for tab in self.tabs if tab.name.lower() == name.lower()), self.tabs[0])

  def get_feeds(self, columns: Column) -> list[Feed]:
    feeds = []
    if columns.rows:
      for row in columns.rows:
        for column in row.columns:
          feeds += self.process_rows(column)

    for widget in columns.widgets:
      if widget.type == 'feed':
        feeds.append(widget)

    return feeds

  def get_feed(self, feed_id: str) -> Feed:
    if not self.feed_hash:
      feeds = []
      for tab in self.tabs:
        for row in tab.rows:
          for column in row.columns:
            feeds += self.get_feeds(column)

      for feed in feeds:
        self.feed_hash[feed.id] = feed

    return self.feed_hash[feed_id]

  def refresh_feeds(self, feed_id: str):
    feed = self.get_feed(feed_id)
    feed.refresh()

  def find_link(self, row: Row, widget_id: str, link_id: str) -> str:
    for column in row.columns:
      if column.rows:
        for row in column.rows:
          link = self.find_link(column, widget_id, link_id)
          if link:
            return link
      else:
        for widget in column.widgets:
          if widget.id == widget_id:
            for item in widget:
              if item.id == link_id:
                return item.link

    return None

  # TODO: Brute force is best force

  def get_link(self, feed_id: str, link_id: str):
    if feed_id == self.id:
      for header in self.headers:
        if header.id == link_id:
          return header.link

    for tab in self.tabs:
      for row in tab.rows:
        link = self.find_link(row, feed_id, link_id)
        if link:
          return link

    return None
