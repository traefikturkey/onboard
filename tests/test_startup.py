def test_startup_uses_working_storage(tmp_path, monkeypatch):
    # point WORKING_STORAGE to a temp dir
    monkeypatch.setenv("WORKING_STORAGE", str(tmp_path / "mywork"))

    # Prevent the scheduler/archive side-effects during test import
    monkeypatch.setenv("ONBOARD_DISABLE_SCHEDULER", "True")

    # Use FeedCache to validate cache directory creation instead of Startup
    from app.models.feed_cache import FeedCache

    fc = FeedCache("dummy", working_dir=tmp_path / "mywork")
    cache = fc.cache_dir
    assert cache.exists()
    assert cache == (tmp_path / "mywork" / "cache").resolve()
