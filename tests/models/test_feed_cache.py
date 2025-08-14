import json
from pathlib import Path
from app.models.feed_cache import FeedCache

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

  working_dir = tmp_path / "workdir"
  assert not working_dir.exists()

  fc = FeedCache("test-feed", working_dir=working_dir)

  # Should not raise, should create cache dir and return empty list
  articles = fc.load_cache(archive_on_load=False)
  assert isinstance(articles, list)
  assert articles == []
  assert fc.cache_dir.exists()


def test_save_and_load_roundtrip(tmp_path):
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

  # Simulate an internal archive error by making the file_store.move call raise;
  # archive_large_jsons should log and swallow this and load_cache should
  # still return the cached articles.
  def raise_err(*args, **kwargs):
    raise RuntimeError("boom")

  monkeypatch.setattr(fc.file_store, "move", raise_err)

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
