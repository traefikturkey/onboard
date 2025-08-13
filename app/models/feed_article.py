import datetime
import html
import re
import warnings
from typing import Optional, Any

from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
# Removed import to avoid circular import: from models.feed import Feed
from models.utils import normalize_text
from models.widget_item import WidgetItem

warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)


class FeedArticle(WidgetItem):
  original_title: str
  title: str
  description: str
  pub_date: datetime.datetime
  summary: Optional[str] = None
  removed: bool = False
  processed: Optional[str] = None

  def __init__(
      self,
      original_title: str,
      title: str,
      link: str,
      description: str,
      pub_date: datetime.datetime,
      processed: str,
      parent: Any,
  ):
    super().__init__(original_title, link, parent)

    self.original_title = normalize_text(original_title)
    if title:
      self.title = normalize_text(title)
    elif self.name:
      self.title = self.name
    else:
      self.title = self.original_title

    self.description = normalize_text(description)
    self.pub_date = pub_date
    self.processed = processed

    summary = normalize_text(self.description)
    summary = BeautifulSoup(html.unescape(summary), "lxml").text
    summary = re.sub(r"\[[\.+|…\]].*$", "", summary)

    if summary == self.original_title or summary in self.original_title:
      self.summary = None
    elif (
        self.original_title in summary
        and len(self.original_title) / len(summary) > 0.64
    ):
      self.title = summary
      self.summary = None
    else:
      self.summary = summary

    filters = getattr(self.parent, "filters", None)
    if filters is not None:
      for filter in filters:
        if not hasattr(self, filter["attribute"]):
          continue
        match filter["type"]:
          case "remove":
            if re.search(
                filter["text"],
                getattr(self, filter["attribute"]),
                re.IGNORECASE,
            ):
              self.removed = True
          case "strip":
            pattern = re.compile(filter["text"])
            result = re.sub(pattern, "", getattr(self, filter["attribute"]))
            setattr(self, filter["attribute"], result)
          case _:
            pass
