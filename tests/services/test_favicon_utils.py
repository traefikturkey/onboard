import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.services import favicon_utils as fu


class TestFaviconUtils(unittest.TestCase):
  def setUp(self):
    self.tmpdir = tempfile.TemporaryDirectory()
    self.base = Path(self.tmpdir.name)
    (self.base / "static/icons_test").mkdir(parents=True, exist_ok=True)
    # favicon_utils imported pwd at module import time; patch that reference
    self.patcher = patch("app.services.favicon_utils.pwd", self.base)
    self.patcher.start()

  def tearDown(self):
    self.patcher.stop()
    self.tmpdir.cleanup()

  def test_normalize_base_and_filenames(self):
    self.assertEqual(fu.normalize_domain("http://example.com/path"), "example.com")
    self.assertEqual(fu.base("http://example.com/page"), "http://example.com")
    self.assertEqual(fu.favicon_filename("http://example.com"), "example.com.favicon.ico")
    self.assertEqual(fu.favicon_failed_filename("http://example.com"), "example.com.failed")

  def test_find_favicon_from_relative_and_absolute(self):
    resp = MagicMock()
    resp.status_code = 200
    resp.text = '<html><head><link rel="icon" href="/fav.ico"></head></html>'

    with patch("app.services.favicon_utils.make_request", return_value=resp):
      url = "http://example.com/some/page"
      found = fu.find_favicon_from(url)
      self.assertEqual(found, "http://example.com/fav.ico")

    resp2 = MagicMock()
    resp2.status_code = 200
    resp2.text = '<html><head><link rel="icon" href="http://cdn.example.com/icon.png"></head></html>'

    with patch("app.services.favicon_utils.make_request", return_value=resp2):
      found2 = fu.find_favicon_from("http://example.com/")
      self.assertEqual(found2, "http://cdn.example.com/icon.png")

  def test_find_favicon_from_handles_errors_and_non200(self):
    with patch("app.services.favicon_utils.make_request", side_effect=Exception("boom")):
      self.assertIsNone(fu.find_favicon_from("http://bad.example"))

    resp = MagicMock()
    resp.status_code = 404
    resp.text = ""
    with patch("app.services.favicon_utils.make_request", return_value=resp):
      self.assertIsNone(fu.find_favicon_from("http://nope.example"))

  def test__download_writes_image_and_marks_failed_and_handles_exception(self):
    icon_dir = "static/icons_test"
    img_resp = MagicMock()
    img_resp.status_code = 200
    img_resp.headers = {"content-type": "image/png"}
    img_resp.content = b"PNGDATA"

    with patch("app.services.favicon_utils.make_request", return_value=img_resp):
      fu._download("http://example.com", icon_dir, "http://cdn/icon.png")
      expected_file = self.base.joinpath(icon_dir, fu.favicon_filename("http://example.com"))
      self.assertTrue(expected_file.exists())
      self.assertEqual(expected_file.read_bytes(), b"PNGDATA")

    bad_resp = MagicMock()
    bad_resp.status_code = 200
    bad_resp.headers = {"content-type": "text/html"}
    bad_resp.content = b"not an image"

    with patch("app.services.favicon_utils.make_request", return_value=bad_resp):
      fu._download("http://noimage.example", icon_dir, "http://cdn/notimage")
      failed = self.base.joinpath(icon_dir, fu.favicon_failed_filename("http://noimage.example"))
      self.assertTrue(failed.exists())
      txt = failed.read_text()
      self.assertIn("content-type", txt)

    with patch("app.services.favicon_utils.make_request", side_effect=Exception("net")):
      fu._download("http://err.example", icon_dir, "http://cdn/err")
      failed2 = self.base.joinpath(icon_dir, fu.favicon_failed_filename("http://err.example"))
      self.assertTrue(failed2.exists())
      self.assertIn("Error", failed2.read_text())

  def test_download_favicon_uses_google_fallback_when_no_link(self):
    icon_dir = "static/icons_test"
    g_resp = MagicMock()
    g_resp.status_code = 200
    g_resp.headers = {"content-type": "image/x-icon"}
    g_resp.content = b"ICO"

    with patch("app.services.favicon_utils.find_favicon_from", return_value=None):
      with patch("app.services.favicon_utils.make_request", return_value=g_resp):
        fu.download_favicon("http://fallback.example", icon_dir)
        got = self.base.joinpath(icon_dir, fu.favicon_filename("http://fallback.example"))
        self.assertTrue(got.exists())
        self.assertEqual(got.read_bytes(), b"ICO")


if __name__ == "__main__":
  unittest.main()
