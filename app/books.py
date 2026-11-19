"""Browse a configured, read-only directory of PDFs."""

import os
from pathlib import Path

from flask import Blueprint, abort, current_app, render_template, send_file

from app.book_metadata import build_book, cover_path, read_metadata

books = Blueprint("books", __name__, url_prefix="/books")


def library_root() -> Path:
    """Return the mounted library root, or fail without exposing its location."""
    configured = current_app.config.get("ONBOARD_BOOKS_ROOT")
    if not configured:
        abort(404)
    root = Path(configured)
    try:
        if root.is_absolute() and root.is_dir():
            return root.resolve(strict=True)
    except OSError, ValueError:
        pass
    abort(503, "The book library is currently unavailable.")


def pdf_path(root: Path, relative: str) -> Path | None:
    """Allow regular PDFs only, with no hidden paths or symlink components."""
    parts = relative.split("/")
    if any(not part or part.startswith(".") for part in parts):
        return None
    if any(part.startswith(("@", "#")) for part in parts[:-1]):
        return None
    if "\\" in relative or (os.name == "nt" and ":" in relative):
        return None
    if Path(parts[-1]).suffix.lower() != ".pdf":
        return None
    if any(ord(char) < 32 or 0xD800 <= ord(char) <= 0xDFFF for char in relative):
        return None

    path = root.joinpath(*parts)
    try:
        if path.resolve(strict=True) == path and path.is_file():
            return path
    except OSError, RuntimeError:
        pass
    return None


def scan_error(error: OSError) -> None:
    """Propagate a directory scan failure rather than reporting an empty library."""
    raise error


@books.after_request
def no_store(response):
    """Keep the book catalog and files out of shared and persistent HTTP caches."""
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Robots-Tag"] = "noindex"
    return response


@books.get("/")
def catalog():
    """List PDFs in title order with catalog-derived filter options."""
    root = library_root()
    metadata = read_metadata()
    by_path = {}
    try:
        for folder, dirs, files in root.walk(on_error=scan_error):
            dirs[:] = [name for name in dirs if not name.startswith((".", "@", "#"))]
            directory = folder.relative_to(root)
            for filename in files:
                relative = (directory / filename).as_posix()
                if pdf_path(root, relative):
                    by_path[relative] = build_book(relative, metadata)
    except OSError:
        abort(503, "The book library is currently unavailable.")

    entries = sorted(
        by_path.values(), key=lambda book: (book.title.casefold(), book.path)
    )
    folders = {book.folder: book.folder_label for book in entries}
    topics = {}
    topic_counts = {}
    # Use metadata order for spelling, ignoring stale entries for PDFs no longer here.
    for path in metadata:
        if path in by_path:
            for key, label in by_path[path].tags.items():
                topics.setdefault(key, label)
                topic_counts[key] = topic_counts.get(key, 0) + 1
    untagged_count = sum(not book.tags for book in entries) if topics else 0

    layout = current_app.extensions["onboard_layout"]
    if layout.is_modified():
        layout.reload()
    return render_template(
        "index.html",
        layout=layout,
        books_entries=entries,
        book_folders=sorted(
            folders.items(), key=lambda item: (item[1].casefold(), item[0])
        ),
        book_topics=topics,
        book_topic_counts=topic_counts,
        books_untagged_count=untagged_count,
    )


@books.get("/cover/<name>")
def cover(name: str):
    """Serve a private local thumbnail through the Books access boundary."""
    if not current_app.config.get("ONBOARD_BOOKS_ROOT"):
        abort(404)
    path = cover_path(name)
    if path is None:
        abort(404)
    try:
        return send_file(path, mimetype="image/jpeg")
    except FileNotFoundError:
        abort(404)
    except OSError:
        abort(503, "The cover is currently unavailable.")


@books.get("/pdf/<path:relative>")
def open_pdf(relative: str):
    """Serve a book inline, with HTTP range support for the browser viewer."""
    path = pdf_path(library_root(), relative)
    if path is None:
        abort(404)
    try:
        return send_file(path, mimetype="application/pdf", conditional=True)
    except FileNotFoundError:
        abort(404)
    except OSError:
        abort(503, "The book is currently unavailable.")
