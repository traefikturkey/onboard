import calendar
import importlib
import logging
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from email import utils
from email.utils import formatdate
from pathlib import Path

import dateutil
import feedparser
import requests

from app.processors.strip_long_urls import StripLongUrls

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

    def __init__(self, widget, feed_cache=None, scheduler=None) -> None:
        super().__init__(widget, scheduler=scheduler)

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

        # Use FeedCache to centralize cache path & IO (inject for testing)
        self.feed_cache = feed_cache or FeedCache(self.id)
        self.cache_path = self.feed_cache.cache_path

        # load cached article dicts then convert to FeedArticle
        dicts = self.feed_cache.load_cache(archive_on_load=False)
        logger.debug(
            f"Feed.__init__: loaded {len(dicts)} dicts from cache for feed id={self.id} path={self.cache_path}"
        )
        self.items = []
        appended = 0
        for article in dicts:
            try:
                # Parse pub_date defensively; if parsing fails, fall back to now
                raw_pub = article.get("pub_date") or ""
                try:
                    pub_dt = dateutil.parser.parse(str(raw_pub))
                except Exception:
                    # Use module-level datetime and timezone (imported at top)
                    pub_dt = datetime.now(tz=timezone.utc)

                self.items.append(
                    FeedArticle(
                        original_title=str(
                            article.get("original_title") or article.get("title") or ""
                        ),
                        title=str(article.get("title") or ""),
                        link=str(article.get("link") or ""),
                        description=str(article.get("description", "")),
                        pub_date=pub_dt,
                        processed=str(article.get("processed") or ""),
                        parent=self,
                    )
                )
                appended += 1
            except Exception:
                # skip malformed entries
                continue
        logger.debug(
            f"Feed.__init__: appended {appended} articles into self.items for feed id={self.id}"
        )
        metadata = self.feed_cache.metadata
        self._http_metadata = dict(metadata) if isinstance(metadata, dict) else {}
        self._pending_http_metadata = dict(self._http_metadata)
        self._last_updated = None
        checked_at = self._http_metadata.get("last_checked")
        if checked_at:
            try:
                self._last_updated = self._utc(dateutil.parser.parse(checked_at))
            except ValueError, TypeError, OverflowError:
                pass
        if self._last_updated is None and self.cache_path.exists():
            self._last_updated = datetime.fromtimestamp(
                os.path.getmtime(self.cache_path), tz=timezone.utc
            )

        self.start_scheduling()

    @staticmethod
    def _utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @Widget.items.setter
    def items(self, items):
        self._items = items
        self._last_updated = datetime.now(timezone.utc)

    def start_scheduling(self):
        """Register feed work once, after its owning layout is ready."""
        if self.scheduler.running and not getattr(self, "job", None):
            self.job = self.scheduler.add_job(
                self.update,
                "cron",
                name=f"{self.id} - {self.name} - cron",
                hour="*",
                jitter=30,
                max_instances=1,
                misfire_grace_time=120,
                coalesce=True,
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
                self.job.modify(next_run_time=datetime.now(timezone.utc))
            except Exception:
                logger.exception(f"Failed to modify job for feed {self.name}")
        else:
            logger.warning(f"Feed: {self.name} does not have a scheduled job!")

    @property
    def needs_update(self):
        force_update = os.getenv("ONBOARD_FEED_FORCE_UPDATE", "").lower() in (
            "true",
            "1",
            "yes",
        )
        # if there is no last_updated time, or if it's more 10 minutes ago, then force an update
        return (
            force_update
            or self.last_updated is None
            or self._utc(self.last_updated)
            < datetime.now(timezone.utc) - timedelta(minutes=10)
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
        try:
            articles = self.download(self.feed_url)
            metadata = dict(self._pending_http_metadata)
            metadata["last_checked"] = datetime.now(timezone.utc).isoformat()
            if articles is None:  # HTTP 304: retain articles without reprocessing.
                self.feed_cache.save_articles(
                    self._serialize_articles(self.items), metadata=metadata
                )
            else:
                articles = self.save_articles(articles, metadata=metadata)
                self._items = articles
            self._http_metadata = metadata
            self._last_updated = self._utc(
                dateutil.parser.parse(metadata["last_checked"])
            )
        except requests.RequestException, ValueError, OSError:
            logger.exception("Failed to update feed %s", self.feed_url)

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
            # Prefer FeedCache for file-store injection without moving active caches.
            try:
                dicts = self.feed_cache.load_cache(archive_on_load=False)
                articles = _to_feed_articles(dicts)
            except Exception:
                articles = []

        articles.sort(key=lambda a: a.pub_date, reverse=True)
        articles = self.processors(articles)

        return articles

    def download(self, feed_url: str) -> list[FeedArticle] | None:
        headers = {}
        if self._http_metadata.get("etag"):
            headers["If-None-Match"] = self._http_metadata["etag"]
        if self._http_metadata.get("last_modified"):
            headers["If-Modified-Since"] = self._http_metadata["last_modified"]
        # Bound both connection establishment and waits for response data.
        with requests.get(feed_url, headers=headers, timeout=(5, 30)) as response:
            response.raise_for_status()
            metadata = dict(self._http_metadata) if response.status_code == 304 else {}
            for header, key in (("ETag", "etag"), ("Last-Modified", "last_modified")):
                if response.headers.get(header):
                    metadata[key] = response.headers[header]
            if response.status_code == 304:
                self._pending_http_metadata = metadata
                return None
            parser_headers = {
                key.lower(): value for key, value in response.headers.items()
            }
            parser_headers.setdefault("content-location", response.url or feed_url)
            feed = feedparser.parse(response.content, response_headers=parser_headers)

        articles = []

        # Log parse problems but continue processing entries when possible
        if getattr(feed, "bozo", False):
            logger.warning(
                "RSS parse issue for %s: %s",
                feed_url,
                getattr(feed, "bozo_exception", "unknown"),
            )

        if not getattr(feed, "entries", []) and (
            getattr(feed, "bozo", False) or not getattr(feed, "version", None)
        ):
            raise ValueError(f"Response from {feed_url} is not a valid feed")

        for entry in getattr(feed, "entries", []) or []:
            # Prefer structured times when available to avoid dateutil parse errors
            pub_date: datetime
            try:
                tm = entry.get("published_parsed") or entry.get("updated_parsed")
                if tm is not None:
                    # Convert struct_time to aware UTC datetime
                    pub_date = datetime.fromtimestamp(
                        calendar.timegm(tm), tz=timezone.utc
                    )
                else:
                    raw = entry.get("published") or entry.get("updated") or formatdate()
                    # email.utils handles many RSS/Atom datetime formats
                    try:
                        from email.utils import parsedate_to_datetime

                        parsed = parsedate_to_datetime(str(raw))
                        pub_date = (
                            parsed
                            if parsed is not None
                            else datetime.now(tz=timezone.utc)
                        )
                    except Exception:
                        # Last resort: dateutil with fallback to now
                        pub_date = dateutil.parser.parse(str(raw))
            except Exception:
                pub_date = datetime.now(tz=timezone.utc)

            description = str(entry.get("description", ""))

            try:
                articles.append(
                    FeedArticle(
                        original_title=str(entry.get("title", "")),
                        title=str(entry.get("title", "")),
                        link=str(entry.get("link", "")),
                        description=description,
                        pub_date=pub_date,
                        processed="",
                        parent=self,
                    )
                )
            except Exception:
                # Skip malformed entries defensively
                continue

        self._pending_http_metadata = metadata
        return articles

    def process(self):
        self.items = self.processors(self.items)

    def processors(self, articles: list[FeedArticle]) -> list[FeedArticle]:
        # Always apply conservative global processors first (unless the feed already lists them)
        try:
            configured = [p.get("processor") for p in self.widget.get("process", [])]
        except Exception:
            configured = []

        try:
            if "strip_long_urls" not in configured:
                articles = StripLongUrls().process(articles)
        except Exception:
            logger.exception(
                "Global processor StripLongUrls failed; continuing without it"
            )

        if "process" in self.widget:
            for processor in self.widget["process"]:
                processor_name = processor["processor"]
                # Check both app/processors and root processors directories
                app_processor_path = pwd.joinpath("processors", processor_name + ".py")
                root_processor_path = pwd.parent.joinpath(
                    "processors", processor_name + ".py"
                )

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
                    except ImportError, AttributeError:
                        processor_instance = NoOpFeedProcessor()
                elif root_processor_path.exists():
                    try:
                        module = importlib.import_module(f"processors.{processor_name}")
                        processor_class = getattr(
                            module,
                            "".join(word.title() for word in processor_name.split("_")),
                        )
                        processor_instance = processor_class()
                    except ImportError, AttributeError:
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

    def save_articles(self, articles: list[FeedArticle], metadata: dict | None = None):
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

        self.feed_cache.save_articles(
            self._serialize_articles(all_articles), metadata=metadata
        )
        logger.info(
            f"Saved {len(all_articles)} articles for {self.name} to cache file {self.cache_path}"
        )
        return all_articles

    @staticmethod
    def _serialize_articles(articles: list[FeedArticle]) -> list[dict]:
        return [
            {
                "original_title": article.original_title,
                "title": article.title,
                "link": article.link,
                "description": article.description,
                "pub_date": utils.format_datetime(article.pub_date),
                "id": article.id,
                "processed": article.processed,
            }
            for article in articles
        ]
