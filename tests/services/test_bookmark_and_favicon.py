from app.services.favicon_store import FaviconStore
from app.services.bookmark_bar_manager import BookmarkBarManager
import os
import sys
import json
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


class TestBookmarkFaviconServices(unittest.TestCase):
  def setUp(self):
    self.tmpdir = tempfile.TemporaryDirectory()
    configs = Path(self.tmpdir.name) / "configs"
    configs.mkdir()
    bb = [
        {"href": "http://example.com/a"},
        {"contents": [{"href": "http://example.com/b"}]},
    ]
    (configs / "bookmarks_bar.json").write_text(json.dumps(bb))

    # Patch the pwd used by utils and the services modules so they resolve
    # filesystem paths under the temporary directory created for the test.
    self.patcher_utils = patch("app.models.utils.pwd", Path(self.tmpdir.name))
    self.patcher_bbm = patch(
        "app.services.bookmark_bar_manager.pwd", Path(self.tmpdir.name)
    )
    self.patcher_fs = patch(
        "app.services.favicon_store.pwd", Path(self.tmpdir.name)
    )

    self.patcher_utils.start()
    self.patcher_bbm.start()
    self.patcher_fs.start()

  def tearDown(self):
    self.patcher_utils.stop()
    self.patcher_bbm.stop()
    self.patcher_fs.stop()
    self.tmpdir.cleanup()

  def test_bookmarks_list_and_reload_calls_fetch(self):
    # Use the runtime import path for the favicon store when creating the
    # MagicMock spec so the patched FaviconStore matches the real class.
    from app.services.favicon_store import FaviconStore as FS

    fs = MagicMock(spec=FS)
    with patch("app.services.bookmark_bar_manager.FaviconStore", return_value=fs):
      bbm = BookmarkBarManager("configs/bookmarks_bar.json")
      urls = bbm.bookmarks_list(bbm.bar)
      self.assertIn("http://example.com/a", urls)
      self.assertIn("http://example.com/b", urls)
      fs.fetch_favicons_from.assert_called()

  def test_favicon_store_icon_path_and_failed(self):
    # create a fake icon file in temp pwd and instantiate the store
    base = Path(self.tmpdir.name)
    (base / "static/icons_test").mkdir(parents=True, exist_ok=True)
    fname = base / "static/icons_test/example.com.favicon.ico"
    fname.write_text("x")

    # Ensure the store is created after the module-level pwd has been
    # patched so its icon_dir points into the temp directory.
    fs = FaviconStore(icon_dir="static/icons_test")

    path = fs.icon_path("http://example.com")
    self.assertTrue(path is not None)
    self.assertFalse(fs.favicon_failed("http://doesnotexist.com"))
