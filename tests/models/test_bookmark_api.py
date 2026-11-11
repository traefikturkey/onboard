"""Validation of recursive bar bookmarks and flat imported sections."""

import pytest
from pydantic import ValidationError

from app.models.bookmark_api import FolderItem, ImportBookmarksRequest


def test_recursive_folder_preserves_supported_fields():
    data = {
        "name": "Outer",
        "multiColumn": 2,
        "openInNewTab": True,
        "contents": [
            {
                "name": "Inner",
                "contents": [
                    {
                        "name": "Link",
                        "href": "/local",
                        "favicon": "/icon.ico",
                        "add_date": "123",
                    }
                ],
            }
        ],
    }
    folder = FolderItem.model_validate(data)
    assert isinstance(folder.contents[0], FolderItem)
    assert folder.model_dump(exclude_none=True, exclude_unset=True) == data


def test_nested_folder_rejects_unsafe_url():
    with pytest.raises(ValidationError):
        FolderItem.model_validate(
            {
                "name": "Outer",
                "contents": [
                    {
                        "name": "Inner",
                        "contents": [{"name": "Bad", "href": "javascript:alert(1)"}],
                    }
                ],
            }
        )


@pytest.mark.parametrize(
    "entry",
    [
        {"name": "Folder", "contents": [], "link": "https://example.com"},
        {"name": "No link"},
        {"name": "Empty link", "link": ""},
    ],
)
def test_import_sections_reject_folders_and_linkless_entries(entry):
    with pytest.raises(ValidationError):
        ImportBookmarksRequest.model_validate(
            {
                "data": {
                    "bar": [],
                    "sections": {
                        "links": {"displayName": "Links", "bookmarks": [entry]}
                    },
                }
            }
        )


def test_typed_import_retains_section_metadata():
    data = {
        "bar": [],
        "sections": {
            "links": {
                "displayName": "Links",
                "openInNewTab": True,
                "bookmarks": [
                    {
                        "name": "Example",
                        "link": "https://example.com",
                        "favicon": "/icon.ico",
                        "add_date": "123",
                    }
                ],
            }
        },
    }
    request = ImportBookmarksRequest(data=data)
    assert request.data.model_dump(exclude_none=True, exclude_unset=True) == data
