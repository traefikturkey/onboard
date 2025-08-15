import importlib
import logging
import os
from collections import defaultdict
from datetime import datetime, timedelta
from email import utils
from email.utils import formatdate
from pathlib import Path

import dateutil
import feedparser

from .feed_article import FeedArticle
from .feed_cache import FeedCache
from .noop_feed_processor import NoOpFeedProcessor
from .utils import calculate_sha1_hash, pwd
from .widget import Widget

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Feed(Widget):
    summary_enabled: bool = True
    from typing import Optional

    hx_get: Optional[str] = None

    def __init__(self, widget) -> None:
        super().__init__(widget)

        self.feed_url = widget["feed_url"]
        self.display_limit = widget.get("display_limit", 10)
        self.summary_enabled = widget.get("summary_enabled", True)
        self.hx_get = f"/feed/{self.id}"

        self._filters = []
        if "filters" in widget:
            for filter_type in self.widget["filters"]:
                for filter in self.widget["filters"][filter_type]:
                    for attribute in filter:
                        filter_text = filter[attribute]
                        self._filters.append(
                            {
                                "type": filter_type,
                                "text": filter_text,
                                "attribute": attribute,
                            }
                        )

        # Use FeedCache to centralize cache path & IO
        self.feed_cache = FeedCache(self.id)
        self.cache_path = self.feed_cache.cache_path

        # load cached article dicts then convert to FeedArticle
        dicts = self.feed_cache.load_cache(archive_on_load=False)
        self.items = []
        for article in dicts:
            try:
                self.items.append(
                    FeedArticle(
                        original_title=str(
                            article.get("original_title") or article.get("title") or ""
                        ),
                        title=str(article.get("title") or ""),
                        link=str(article.get("link") or ""),
                        description=str(article.get("description", "")),
                        pub_date=dateutil.parser.parse(
                            str(article.get("pub_date") or "")
                        ),
                        processed=str(article.get("processed") or ""),
                        parent=self,
                    )
                )
            except Exception:
                # skip malformed entries
                continue
        if self.items:
            self._last_updated = datetime.fromtimestamp(
                os.path.getmtime(self.cache_path)
            )
        else:
            self._last_updated = None

        if self.scheduler.running:
            self.job = self.scheduler.add_job(
                self.update,
                "cron",
                name=f"{self.id} - {self.name} - cron",
                hour="*",
                jitter=30,
                max_instances=1,
            )
            logger.debug(
                f"Feed: {self.name} cron job for scheduled with job id: {self.job.id}"
            )

            if self.needs_update:
                self.refresh()

    def refresh(self):
        # Be defensive: some Feed instances may not have a 'job' attribute
        if hasattr(self, "job") and self.job:
            logging.debug(f"Feed: {self.name} scheduled for immediate update now!")
            try:
                self.job.modify(next_run_time=datetime.now())
            except Exception:
                logger.exception(f"Failed to modify job for feed {self.name}")
        else:
            logger.warning(f"Feed: {self.name} does not have a scheduled job!")

    @property
    def needs_update(self):
        force_update = bool(os.getenv("ONBOARD_FEED_FORCE_UPDATE", "False"))
        # if there is no last_updated time, or if it's more 10 minutes ago, then force an update
        return (
            force_update
            or self.last_updated is None
            or self.last_updated < datetime.now() - timedelta(minutes=10)
        )

    @property
    def filters(self):
        return self._filters

    @property
    def feed_url(self) -> str:
        return self._url

    @feed_url.setter
    def feed_url(self, url: str):
        self._url = url
        self.id = calculate_sha1_hash(url)

    def update(self):
        articles = self.download(self.feed_url)
        self.items = self.save_articles(articles)

    def load_cache(self, cache_path: Path | None = None) -> list[FeedArticle]:
        """Load cached articles as FeedArticle objects.

        If `cache_path` is provided, read that file (legacy behavior).
        Otherwise, use the injected `FeedCache` to load the cache for this feed.
        """
        articles: list[FeedArticle] = []

        def _to_feed_articles(json_articles):
            out = []
            for article in json_articles:
                try:
                    out.append(
                        FeedArticle(
                            original_title=article.get(
                                "original_title", article.get("title")
                            ),
                            title=article.get("title"),
                            link=article.get("link"),
                            description=article.get("description", ""),
                            pub_date=dateutil.parser.parse(article.get("pub_date")),
                            processed=article.get("processed", None),
                            parent=self,
                        )
                    )
                except Exception:
                    # skip malformed entries
                    continue
            return out

        if cache_path is not None:
            # legacy path-based loader (kept for backward compatibility)
            try:
                payload = self.feed_cache.file_store.read_json(cache_path)
                json_articles = (
                    payload.get("articles", []) if isinstance(payload, dict) else []
                )
                articles = _to_feed_articles(json_articles)
            except Exception as ex:
                logging.error(
                    f"Failed to load cached articles for {self.name} : {str(ex)}"
                )
        else:
            # prefer FeedCache which handles archive-on-load and file-store injection
            try:
                dicts = self.feed_cache.load_cache(archive_on_load=False)
                articles = _to_feed_articles(dicts)
            except Exception:
                articles = []

        articles.sort(key=lambda a: a.pub_date, reverse=True)
        return articles

    def download(self, feed_url: str) -> list[FeedArticle]:
        articles = []
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            # coerce potentially unexpected types to str for parsing and FeedArticle
            published = entry.get("published", entry.get("updated", formatdate()))
            pub_date = dateutil.parser.parse(str(published))

            if "description" in entry:
                description = str(entry.description)
            else:
                description = ""

            articles.append(
                FeedArticle(
                    original_title=str(entry.title),
                    title=str(entry.title),
                    link=str(entry.link),
                    description=description,
                    pub_date=pub_date,
                    processed="",
                    parent=self,
                )
            )

        return articles

    def process(self):
        self.items = self.processors(self.items)

    def processors(self, articles: list[FeedArticle]) -> list[FeedArticle]:
        if "process" in self.widget:
            for processor in self.widget["process"]:
                processor_name = processor["processor"]
                # Check both app/processors and root processors directories
                app_processor_path = pwd.joinpath(
                    "app", "processors", processor_name + ".py"
                )
                root_processor_path = pwd.joinpath("processors", processor_name + ".py")

                processor_instance = None
                if app_processor_path.exists():
                    try:
                        module = importlib.import_module(
                            f"app.processors.{processor_name}"
                        )
                        processor_class = getattr(
                            module,
                            "".join(word.title() for word in processor_name.split("_")),
                        )
                        processor_instance = processor_class()
                    except (ImportError, AttributeError):
                        processor_instance = NoOpFeedProcessor()
                elif root_processor_path.exists():
                    try:
                        module = importlib.import_module(f"processors.{processor_name}")
                        processor_class = getattr(
                            module,
                            "".join(word.title() for word in processor_name.split("_")),
                        )
                        processor_instance = processor_class()
                    except (ImportError, AttributeError):
                        processor_instance = NoOpFeedProcessor()
                else:
                    processor_instance = NoOpFeedProcessor()

                articles = processor_instance.process(articles)

        return articles

    def remove_duplicate_articles(self, articles):
        # Filters a list of objects and returns a new list with objects where 'removed' is False.
        articles = list(filter(lambda obj: not obj.removed, articles))

        # Create a dictionary to group articles by their ID
        article_dict = defaultdict(list)
        for article in articles:
            article_dict[article.id].append(article)

        # Filter the articles, keeping the one with 'processed' set if it exists
        return [
            next(
                (a for a in articles_list if a.processed is not None), articles_list[0]
            )
            for articles_list in article_dict.values()
        ]

    def save_articles(self, articles: list[FeedArticle]):
        # load all existing articles from the json file, and add the new ones
        # then apply the filters
        # Get existing articles as FeedArticle objects
        existing = self.items or []
        all_articles = existing + articles

        # using article.id remove duplicates from articles
        all_articles = self.remove_duplicate_articles(all_articles)

        all_articles = self.processors(all_articles)

        # sort articles in place by pub_date newest to oldest
        all_articles.sort(key=lambda a: a.pub_date, reverse=True)

        # Persist using FeedCache (save serializable dicts)
        serializable = [
            {
                "original_title": article.original_title,
                "title": article.title,
                "link": article.link,
                "description": article.description,
                "pub_date": utils.format_datetime(article.pub_date),
                "id": article.id,
                "processed": article.processed,
            }
            for article in all_articles
        ]

        self.feed_cache.save_articles(serializable)
        logger.info(
            f"Saved {len(all_articles)} articles for {self.name} to cache file {self.cache_path}"
        )
        return all_articles
