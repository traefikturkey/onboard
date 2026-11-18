"""Browse a configured, read-only directory of PDFs."""

from pathlib import Path

from flask import Blueprint, abort, current_app, render_template, send_file

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
    if any(not part or part.startswith((".", "@", "#")) for part in parts):
        return None
    if any(char in relative for char in ("\\", ":", "\x00")):
        return None
    if not relative.isprintable() or Path(parts[-1]).suffix.lower() != ".pdf":
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
    """List PDFs in their library folders."""
    root = library_root()
    sections = []
    try:
        for folder, dirs, files in root.walk(on_error=scan_error):
            dirs[:] = sorted(
                (name for name in dirs if not name.startswith((".", "@", "#"))),
                key=str.casefold,
            )
            directory = folder.relative_to(root)
            entries = []
            for filename in sorted(files, key=str.casefold):
                relative = (directory / filename).as_posix()
                if pdf_path(root, relative):
                    entries.append((Path(filename).stem, relative))
            if entries:
                label = " / ".join(part.replace("_", " ") for part in directory.parts)
                sections.append((label or "Unsorted", entries))
    except OSError:
        abort(503, "The book library is currently unavailable.")

    layout = current_app.extensions["onboard_layout"]
    if layout.is_modified():
        layout.reload()
    return render_template("index.html", layout=layout, books_sections=sections)


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
