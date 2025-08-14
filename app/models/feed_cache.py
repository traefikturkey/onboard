import logging
import os
from datetime import date
from pathlib import Path
from typing import List, Optional

from .file_store import CacheStore
from .local_file_store import LocalFileStore
from .utils import pwd


def _is_testing_mode() -> bool:
    # Consider testing mode if FLASK_ENV=="testing" or scheduler/archive explicitly disabled
    if os.environ.get("FLASK_ENV", "").lower() == "testing":
        return True
    if os.environ.get("ONBOARD_DISABLE_SCHEDULER", "False").lower() == "true":
        return True
    return False


class FeedCache:
    """Small utility to manage per-feed JSON cache files.

    Responsibilities:
    - compute cache dir (based on working_dir or WORKING_STORAGE)
    - load cache as list[dict]
    - save articles atomically
    - archive large json files in the cache directory
    """

    def __init__(
        self,
        feed_id: str,
        working_dir: Optional[Path] = None,
        file_store: Optional[CacheStore] = None,
    ):
        """Create a FeedCache bound to a feed id.

        If `file_store` is provided, use it for all filesystem operations. If not,
        fall back to the real filesystem via `LocalFileStore` so behavior is
        unchanged.
        """
        self.feed_id = feed_id
        if working_dir is None:
            cache_dir = pwd.joinpath(
                os.getenv("WORKING_STORAGE", ".working"), "cache"
            ).resolve()
        else:
            cache_dir = Path(working_dir).joinpath("cache").resolve()

        # Ensure the directory exists when using the real filesystem
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir: Path = cache_dir
        self.cache_path: Path = cache_dir.joinpath(f"{self.feed_id}.json")
        # Dependency-injected file store; default to LocalFileStore for
        # backwards compatibility.
        self.file_store: CacheStore = file_store or LocalFileStore()

        # Run best-effort startup logic (archive existing large cache files)
        # by default we avoid running this in testing or when the scheduler is disabled.
        if not _is_testing_mode():
            # archive_large_jsons is implemented to never raise; call directly
            self.archive_large_jsons()

    def load_cache(self, archive_on_load: bool = True) -> List[dict]:
        """Return list of article dicts stored in the cache file.

        If archive_on_load is True, run archive_large_jsons first. On error, return []
        """
        try:
            if archive_on_load:
                # archive_large_jsons will handle/log any internal errors and will not
                # raise, so call directly.
                self.archive_large_jsons()

            # Use the file_store to read JSON; implementations are expected to
            # raise on errors which we catch below and return []. If the store
            # does not find the file it may raise or return an empty payload.
            if not self.cache_path.exists():
                return []

            payload = self.file_store.read_json(self.cache_path)
            return payload.get("articles", []) if isinstance(payload, dict) else []
        except Exception:
            # Keep behaviour simple: on any parse/read error return empty list
            return []

    def save_articles(self, articles: List[dict]) -> List[dict]:
        """Atomically write the provided list of article dicts into the feed cache file.

        Returns the list written.
        """
        data = {"name": None, "link": None, "articles": articles}

        # Delegate atomic write to the file store implementation. Implementations
        # should ensure parent directories exist when writing.
        self.file_store.write_json_atomic(self.cache_path, data)
        return articles

    def archive_large_jsons(self, min_size_bytes: int = 300 * 1024) -> List[Path]:
        """Move any .json files in `cache_dir` larger than `min_size_bytes` into an archive folder.

        Returns list of new paths for moved files.
        """
        logger = logging.getLogger(__name__)
        moved: List[Path] = []

        try:
            today = date.today().isoformat()
            archive_dir = self.cache_dir.joinpath(f"archive-{today}")

            # Ensure archive dir exists
            archive_dir.mkdir(parents=True, exist_ok=True)

            for p in list(self.file_store.list_dir(self.cache_dir)):
                if not p.is_file():
                    continue
                if p.suffix != ".json":
                    continue

                # Use a safe stat call; if file disappears, skip it.
                try:
                    size = p.stat().st_size
                except FileNotFoundError:
                    continue

                if size > min_size_bytes:
                    dest = archive_dir.joinpath(p.name)
                    # Delegate move to file_store so tests can simulate moves
                    try:
                        self.file_store.move(p, dest)
                        moved.append(dest)
                    except Exception as e:
                        # Log per-file move errors and continue with other files
                        logger.exception("Failed to move %s to %s: %s", p, dest, e)
                        continue
        except Exception as e:
            # Top-level safety: archive_large_jsons must never raise. Log and return
            logger.exception(
                "archive_large_jsons encountered an unexpected error: %s", e
            )

        return moved
