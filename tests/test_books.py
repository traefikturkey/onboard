"""Books catalog and browser PDF responses."""

import json

import pytest
from bs4 import BeautifulSoup

PDF = b"%PDF-1.4\nSample book\n%%EOF\n"


@pytest.fixture(autouse=True)
def isolate_books(test_app, tmp_path):
    test_app.config.update(
        ONBOARD_BOOKS_ROOT=None, ONBOARD_BOOKS_METADATA=tmp_path / "books.json"
    )


def test_books_are_opt_in(test_client):

    assert b'/books/' not in test_client.get("/").data
    assert test_client.get("/books/").status_code == 404
    assert test_client.get("/books/pdf/sample.pdf").status_code == 404
    assert test_client.get(f"/books/cover/{'a' * 64}.jpg").status_code == 404


def test_catalog_lists_current_pdfs_with_folder_filters(
    test_app, test_client, tmp_path
):
    test_app.config["ONBOARD_BOOKS_ROOT"] = tmp_path
    shelf = tmp_path / "Computer_Science"
    shelf.mkdir()
    (shelf / "One & Two.PDF").write_bytes(PDF)
    (shelf / "notes.txt").write_text("not a book")
    (shelf / ".hidden.pdf").write_bytes(PDF)
    nas_metadata = shelf / "@eaDir"
    nas_metadata.mkdir()
    (nas_metadata / "thumbnail.pdf").write_bytes(PDF)
    nested = shelf / "Compilers"
    nested.mkdir()

    assert b'href="/books/"' in test_client.get("/").data
    response = test_client.get("/books/")
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "private, no-store"
    assert b'hx-history="false"' in response.data
    page = BeautifulSoup(response.data, 'html.parser')
    options = page.select('#books-folder option')
    assert [(option['value'], option.text) for option in options] == [
        ('', 'All folders'),
        ('Computer_Science', 'Computer Science'),
    ]
    assert page.select_one('.book-tile')['data-folder'] == 'Computer_Science'
    assert b"One &amp; Two" in response.data
    assert b'/books/pdf/Computer_Science/One%20&amp;%20Two.PDF' in response.data
    assert b"notes.txt" not in response.data
    assert b".hidden.pdf" not in response.data
    assert b"thumbnail.pdf" not in response.data

    (nested / "#1 Parsers%.pdf").write_bytes(PDF)
    updated = test_client.get("/books/")
    url = "/books/pdf/Computer_Science/Compilers/%231%20Parsers%25.pdf"
    assert b'<option value="Computer_Science/Compilers">' in updated.data
    assert b"Computer Science / Compilers" in updated.data
    assert url.encode() in updated.data
    with test_client.get(url) as book:
        assert book.data == PDF


