from app.services.favicon_store import FaviconStore


class FakeScheduler:
    def __init__(self):
        self.calls = []

    def add_job(self, func, *a, **kw):
        # capture both positional args and kw args for assertions
        self.calls.append(
            {
                "func": func,
                "pos_args": a,
                "kw": kw,
            }
        )


def test_icon_path_and_none(tmp_path, monkeypatch):
    # patch module-level pwd to point to tmp_path
    monkeypatch.setattr("app.services.favicon_store.pwd", tmp_path)

    # patch favicon_filename to a predictable name
    monkeypatch.setattr(
        "app.services.favicon_store.favicon_filename", lambda u: "ic.ico"
    )

    store = FaviconStore(icon_dir="static/icons")

    # create the icon file
    icon_file = tmp_path / "static/icons/ic.ico"
    icon_file.parent.mkdir(parents=True, exist_ok=True)
    icon_file.write_text("x")

    assert store.icon_path("http://example.com") == "/static/icons/ic.ico"
    assert store.icon_path(None) is None


def test_favicon_failed_marker(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.favicon_store.pwd", tmp_path)
    monkeypatch.setattr(
        "app.services.favicon_store.favicon_failed_filename", lambda u: "fail.failed"
    )

    store = FaviconStore(icon_dir="icons")

    # no marker yet
    assert store.favicon_failed("http://foo") is False

    failed_file = tmp_path / "icons/fail.failed"
    failed_file.parent.mkdir(parents=True, exist_ok=True)
    failed_file.write_text("")

    assert store.favicon_failed("http://foo") is True


def test_should_processed_variants(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.favicon_store.pwd", tmp_path)
    store = FaviconStore(icon_dir="icons")

    # None/empty url -> False
    assert store.should_processed(None) is False

    # IP address should be detected by pattern -> False
    assert store.should_processed("http://127.0.0.1:8000/") is False

    # If icon_path returns truthy -> not processed
    monkeypatch.setattr(store, "icon_path", lambda u: "/icons/exists.ico")
    assert store.should_processed("http://example.com") is False

    # If favicon_failed is True -> not processed
    monkeypatch.setattr(store, "icon_path", lambda u: None)
    monkeypatch.setattr(store, "favicon_failed", lambda u: True)
    assert store.should_processed("http://example.com") is False

    # normal case -> True
    monkeypatch.setattr(store, "favicon_failed", lambda u: False)
    assert store.should_processed("http://normal.example.com") is True


def test_fetch_favicons_from_schedules_dedupe(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.favicon_store.pwd", tmp_path)

    fake_scheduler = FakeScheduler()
    monkeypatch.setattr(
        "app.services.favicon_store.Scheduler.getScheduler", lambda: fake_scheduler
    )

    # base() will map different URLs to the same base (simulate)
    monkeypatch.setattr(
        "app.services.favicon_store.base",
        lambda u: u.split("/")[2] if "/" in u else u,
    )

    store = FaviconStore(icon_dir="icons")

    urls = [
        "http://example.com/path1",
        "https://example.com/path2",
        "http://other.test/",
    ]

    store.fetch_favicons_from(urls)

    # should schedule one job for fetch_favicons
    assert any(
        call["kw"].get("id") == "fetch_favicons" for call in fake_scheduler.calls
    )

    # inspect the call and ensure deduped bases are passed
    fetch_call = next(
        call
        for call in fake_scheduler.calls
        if call["kw"].get("id") == "fetch_favicons"
    )
    # args may be positional or kw; fetch_favicons uses args=[processable_urls]
    arg_sets = []
    if fetch_call["pos_args"]:
        arg_sets = list(fetch_call["pos_args"])
    if fetch_call["kw"].get("args"):
        arg_sets = list(fetch_call["kw"]["args"])

    # the first element should be a set of bases
    assert any(isinstance(x, set) for x in arg_sets)


def test__process_urls_for_favicons_schedules_downloads(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.favicon_store.pwd", tmp_path)

    fake_scheduler = FakeScheduler()
    monkeypatch.setattr(
        "app.services.favicon_store.Scheduler.getScheduler", lambda: fake_scheduler
    )

    # patch download_favicon in the module so the scheduled function is the imported symbol
    downloaded = []

    def fake_download(url, icon_dir):
        downloaded.append((url, icon_dir))

    monkeypatch.setattr("app.services.favicon_store.download_favicon", fake_download)

    store = FaviconStore(icon_dir="icons")

    urls = {"http://a.com/", "http://b.com/"}
    store._process_urls_for_favicons(urls)

    # ensure a job was scheduled for each url
    scheduled_ids = {c["kw"].get("id") for c in fake_scheduler.calls}
    assert all(f"_get_favicon_({u})" in scheduled_ids for u in urls)

    # ensure the fake download wasn't executed by scheduler but is available as the function
    # (we verify the add_job recorded the function object)
    funcs = [c["func"] for c in fake_scheduler.calls]
    assert any(f is fake_download for f in funcs)
