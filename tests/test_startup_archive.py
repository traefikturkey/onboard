import json
from pathlib import Path


def _write_file(path: Path, size_bytes: int):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(b"a" * size_bytes)


def test_constructor_and_default_load_keep_large_active_caches(tmp_path, monkeypatch):
    from app.models.feed_cache import FeedCache

    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.delenv("ONBOARD_DISABLE_SCHEDULER", raising=False)
    cache = tmp_path / "cache"
    cache.mkdir()
    articles = [{"title": "Large article", "description": "x" * (400 * 1024)}]
    active = cache / "active.json"
    active.write_text(json.dumps({"articles": articles}), encoding="utf-8")
    other = cache / "other.json"
    other.write_bytes(active.read_bytes())

    feed_cache = FeedCache("active", working_dir=tmp_path)
    assert feed_cache.load_cache() == articles
    assert active.exists()
    assert other.exists()
    assert not list(cache.glob("archive-*"))


def test_archive_large_jsons(tmp_path, monkeypatch):
    # prepare WORKING_STORAGE cache dir
    work = tmp_path / "workdir"
    cache = work / "cache"
    cache.mkdir(parents=True)

    small = cache / "small.json"
    large = cache / "large.json"

    _write_file(small, 100)  # 100 bytes
    _write_file(large, 400 * 1024)  # 400 KB

    monkeypatch.setenv("WORKING_STORAGE", str(work))

    # Archival remains available only when explicitly requested.
    from app.models.feed_cache import FeedCache

    fc = FeedCache("big-feed", working_dir=work)

    moved = fc.archive_large_jsons(min_size_bytes=300 * 1024)

    # large should be moved to archive dir
    archive_dir = cache / f"archive-{__import__('datetime').date.today().isoformat()}"
    assert (archive_dir / "large.json").exists()
    assert not (cache / "large.json").exists()

    # small should remain
    assert (cache / "small.json").exists()

    # function should return a list containing the moved file
    assert any(p.name == "large.json" for p in moved)