def test_metadata_displays_cover_caption_and_native_details(
    test_app, test_client, tmp_path
):
    root = tmp_path / "books"
    root.mkdir()
    pdf = root / "imported_title_-_Doe_v2.pdf"
    pdf.write_bytes(PDF)
    (root / "Other_Title.pdf").write_bytes(PDF)
    metadata_file = tmp_path / "books.json"
    cover = "a" * 64 + ".jpg"
    covers = tmp_path / "book-covers"
    covers.mkdir()
    (covers / cover).write_bytes(b"cover")
    test_app.config.update(
        ONBOARD_BOOKS_ROOT=root, ONBOARD_BOOKS_METADATA=metadata_file
    )
    metadata = {
        pdf.name: {
            "title": "Verified & Complete",
            "subtitle": "A Guide",
            "authors": ["Jane Doe", "Alex Lee"],
            "date": "2025-02-01",
            "edition": "2nd edition",
            "summary": "Example <book> summary.",
            "cover": cover,
        },
        "absent.pdf": {"title": "A book not in the library"},
    }
    metadata_file.write_text(json.dumps(metadata), encoding="utf-8")

    response = test_client.get("/books/")
    assert response.status_code == 200
    page = BeautifulSoup(response.data, 'html.parser')
    assert page.select_one('.books-filters').has_attr('hidden')
    fallback, tile = page.select('.books-grid > li')
    assert fallback.select_one('.book-title').text == 'Other Title'
    assert (
        fallback.select_one('.book-cover-fallback').get_text(strip=True)
        == 'Other Title'
    )
    assert fallback.img is None
    assert 'A book not in the library' not in page.get_text()
    (link,) = tile.select('a')
    assert link['href'] == '/books/pdf/imported_title_-_Doe_v2.pdf'
    assert link['target'] == '_blank'
    assert link['hx-boost'] == 'false'
    assert link.select_one('.book-title')['id'] == link['aria-labelledby']
    assert link.select_one('.book-title').text == 'Verified & Complete'
    assert link.img['src'] == f'/books/cover/{cover}'
    assert link.img['loading'] == 'lazy'
    assert tile.select_one('.book-edition').text == '2025 · 2nd edition'
    toggle = tile.select_one('.book-details-toggle')
    assert not toggle.has_attr('hidden')
    panel = tile.find(id=toggle['popovertarget'])
    assert panel['popover'] == 'auto'
    (preview,) = page.select('.book-hover-preview')
    assert preview['popover'] == 'manual'
    assert preview['aria-hidden'] == 'true'
    assert not preview.get_text(strip=True)
    assert panel.find(id=panel['aria-labelledby']).text == 'Verified & Complete'
    assert panel.img is None
    assert 'A Guide' in panel.text
    assert 'Jane Doe, Alex Lee' in panel.text
    assert panel.time.text == '2025-02-01'
    assert '2nd edition' in panel.text
    assert 'Folder: Unsorted' in panel.text
    assert 'Example <book> summary.' in panel.text
    assert panel.find('book') is None
    with test_client.get(f"/books/cover/{cover}") as response:
        assert response.status_code == 200
        assert response.mimetype == "image/jpeg"
        assert response.headers["Cache-Control"] == "private, no-store"
        assert response.data == b"cover"
    assert test_client.get("/books/cover/not-a-cover.jpg").status_code == 404
    assert pdf.read_bytes() == PDF


def test_catalog_sorts_by_title_then_path_and_derives_topics(
    test_app, test_client, tmp_path
):
    root = tmp_path / 'library'
    root.mkdir()
    (root / 'Z_shelf').mkdir()
    for path in ('Z_shelf/second.pdf', 'first.pdf', 'last.pdf', 'earliest.pdf'):
        (root / path).write_bytes(PDF)
    test_app.config['ONBOARD_BOOKS_ROOT'] = root
    (tmp_path / 'books.json').write_text(
        json.dumps(
            {
                'absent.pdf': {'tags': ['URBAN GARDEN', 'Stale']},
                'Z_shelf/second.pdf': {
                    'title': 'A title',
                    'tags': ['  Urban\t Garden ', 'urban garden', None, '', 'Design'],
                },
                'first.pdf': {
                    'title': 'A title',
                    'tags': ['urban garden', ' Design ', '   '],
                    'summary': 'Unique summary word',
                },
                'last.pdf': {'title': 'Z title', 'tags': 'Not a list'},
                'earliest.pdf': {'title': '0 title', 'tags': []},
            }
        ),
        encoding='utf-8',
    )

    page = BeautifulSoup(test_client.get('/books/').data, 'html.parser')
    tiles = page.select('.books-grid > li')
    assert [tile.a['href'] for tile in tiles] == [
        '/books/pdf/earliest.pdf',
        '/books/pdf/Z_shelf/second.pdf',
        '/books/pdf/first.pdf',
        '/books/pdf/last.pdf',
    ]
    assert {
        chip['data-topic']: ' '.join(chip.stripped_strings)
        for chip in page.select('button[data-topic]')
    } == {
        '': 'Untagged 2',
        'design': 'Design 2',
        'urban garden': 'Urban Garden 2',
    }
    assert json.loads(tiles[2]['data-topics']) == ['urban garden', 'design']
    assert 'Unique summary word' not in tiles[2]['data-search']
    assert 'Topics: Urban Garden, Design' in tiles[2].select_one('.book-details').text


