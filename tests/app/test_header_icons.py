from types import SimpleNamespace

import pytest
from bs4 import BeautifulSoup


@pytest.mark.parametrize("include_gmail", [False, True])
def test_header_icons_preserve_utility_links(test_client, mock_layout, include_gmail):
    headers = [
        ("Docs", "https://docs.google.com/"),
        ("Photos", "https://photos.google.com/"),
        ("Maps", "https://www.google.com/maps"),
        ("Amazon", "https://www.amazon.com/"),
        ("eBay", "https://www.ebay.com/"),
        ("Youtube", "https://www.youtube.com/"),
        ("Other", "https://example.com/"),
    ]
    icons = {
        "Docs": "docs.ico",
        "Photos": "photos.ico",
        "Maps": "maps.ico",
        "Amazon": "amazon.ico",
        "eBay": "ebay.ico",
        "Youtube": "youtube.ico",
    }
    if include_gmail:
        headers.insert(0, ("Gmail", "https://mail.google.com/mail/u/0/#inbox"))
        icons["Gmail"] = "gmail.ico"

    mock_layout.headers = [
        SimpleNamespace(name=name, link=link) for name, link in headers
    ]
    mock_layout.bookmark_bar = []
    mock_layout.tabs = []
    mock_layout.tab.return_value = SimpleNamespace(rows=[])

    response = test_client.get("/")

    assert response.status_code == 200
    links = BeautifulSoup(response.data, "html.parser").select(".header a")
    assert [(link.get_text(strip=True), link["href"]) for link in links] == headers
    assert all(link["target"] == "_blank" for link in links)
    assert len([icon for link in links for icon in link.select("img")]) == len(icons)

    for link in links:
        filename = icons.get(link.get_text(strip=True))
        if filename is None:
            assert link.find("img") is None
            continue

        icon = link.find("img")
        assert icon["src"] == f"/static/img/{filename}"
        assert icon["class"] == ["header-link-icon"]
        assert icon["alt"] == ""
        assert (icon["width"], icon["height"]) == ("16", "16")

        resource = test_client.get(icon["src"])
        assert resource.status_code == 200
        assert resource.data.startswith(b"\x00\x00\x01\x00")
