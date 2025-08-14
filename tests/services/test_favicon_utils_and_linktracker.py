from app.services.link_tracker import LinkTracker
from app.services import favicon_utils
import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


class TestFaviconUtilsAndLinkTracker(unittest.TestCase):
  def setUp(self):
    self.tmpdir = tempfile.TemporaryDirectory()
    self.base = Path(self.tmpdir.name)

  def tearDown(self):
    self.tmpdir.cleanup()

  def test_normalize_and_base_and_filenames(self):
    self.assertEqual(favicon_utils.normalize_domain("http://example.com/path"), "example.com")
    self.assertEqual(favicon_utils.base("http://example.com/path"), "http://example.com")
    self.assertEqual(favicon_utils.favicon_filename("http://example.com"), "example.com.favicon.ico")
    self.assertEqual(favicon_utils.favicon_failed_filename("http://example.com"), "example.com.failed")

  def test_favicon_path_and_download_failure_creates_failed_file(self):
    icon_dir = self.base / "icons"
    icon_dir.mkdir()
    # mock make_request to return non-image

    class R:
      status_code = 200
      headers = {"content-type": "text/html"}
      content = b"notimage"
      text = ""

    with patch("app.services.favicon_utils.make_request", return_value=R()):
      # call _download indirectly via download_favicon
      favicon_utils._download("http://example.com", str(icon_dir), "http://example.com/favicon.ico")
      failed = icon_dir / "example.com.failed"
      self.assertTrue(failed.exists())

  def test_link_tracker_insert_and_query(self):
    # patch pwd so db goes to temp configs
    with patch("app.models.utils.pwd", self.base):
      lt = LinkTracker()
      lt.cursor.execute("DELETE FROM CLICK_EVENTS")
      lt.connection.commit()
      lt.track_click_event("w", "l", "http://a")
      df = lt.get_click_events()
      self.assertEqual(len(df), 1)