def test_empty_catalog_still_renders_as_books_page(test_app, test_client, tmp_path):
    test_app.config['ONBOARD_BOOKS_ROOT'] = tmp_path

    response = test_client.get('/books/')
    assert response.status_code == 200
    page = BeautifulSoup(response.data, 'html.parser')
    assert page.body['hx-history'] == 'false'
    assert page.title.text.startswith('Books - ')
    assert page.select_one('a[aria-current=page]')['href'] == '/books/'
    assert 'No PDF books found.' in page.select_one('.books-catalog').text
    assert page.select_one('.books-filters') is None


def test_invalid_metadata_does_not_hide_books(test_app, test_client, tmp_path):
    root = tmp_path / "books"
    root.mkdir()
    (root / "Fallback_Title.pdf").write_bytes(PDF)
    metadata_file = tmp_path / "books.json"
    metadata_file.write_text("{invalid JSON}", encoding="utf-8")
    test_app.config.update(
        ONBOARD_BOOKS_ROOT=root, ONBOARD_BOOKS_METADATA=metadata_file
    )

    response = test_client.get("/books/")
    assert response.status_code == 200
    page = BeautifulSoup(response.data, 'html.parser')
    assert page.select_one('.book-title').text == 'Fallback Title'
    assert page.select_one('.book-details-toggle').has_attr('popovertarget')
    assert page.select_one('.books-topics') is None


def test_pdf_opens_inline_and_supports_range(test_app, test_client, tmp_path):
    test_app.config["ONBOARD_BOOKS_ROOT"] = tmp_path
    (tmp_path / "One & Two.PDF").write_bytes(PDF)
    url = "/books/pdf/One%20%26%20Two.PDF"

    with test_client.get(url) as response:
        assert response.status_code == 200
        assert response.mimetype == "application/pdf"
        assert response.headers["Content-Disposition"].startswith("inline;")
        assert response.headers["Cache-Control"] == "private, no-store"
        assert response.data == PDF

    with test_client.get(url, headers={"Range": "bytes=0-7"}) as response:
        assert response.status_code == 206
        assert response.headers["Content-Range"] == f"bytes 0-7/{len(PDF)}"
        assert response.data == PDF[:8]


def test_only_library_pdfs_are_served(test_app, test_client, tmp_path):
    root = tmp_path / "books"
    root.mkdir()
    test_app.config["ONBOARD_BOOKS_ROOT"] = root
    (root / "notes.txt").write_text("not a book")
    (root / ".hidden.pdf").write_bytes(PDF)
    (root / "directory.pdf").mkdir()

    for name in ("missing.pdf", "notes.txt", ".hidden.pdf", "directory.pdf"):
        assert test_client.get(f"/books/pdf/{name}").status_code == 404


def test_symlinks_are_not_listed_or_served(test_app, test_client, tmp_path):
    root = tmp_path / "books"
    root.mkdir()
    test_app.config["ONBOARD_BOOKS_ROOT"] = root
    outside = tmp_path / "outside.pdf"
    outside.write_bytes(PDF)
    link = root / "linked.pdf"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("Creating symlinks is not permitted on this host")

    assert b"linked.pdf" not in test_client.get("/books/").data
    assert test_client.get("/books/pdf/linked.pdf").status_code == 404


def test_missing_mount_reports_unavailable(test_app, test_client, tmp_path):
    root = tmp_path / "not-mounted"
    test_app.config["ONBOARD_BOOKS_ROOT"] = root

    response = test_client.get("/books/")
    assert response.status_code == 503
    assert str(root).encode() not in response.data
