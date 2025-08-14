import importlib
import sys


def test_startup_uses_working_storage(tmp_path, monkeypatch):
    # point WORKING_STORAGE to a temp dir
    monkeypatch.setenv("WORKING_STORAGE", str(tmp_path / "mywork"))

    # Prevent the scheduler/archive side-effects during test import
    monkeypatch.setenv("ONBOARD_DISABLE_SCHEDULER", "True")

    # reload module to pick up the environment change
    if "app.startup" in sys.modules:
        importlib.reload(sys.modules["app.startup"])
    else:
        import app.startup  # noqa: F401

    from app.startup import Startup

    cache = Startup.get_cache_dir()
    assert cache.exists()
    assert cache == (tmp_path / "mywork" / "cache").resolve()
