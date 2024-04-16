from dataclasses import field
from models.feed_article import FeedArticle
from models.widget import Widget

class Feed(Widget):
  feed_url: str
  id: str = field(init=False)
  summary_enabled: bool = field(init=False)
  articles: list[FeedArticle] = field(default_factory=list)
  
  def __init__(self, widget):
    self.feed_url = widget['feed_url']
    self.summary_enabled = widget.get('summary_enabled', True)
    super().__init__(widget)
    
  @property
  def feed_url(self):
    return self._url
  
  @feed_url.setter
  def feed_url(self, url: str):
    self._url = url
    self.id = Widget.calculate_sha1_hash(url)
