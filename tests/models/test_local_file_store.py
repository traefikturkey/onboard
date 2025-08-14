from pathlib import Path

from app.models.local_file_store import LocalFileStore


def test_write_and_read_roundtrip(tmp_path: Path):
    store = LocalFileStore()
    p = tmp_path.joinpath("cache/test.json")
    data = {"articles": [{"id": 1, "title": "a"}]}

    store.write_json_atomic(p, data)
    read = store.read_json(p)
    assert read == data


def test_list_and_move(tmp_path: Path):
    store = LocalFileStore()
    cache_dir = tmp_path.joinpath("cache")
    cache_dir.mkdir()
    a = cache_dir.joinpath("a.json")
    b = cache_dir.joinpath("b.json")

    store.write_json_atomic(a, {"foo": 1})
    store.write_json_atomic(b, {"foo": 2})

    entries = store.list_dir(cache_dir)
    assert set([p.name for p in entries]) >= {"a.json", "b.json"}

    dst_dir = tmp_path.joinpath("archive")
    dst = dst_dir.joinpath("a.json")
    store.move(a, dst)
    assert not a.exists()
    assert dst.exists()
    assert store.read_json(dst)["foo"] == 1
