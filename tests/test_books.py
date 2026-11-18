"""Books catalog and browser PDF responses."""

import pytest

PDF = b"%PDF-1.4\nSample book\n%%EOF\n"


def test_books_are_opt_in(test_app, test_client):
    test_app.config["ONBOARD_BOOKS_ROOT"] = None

    assert b'/books/' not in test_client.get("/").data
    assert test_client.get("/books/").status_code == 404
    assert test_client.get("/books/pdf/sample.pdf").status_code == 404


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

    (nested / "Parsers #1%.pdf").write_bytes(PDF)
    updated = test_client.get("/books/")
    url = "/books/pdf/Computer_Science/Compilers/Parsers%20%231%25.pdf"
    assert b"Computer Science / Compilers (1)" in updated.data
    assert url.encode() in updated.data
    with test_client.get(url) as book:
        assert book.data == PDF


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
