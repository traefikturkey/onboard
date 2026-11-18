"""Books catalog and browser PDF responses."""

import json

import pytest

PDF = b"%PDF-1.4\nSample book\n%%EOF\n"


def test_books_are_opt_in(test_app, test_client):
    test_app.config["ONBOARD_BOOKS_ROOT"] = None

    assert b'/books/' not in test_client.get("/").data
    assert test_client.get("/books/").status_code == 404
    assert test_client.get("/books/pdf/sample.pdf").status_code == 404
    assert test_client.get(f"/books/cover/{'a' * 64}.jpg").status_code == 404


def test_catalog_lists_current_pdfs_by_folder(test_app, test_client, tmp_path):
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
    assert b"Computer Science (1)" in response.data
    assert b"One &amp; Two" in response.data
    assert b'/books/pdf/Computer_Science/One%20&amp;%20Two.PDF' in response.data
    assert b"notes.txt" not in response.data
    assert b".hidden.pdf" not in response.data
    assert b"thumbnail.pdf" not in response.data

    (nested / "#1 Parsers%.pdf").write_bytes(PDF)
    updated = test_client.get("/books/")
    url = "/books/pdf/Computer_Science/Compilers/%231%20Parsers%25.pdf"
    assert b"Computer Science / Compilers (1)" in updated.data
    assert url.encode() in updated.data
    with test_client.get(url) as book:
        assert book.data == PDF


def test_metadata_displays_clean_title_and_optional_details(test_app, test_client, tmp_path):
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

    page = test_client.get("/books/")
    assert page.status_code == 200
    assert b"Verified &amp; Complete</a>" in page.data
    assert b"/books/pdf/imported_title_-_Doe_v2.pdf" in page.data
    assert b"Other Title</a>" in page.data
    assert b"A book not in the library" not in page.data
    assert page.data.count(b'popover="manual"') == 1
    assert b"A Guide" in page.data
    assert b"Jane Doe, Alex Lee" in page.data
    assert b' datetime="2025-02-01"' in page.data
    assert b"2nd edition" in page.data
    assert b"Example &lt;book&gt; summary." in page.data
    assert f'data-cover="/books/cover/{cover}"'.encode() in page.data
    with test_client.get(f"/books/cover/{cover}") as response:
        assert response.status_code == 200
        assert response.mimetype == "image/jpeg"
        assert response.headers["Cache-Control"] == "private, no-store"
        assert response.data == b"cover"
    assert test_client.get("/books/cover/not-a-cover.jpg").status_code == 404
    assert pdf.read_bytes() == PDF


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
    assert b"Fallback Title</a>" in response.data
    assert b'popover="manual"' not in response.data


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
