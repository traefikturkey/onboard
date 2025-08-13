import importlib
import json
import logging
import os
from collections import defaultdict
from datetime import datetime, timedelta
from email import utils
from email.utils import formatdate
from pathlib import Path

import dateutil
import feedparser
from models.feed_article import FeedArticle
from models.noop_feed_processor import NoOpFeedProcessor
from models.utils import calculate_sha1_hash, pwd
from models.widget import Widget

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

        cache_dir = pwd.joinpath(
            os.getenv("WORKING_STORAGE", ".working"), "cache"
        ).resolve()
        if not cache_dir.exists():
            cache_dir.mkdir(parents=True, exist_ok=True)

        self.cache_path = cache_dir.joinpath(f"{self.id}.json")

        self.items = self.load_cache(self.cache_path)
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
        if self.job:
            logging.debug(f"Feed: {self.name} scheduled for immediate update now!")
            self.job.modify(next_run_time=datetime.now())
        else:
            logging.warn(f"Feed: {self.name} does not have a scheduled job!")

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

    def load_cache(self, cache_path: Path) -> list[FeedArticle]:
        articles = []
        if cache_path.exists():
            try:
                with open(cache_path, "r") as f:
                    json_articles = json.load(f)["articles"]

                    for article in json_articles:
                        articles.append(
                            FeedArticle(
                                original_title=article.get(
                                    "original_title", article["title"]
                                ),
                                title=article["title"],
                                link=article["link"],
                                description=article["description"],
                                pub_date=dateutil.parser.parse(article["pub_date"]),
                                processed=article.get("processed", None),
                                parent=self,
                            )
                        )
                logging.debug(
                    f"Loaded {len(articles)} cached articles for {self.name} : file {self.cache_path}"
                )
            except Exception as ex:
                logging.error(
                    f"Failed to load cached articles for {self.name} : {str(ex)}"
                )
        else:
            logging.debug(
                f"Failed to load cached articles for {self.name} : file {self.cache_path} does not exist"
            )

        articles.sort(key=lambda a: a.pub_date, reverse=True)
        return articles

    def download(self, feed_url: str) -> list[FeedArticle]:
        articles = []
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            pub_date = dateutil.parser.parse(
                entry.get("published", entry.get("updated", formatdate()))
            )

            if "description" in entry:
                description = entry.description
            else:
                description = ""

            articles.append(
                FeedArticle(
                    original_title=entry.title,
                    title=entry.title,
                    link=entry.link,
                    description=description,
                    pub_date=pub_date,
                    processed=None,
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
                processor_path = pwd.joinpath("processors", processor_name + ".py")
                if processor_path.exists():
                    module = importlib.import_module(f"processors.{processor_name}")
                    processor_class = getattr(
                        module,
                        "".join(word.title() for word in processor_name.split("_")),
                    )
                    processor_instance = processor_class()
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
        all_articles = self.load_cache(self.cache_path) + articles

        # using article.id remove duplicates from articles
        all_articles = self.remove_duplicate_articles(all_articles)

        all_articles = self.processors(all_articles)

        # sort articles in place by pub_date newest to oldest
        all_articles.sort(key=lambda a: a.pub_date, reverse=True)

        data = {
            "name": self.name,
            "link": self.link,
            "articles": [
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
            ],
        }
        with open(self.cache_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(
            f"Saved {len(all_articles)} articles for {self.name} to cache file {self.cache_path}"
        )
        return all_articles
