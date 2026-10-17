import importlib
from types import SimpleNamespace

import pytest
from bs4 import BeautifulSoup
from jinja2 import DictLoader


@pytest.mark.parametrize("app_kind", ["factory", "main"])
def test_feed_fragment_escapes_decoded_feed_content_and_removes_load_trigger(
    app_kind, mock_layout, mock_bookmark_manager, mock_link_tracker, monkeypatch
):
    if app_kind == "factory":
        from app.factory import create_app

        app = create_app(
            layout=mock_layout,
            bookmark_manager=mock_bookmark_manager,
            link_tracker=mock_link_tracker,
            testing=True,
        )
    else:
        main = importlib.import_module("app.main")
        app = main.app
        monkeypatch.setattr(main, "layout", mock_layout)

    mock_layout.get_feed.return_value = SimpleNamespace(template="feed_fragment.html")
    loader = DictLoader(
        {
            "feed_fragment.html": (
                '<div hx-trigger="load once">{{ widget.payload }}</div>'
                '<span title="{{ widget.attribute }}">ok</span>'
            )
        }
    )
    monkeypatch.setattr(app, "jinja_loader", loader)
    mock_layout.get_feed.return_value.payload = "<script>alert(1)</script>"
    mock_layout.get_feed.return_value.attribute = 'x" onmouseover="alert(1)'

    response = app.test_client().get("/feed/example")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    parsed = BeautifulSoup(body, "html.parser")
    assert not parsed.find("div").has_attr("hx-trigger")
    assert parsed.find("div").get_text() == "<script>alert(1)</script>"
    assert parsed.find("script") is None
    span = parsed.find("span")
    assert span["title"] == 'x" onmouseover="alert(1)'
    assert not span.has_attr("onmouseover")
    assert "<script>" not in body
