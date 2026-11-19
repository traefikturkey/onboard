"""Read optional, operator-managed display metadata for the PDF catalog."""

import json
import re
from pathlib import Path
from typing import NamedTuple

from flask import current_app

COVER_NAME = re.compile(r"[0-9a-f]{64}\.jpg")
DATE = re.compile(r"[0-9]{4}(?:-[0-9]{2}-[0-9]{2})?")
DEFAULT_METADATA = Path(__file__).parent / "configs" / "books.json"


class Book(NamedTuple):
    """A catalog entry with an unchanged PDF URL and optional details."""

    path: str
    title: str
    subtitle: str
    authors: list[str]
    date: str
    edition: str
    summary: str
    cover: str
    tags: dict[str, str]

    @property
    def folder(self) -> str:
        return self.path.rpartition("/")[0] or "."

    @property
    def folder_label(self) -> str:
        if self.folder == ".":
            return "Unsorted"
        return " / ".join(part.replace("_", " ") for part in self.folder.split("/"))


def metadata_path() -> Path:
    """Use the instance's private metadata file by default."""
    return Path(current_app.config.get("ONBOARD_BOOKS_METADATA") or DEFAULT_METADATA)


def read_metadata() -> dict:
    """Missing or invalid metadata must not disable PDF browsing."""
    try:
        raw = json.loads(metadata_path().read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        return {}
    except OSError, ValueError:
        current_app.logger.warning("Could not read the optional books metadata file")
        return {}
    if not isinstance(raw, dict):
        current_app.logger.warning("Books metadata must be an object keyed by PDF path")
        return {}
    return raw


def clean_text(value: object) -> str:
    """Normalize spacing in a string without interpreting it as markup."""
    if not isinstance(value, str):
        return ""
    return " ".join(
        "".join(char for char in value if not 0xD800 <= ord(char) <= 0xDFFF).split()
    )


def build_book(relative: str, metadata: dict) -> Book:
    """Merge the existing PDF entry with its curated display fields."""
    entry = metadata.get(relative)
    if not isinstance(entry, dict):
        entry = {}
    fallback = Path(relative).stem.removeprefix("_OceanofPDF.com_").replace("_", " ")
    authors = entry.get("authors")
    cover = clean_text(entry.get("cover"))
    date = clean_text(entry.get("date"))
    tags = {}
    if isinstance(entry.get("tags"), list):
        for value in entry["tags"]:
            if tag := clean_text(value):
                tags.setdefault(tag.casefold(), tag)
    return Book(
        relative,
        clean_text(entry.get("title")) or clean_text(fallback) or Path(relative).name,
        clean_text(entry.get("subtitle")),
        (
            list(filter(None, map(clean_text, authors)))
            if isinstance(authors, list)
            else []
        ),
        date if DATE.fullmatch(date) else "",
        clean_text(entry.get("edition")),
        clean_text(entry.get("summary")),
        cover if COVER_NAME.fullmatch(cover) and cover_path(cover) else "",
        tags,
    )


def cover_path(name: str) -> Path | None:
    """Return one JPEG thumbnail from the private covers folder, not a symlink."""
    if not COVER_NAME.fullmatch(name):
        return None
    try:
        path = metadata_path().parent.resolve(strict=True) / "book-covers" / name
        if path.resolve(strict=True) == path and path.is_file():
            return path
    except OSError:
        pass
    return None
