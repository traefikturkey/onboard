import json
import os
import shutil
from datetime import date
from pathlib import Path
from typing import List, Optional

from .utils import pwd


class FeedCache:
    """Small utility to manage per-feed JSON cache files.

    Responsibilities:
    - compute cache dir (based on working_dir or WORKING_STORAGE)
    - load cache as list[dict]
    - save articles atomically
    - archive large json files in the cache directory
    """

    def __init__(self, feed_id: str, working_dir: Optional[Path] = None):
        self.feed_id = feed_id
        if working_dir is None:
            cache_dir = pwd.joinpath(
                os.getenv("WORKING_STORAGE", ".working"), "cache"
            ).resolve()
        else:
            cache_dir = Path(working_dir).joinpath("cache").resolve()

        cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir: Path = cache_dir
        self.cache_path: Path = cache_dir.joinpath(f"{self.feed_id}.json")

    def load_cache(self, archive_on_load: bool = True) -> List[dict]:
        """Return list of article dicts stored in the cache file.

        If archive_on_load is True, run archive_large_jsons first. On error, return []
        """
        try:
            if archive_on_load:
                # best-effort
                try:
                    self.archive_large_jsons()
                except Exception:
                    pass

            if not self.cache_path.exists():
                return []

            with open(self.cache_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            return payload.get("articles", []) if isinstance(payload, dict) else []
        except Exception:
            # Keep behaviour simple: on any parse/read error return empty list
            return []

    def save_articles(self, articles: List[dict]) -> List[dict]:
        """Atomically write the provided list of article dicts into the feed cache file.

        Returns the list written.
        """
        data = {"name": None, "link": None, "articles": articles}

        tmp_path = self.cache_path.with_suffix(self.cache_path.suffix + ".tmp")
        # ensure directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        # atomic replace
        os.replace(str(tmp_path), str(self.cache_path))
        return articles

    def archive_large_jsons(self, min_size_bytes: int = 300 * 1024) -> List[Path]:
        """Move any .json files in `cache_dir` larger than `min_size_bytes` into an archive folder.

        Returns list of new paths for moved files.
        """
        moved = []
        today = date.today().isoformat()
        archive_dir = self.cache_dir.joinpath(f"archive-{today}")
        archive_dir.mkdir(parents=True, exist_ok=True)

        for p in list(self.cache_dir.iterdir()):
            if not p.is_file():
                continue
            if p.suffix != ".json":
                continue
            try:
                if p.stat().st_size > min_size_bytes:
                    dest = archive_dir.joinpath(p.name)
                    shutil.move(str(p), str(dest))
                    moved.append(dest)
            except FileNotFoundError:
                continue
        return moved
