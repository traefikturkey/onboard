from types import SimpleNamespace

import pytest
from bs4 import BeautifulSoup

from app.models.bookmark import Bookmark


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
        Bookmark.from_dict({"name": name, "link": link}, SimpleNamespace(id="layout"))
        for name, link in headers
    ]
    mock_layout.bookmark_bar = []
    mock_layout.tabs = [SimpleNamespace(name="Home")]
    mock_layout.tab.return_value = SimpleNamespace(rows=[])

    response = test_client.get("/")

    assert response.status_code == 200
    soup = BeautifulSoup(response.data, "html.parser")
    links = soup.select(".header .row:not(.tab-bar) > a")
    assert "header-link-with-icon" not in soup.select_one(".tab-bar a").get("class", [])
    assert [(link.get_text(strip=True), link["href"]) for link in links] == headers
    assert all(link["target"] == "_blank" for link in links)
    assert len([icon for link in links for icon in link.select("img")]) == len(icons)

    for link in links:
        filename = icons.get(link.get_text(strip=True))
        if filename is None:
            assert link.find("img") is None
            assert "header-link-with-icon" not in link.get("class", [])
            continue

        assert link["class"] == ["header-link-with-icon"]
        icon = link.find("img")
        assert icon["src"] == f"/static/img/{filename}"
        assert icon["class"] == ["header-link-icon"]
        assert icon["alt"] == ""
        assert (icon["width"], icon["height"]) == ("16", "16")

        resource = test_client.get(icon["src"])
        assert resource.status_code == 200
        assert resource.data.startswith(b"\x00\x00\x01\x00")


def test_header_search_menu_keeps_homepage_link_and_exact_search_url(
    test_client, mock_layout
):
    search_url = "https://example.com/search?q=3d%20printer&filter=1"
    mock_layout.headers = [
        Bookmark.from_dict(
            {
                "name": "Searches",
                "link": "https://example.com/",
                "contents": [{"name": "3D Printer", "href": search_url}],
                "multiColumn": 2,
            },
            SimpleNamespace(id="layout"),
        )
    ]
    mock_layout.bookmark_bar = []
    mock_layout.tabs = [SimpleNamespace(name="Home")]
    mock_layout.tab.return_value = SimpleNamespace(rows=[])

    response = test_client.get("/")

    assert response.status_code == 200
    soup = BeautifulSoup(response.data, "html.parser")
    menu = soup.select_one("[data-utility-menu]")
    homepage = menu.select_one(":scope > a")
    assert homepage["href"] == "https://example.com/"
    assert homepage["target"] == "_blank"
    toggle = menu.select_one("button")
    dropdown = menu.select_one("ul")
    assert toggle["aria-expanded"] == "false"
    assert toggle["aria-controls"] == dropdown["id"]
    assert dropdown.has_attr("hidden")
    assert dropdown.select_one("a")["href"] == search_url
    assert dropdown.select_one("a")["target"] == "_blank"
    assert soup.select_one('script[src="/static/js/header-menu.js"]') is not None
