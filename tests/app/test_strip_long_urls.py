from app.processors.strip_long_urls import StripLongUrls


class DummyArticle:
    def __init__(self, title):
        # The processor now targets the `name` field used by the widget/template.
        # Keep `title` for compatibility but tests should assert on `name`.
        self.name = title
        self.title = title


def test_short_url_kept():
    processor = StripLongUrls()
    a = DummyArticle("Short link http://ex.com/abc")
    out = processor.process([a])
    assert out[0].name == "Short link http://ex.com/abc"


def test_long_url_stripped():
    processor = StripLongUrls()
    long_url = "https://example.com/" + "x" * 60
    a = DummyArticle(f"Breaking: {long_url}")
    out = processor.process([a])
    assert "http" not in out[0].name
    assert out[0].name.strip() == "Breaking"


def test_mixed_urls_only_long_removed():
    processor = StripLongUrls()
    long_url = "https://example.com/" + "y" * 50
    short_url = "http://t.co/abc"
    a = DummyArticle(f"Update {short_url} and {long_url}")
    out = processor.process([a])
    assert "http://t.co/abc" in out[0].name
    assert "example.com" not in out[0].name


def test_only_long_url_keeps_original():
    processor = StripLongUrls()
    long_url = "http://" + "z" * 100
    a = DummyArticle(long_url)
    out = processor.process([a])
    # Processor is conservative: if stripping produces empty name, original is preserved
    assert out[0].name == long_url


def test_threshold_env_override(tmp_path, monkeypatch):
    monkeypatch.setenv("ONBOARD_STRIP_URL_LENGTH", "10")
    processor = StripLongUrls()
    shortish = "http://short"  # length 12 -> with threshold 10 should be removed
    a = DummyArticle(f"Title {shortish}")
    out = processor.process([a])
    assert "http" not in out[0].name
