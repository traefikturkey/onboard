import json
import os
import time

import pytest

from app.services.bookmark_bar_manager import BookmarkBarManager


class DummyFaviconStore:
    def fetch_favicons_from(self, urls):
        # do nothing, avoids network calls
        return None


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def test_reload_loads_valid_json(tmp_path, monkeypatch):
    file_path = tmp_path / "bookmarks.json"
    # Use consolidated schema with bar + sections
    data = {
        "bar": [{"name": "Test", "href": "https://example.com"}],
        "sections": {"test-section": {"displayName": "Test", "bookmarks": []}},
    }
    write_file(file_path, json.dumps(data))

    # Point pwd.joinpath to our tmp file
    class Pwd:
        def joinpath(self, _):
            return str(file_path)

    monkeypatch.setattr("app.services.bookmark_bar_manager.pwd", Pwd())
    # Replace favicon_store
    monkeypatch.setattr(
        "app.services.bookmark_bar_manager.FaviconStore", lambda: DummyFaviconStore()
    )

    mgr = BookmarkBarManager("bookmarks.json")
    assert isinstance(mgr.bar, list)
    assert mgr.bar[0]["name"] == "Test"
    assert mgr.get_section("test-section") is not None


def test_reload_handles_corrupt_json_and_keeps_previous(tmp_path, monkeypatch):
    file_path = tmp_path / "bookmarks.json"
    # Use consolidated schema
    good = {"bar": [{"name": "Good", "href": "https://good.example"}], "sections": {}}
    write_file(file_path, json.dumps(good))

    class Pwd:
        def joinpath(self, _):
            return str(file_path)

    monkeypatch.setattr("app.services.bookmark_bar_manager.pwd", Pwd())
    monkeypatch.setattr(
        "app.services.bookmark_bar_manager.FaviconStore", lambda: DummyFaviconStore()
    )

    mgr = BookmarkBarManager("bookmarks.json")
    assert mgr.bar[0]["name"] == "Good"

    # Now corrupt the file
    corrupt_content = "{ not valid json...\n"
    write_file(file_path, corrupt_content)

    # Update file mtime so manager sees modification
    os.utime(file_path, None)

    # Call reload explicitly
    mgr.reload()

    # Ensure backup file created
    backups = list(tmp_path.glob("bookmarks.json.corrupt.*"))
    assert len(backups) == 1

    # Manager should have kept previous bar
    assert mgr.bar[0]["name"] == "Good"


def test_reload_handles_missing_file(tmp_path, monkeypatch):
    file_path = tmp_path / "nonexistent.json"

    class Pwd:
        def joinpath(self, _):
            return str(file_path)

    monkeypatch.setattr("app.services.bookmark_bar_manager.pwd", Pwd())
    monkeypatch.setattr(
        "app.services.bookmark_bar_manager.FaviconStore", lambda: DummyFaviconStore()
    )

    mgr = BookmarkBarManager("nonexistent.json")
    # Missing file should result in empty bar, not exception
    assert isinstance(mgr.bar, list)
    assert mgr.bar == []


def test_reload_rejects_legacy_flat_array_format(tmp_path, monkeypatch):
    """Test that legacy flat array format is rejected with clear error."""
    file_path = tmp_path / "bookmarks.json"
    # Legacy flat array format (no longer supported)
    legacy_data = [{"name": "Test", "href": "https://example.com"}]
    write_file(file_path, json.dumps(legacy_data))

    class Pwd:
        def joinpath(self, _):
            return str(file_path)

    monkeypatch.setattr("app.services.bookmark_bar_manager.pwd", Pwd())
    monkeypatch.setattr(
        "app.services.bookmark_bar_manager.FaviconStore", lambda: DummyFaviconStore()
    )

    mgr = BookmarkBarManager("bookmarks.json")
    # Should have empty bar since legacy format is rejected
    assert mgr.bar == []

    # Backup should be created for the invalid format file
    backups = list(tmp_path.glob("bookmarks.json.corrupt.*"))
    assert len(backups) == 1
