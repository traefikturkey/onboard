from types import SimpleNamespace

from bs4 import BeautifulSoup


def test_header_gmail_icon_preserves_utility_links(test_client, mock_layout):
    headers = [
        ("Docs", "https://docs.google.com/"),
        ("Gmail", "https://mail.google.com/mail/u/0/"),
        ("Photos", "https://photos.google.com/"),
        ("Maps", "https://www.google.com/maps"),
        ("Youtube", "https://www.youtube.com/"),
    ]
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
    assert len([icon for link in links for icon in link.select("img")]) == 1

    icon = links[1].find("img")
    assert icon["src"] == "/static/img/gmail.ico"
    assert icon["alt"] == ""
    assert (icon["width"], icon["height"]) == ("16", "16")

    resource = test_client.get(icon["src"])
    assert resource.status_code == 200
    assert resource.data.startswith(b"\x00\x00\x01\x00")
