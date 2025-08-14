import json
from pathlib import Path

# The tests follow the FeedCache API defined in the plan:
# FeedCache(feed_id: str, working_dir: Optional[Path] = None)
#   - load_cache(archive_on_load: bool = True) -> list[dict]
#   - save_articles(articles: list) -> list
#   - archive_large_jsons(min_size_bytes: int = 300*1024) -> list[Path]
# These tests are written before the implementation (Phase 1).


def _make_cache_paths(tmp_path: Path, feed_id: str):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{feed_id}.json"
    return cache_dir, cache_path


def test_load_creates_cache_dir_and_returns_empty_when_missing(tmp_path, monkeypatch):
    # Use explicit working_dir so tests don't interact with Startup/scheduler
    from app.models.feed_cache import FeedCache

    working_dir = tmp_path / "workdir"
    assert not working_dir.exists()

    fc = FeedCache("test-feed", working_dir=working_dir)

    # Should not raise, should create cache dir and return empty list
    articles = fc.load_cache(archive_on_load=False)
    assert isinstance(articles, list)
    assert articles == []
    assert fc.cache_dir.exists()


def test_save_and_load_roundtrip(tmp_path):
    from app.models.feed_cache import FeedCache

    working_dir = tmp_path / "workdir2"
    fc = FeedCache("roundtrip-feed", working_dir=working_dir)

    sample = [{"id": "1", "title": "Hello"}, {"id": "2", "title": "Bye"}]
    saved = fc.save_articles(sample)

    # save_articles should return a list (possibly the same list or normalized)
    assert isinstance(saved, list)

    loaded = fc.load_cache(archive_on_load=False)
    # Loaded articles should match what was saved (order may be preserved by implementation)
    assert isinstance(loaded, list)
    # Compare by set of json strings to avoid ordering assumption
    assert {json.dumps(a, sort_keys=True) for a in loaded} == {
        json.dumps(a, sort_keys=True) for a in sample
    }


def test_archive_large_jsons_moves_large_files(tmp_path):
    from app.models.feed_cache import FeedCache

    working_dir = tmp_path / "workdir3"
    fc = FeedCache("big-feed", working_dir=working_dir)

    # Ensure cache_dir exists
    fc.cache_dir.mkdir(parents=True, exist_ok=True)

    # Create a large JSON file (>300KB)
    big_file = fc.cache_dir / "other-large.json"
    data = {"x": "A" * (350 * 1024)}
    with open(big_file, "w", encoding="utf-8") as f:
        json.dump(data, f)

    assert big_file.exists()

    moved = fc.archive_large_jsons(min_size_bytes=300 * 1024)

    # archive_large_jsons should return a list of moved Paths
    assert isinstance(moved, list)
    assert any(p.name == "other-large.json" for p in moved)

    # The original file should no longer be in cache_dir
    assert not big_file.exists()

    # And it should exist inside an archive folder
    archive_dirs = [
        p
        for p in (fc.cache_dir.iterdir())
        if p.is_dir() and p.name.startswith("archive-")
    ]
    assert archive_dirs, "no archive directory created"
    archived_path = archive_dirs[0] / "other-large.json"
    assert archived_path.exists()


def test_load_handles_corrupt_json_gracefully(tmp_path):
    from app.models.feed_cache import FeedCache

    working_dir = tmp_path / "workdir4"
    fc = FeedCache("corrupt-feed", working_dir=working_dir)

    # Create a corrupt JSON file at the expected cache path
    fc.cache_dir.mkdir(parents=True, exist_ok=True)
    with open(fc.cache_path, "w", encoding="utf-8") as f:
        f.write("{ this is not: valid json }")

    # load_cache should handle the parse error and return an empty list (no exception)
    articles = fc.load_cache(archive_on_load=False)
    assert isinstance(articles, list)
    assert articles == []
