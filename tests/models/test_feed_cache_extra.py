import json
from pathlib import Path

from app.models.feed_cache import FeedCache


def test_archive_moves_large_json_and_skips_others(tmp_path):
  cache_root = tmp_path
  cache_dir = cache_root.joinpath("cache")
  cache_dir.mkdir()

  # small json (should be ignored)
  small = cache_dir.joinpath("small.json")
  small.write_text(json.dumps({"articles": []}), encoding="utf-8")

  # large json (should be moved)
  large = cache_dir.joinpath("large.json")
  large.write_text("x" * 1024, encoding="utf-8")

  # non-json file (should be ignored)
  other = cache_dir.joinpath("ignore.txt")
  other.write_text("hello", encoding="utf-8")

  fc = FeedCache("testfeed", working_dir=cache_root)

  moved = fc.archive_large_jsons(min_size_bytes=100)

  assert len(moved) == 1
  dest = moved[0]
  assert dest.exists()
  assert dest.name == "large.json"
  # original large file removed
  assert not (cache_dir.joinpath("large.json")).exists()


def test_archive_handles_filenotfound(tmp_path, monkeypatch):
  cache_root = tmp_path
  cache_dir = cache_root.joinpath("cache")
  cache_dir.mkdir()

  disappearing = cache_dir.joinpath("will_disappear.json")
  disappearing.write_text("{}", encoding="utf-8")

  fc = FeedCache("feed", working_dir=cache_root)

  # monkeypatch Path.stat to raise FileNotFoundError for this specific file
  original_stat = Path.stat

  def fake_stat(self, *args, **kwargs):
    if self.name == "will_disappear.json":
      raise FileNotFoundError()
    return original_stat(self, *args, **kwargs)

  # ensure is_file does not call the original stat (which would raise) so the exception
  # occurs inside the try/except block in archive_large_jsons
  def fake_is_file(self):
    return True

  monkeypatch.setattr(Path, "is_file", fake_is_file)
  monkeypatch.setattr(Path, "stat", fake_stat)

  # Should not raise and should return empty moved list
  moved = fc.archive_large_jsons(min_size_bytes=0)
  assert moved == []


def test_load_cache_swallows_archive_exceptions_and_reads_file(tmp_path, monkeypatch):
  cache_root = tmp_path
  cache_dir = cache_root.joinpath("cache")
  cache_dir.mkdir()

  data = {"articles": [{"id": 1}]}
  cache_file = cache_dir.joinpath("myfeed.json")
  cache_file.write_text(json.dumps(data), encoding="utf-8")

  fc = FeedCache("myfeed", working_dir=cache_root)

  # Make archive_large_jsons raise an exception; load_cache should swallow it and still return data
  def raise_err():
    raise RuntimeError("boom")

  monkeypatch.setattr(fc, "archive_large_jsons", raise_err)

  articles = fc.load_cache(archive_on_load=True)
  assert articles == data["articles"]


def test_load_cache_invalid_and_non_dict_payloads_return_empty(tmp_path):
  cache_root = tmp_path
  cache_dir = cache_root.joinpath("cache")
  cache_dir.mkdir()

  fc = FeedCache("feedx", working_dir=cache_root)
  # invalid json
  p = cache_dir.joinpath("feedx.json")
  p.write_text("not-valid-json", encoding="utf-8")
  assert fc.load_cache() == []

  # non-dict json (e.g., list)
  p.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
  assert fc.load_cache() == []


def test_save_articles_writes_file_atomically(tmp_path):
  cache_root = tmp_path
  fc = FeedCache("saver", working_dir=cache_root)

  articles = [{"a": 1}]
  ret = fc.save_articles(articles)
  assert ret is articles
  # file should exist and contain the articles
  loaded = fc.load_cache(archive_on_load=False)
  assert loaded == articles
