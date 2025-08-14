from pathlib import Path


def _write_file(path: Path, size_bytes: int):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(b"a" * size_bytes)


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
    # Prevent scheduler/archive side-effects during test import
    monkeypatch.setenv("ONBOARD_DISABLE_SCHEDULER", "True")

    # Use FeedCache to exercise the archive behavior (Startup is being removed)
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
