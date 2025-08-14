import logging
import re

from app.models.scheduler import Scheduler
from app.models.utils import pwd
from services.favicon_utils import (
    base,
    download_favicon,
    favicon_failed_filename,
    favicon_filename,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class FaviconStore:
  def __init__(self, icon_dir="static/assets/icons"):
    self.relative_icon_dir = icon_dir
    self.icon_dir = pwd.joinpath(icon_dir).resolve()
    self.icon_dir.mkdir(parents=True, exist_ok=True)

    self.ip_pattern = re.compile(
        r"^(?:(?:https?://)?(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
        r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(?::\d{1,5})?(?:\/)?$"
    )

  @property
  def scheduler(self):
    return Scheduler.getScheduler()

  from typing import Optional

  def icon_path(self, url) -> Optional[str]:
    if not url:
      return None

    filename = favicon_filename(url)
    favicon_relative_path = f"{self.relative_icon_dir}/{filename}"

    if pwd.joinpath(favicon_relative_path).exists():
      return f"/{favicon_relative_path}"
    else:
      return None

  def favicon_failed(self, url) -> bool:
    favicon_filename = favicon_failed_filename(url)
    return pwd.joinpath(self.relative_icon_dir, favicon_filename).exists()

  def fetch_favicons_from(self, urls):
    base_urls = sorted(set(map(lambda url: base(url), urls)))
    processable_urls = set(
        filter(lambda url: self.should_processed(url), base_urls)
    )
    # logger.debug(f"============================ {len(processable_urls)} processable urls")

    self.scheduler.add_job(
        self._process_urls_for_favicons,
        args=[processable_urls],
        id="fetch_favicons",
        name="fetch_favicons",
        misfire_grace_time=None,
        replace_existing=False,
        max_instances=1,
        coalesce=True,
    )

  def _process_urls_for_favicons(self, urls):
    for url in urls:
      name = f"_get_favicon_({url})"
      self.scheduler.add_job(
          download_favicon,
          args=[url, self.icon_dir],
          id=name,
          name=name,
          misfire_grace_time=None,
          executor="processpool",
      )

  def should_processed(self, url):
    return not (
        not url
        or bool(self.ip_pattern.match(url))
        or self.icon_path(url)
        or self.favicon_failed(url)
    )
