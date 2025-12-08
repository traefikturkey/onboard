from onboard.services.text_extractor import TextExtractor


def test_text_extractor_network_fallback(monkeypatch):
    te = TextExtractor()

    # Simulate network failure
    monkeypatch.setattr(te, "_fetch", lambda url: None)
    result = te.extract("https://example.com/page")
    assert result.title == "https://example.com/page"
    assert result.text == ""
    assert isinstance(result.content_hash, str) and len(result.content_hash) == 64
