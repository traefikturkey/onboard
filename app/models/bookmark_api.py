"""Pydantic models for bookmark API request/response validation."""

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator


class BookmarkItem(BaseModel):
    """Model for a single bookmark."""

    name: str = Field(..., min_length=1, max_length=500, description="Bookmark name")
    href: Optional[str] = Field(None, description="Bookmark URL (for bar bookmarks)")
    link: Optional[str] = Field(
        None, description="Bookmark URL (for section bookmarks)"
    )
    favicon: Optional[str] = Field(None, description="Path to favicon")
    add_date: Optional[str] = Field(None, description="Unix timestamp as string")

    @field_validator("href", "link")
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate URL format."""
        if v is not None and v.strip():
            # Basic URL validation
            if not (
                v.startswith("http://") or v.startswith("https://") or v.startswith("/")
            ):
                raise ValueError("URL must start with http://, https://, or /")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not empty."""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()


class FolderItem(BookmarkItem):
    """Model for a bookmark folder with nested contents."""

    contents: list[dict[str, Any]] = Field(
        default_factory=list, description="Nested bookmarks"
    )
    multiColumn: Optional[int] = Field(
        None, ge=1, le=10, description="Number of columns for display"
    )
    openInNewTab: Optional[bool] = Field(None, description="Open links in new tab")


class SectionBookmarkItem(BaseModel):
    """Model for a bookmark within a section."""

    name: str = Field(..., min_length=1, max_length=500, description="Bookmark name")
    link: str = Field(..., description="Bookmark URL")

    @field_validator("link")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        if not (
            v.startswith("http://") or v.startswith("https://") or v.startswith("/")
        ):
            raise ValueError("URL must start with http://, https://, or /")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not empty."""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()


class SectionData(BaseModel):
    """Model for a bookmark section."""

    displayName: str = Field(
        ..., min_length=1, max_length=200, description="Display name for the section"
    )
    bookmarks: list[SectionBookmarkItem] = Field(
        default_factory=list, description="List of bookmarks in section"
    )

    @field_validator("displayName")
    @classmethod
    def validate_display_name(cls, v: str) -> str:
        """Validate display name is not empty."""
        if not v or not v.strip():
            raise ValueError("Display name cannot be empty")
        return v.strip()


class CreateSectionRequest(BaseModel):
    """Request model for creating a new section."""

    section_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Section identifier (alphanumeric, underscores, hyphens)",
    )
    displayName: str = Field(
        ..., min_length=1, max_length=200, description="Display name for the section"
    )

    @field_validator("section_id")
    @classmethod
    def validate_section_id(cls, v: str) -> str:
        """Validate section ID is alphanumeric with underscores and hyphens only."""
        if not v or not v.strip():
            raise ValueError("Section ID cannot be empty")

        v = v.strip()
        # Allow alphanumeric, underscores, and hyphens
        if not all(c.isalnum() or c in "_-" for c in v):
            raise ValueError(
                "Section ID must contain only alphanumeric characters, underscores, and hyphens"
            )

        return v

    @field_validator("displayName")
    @classmethod
    def validate_display_name(cls, v: str) -> str:
        """Validate display name is not empty."""
        if not v or not v.strip():
            raise ValueError("Display name cannot be empty")
        return v.strip()


class UpdateSectionRequest(BaseModel):
    """Request model for updating a section."""

    displayName: str = Field(
        ..., min_length=1, max_length=200, description="Display name for the section"
    )

    @field_validator("displayName")
    @classmethod
    def validate_display_name(cls, v: str) -> str:
        """Validate display name is not empty."""
        if not v or not v.strip():
            raise ValueError("Display name cannot be empty")
        return v.strip()


class LocationSpec(BaseModel):
    """Model for specifying a bookmark location."""

    type: Literal["bar", "section"] = Field(..., description="Location type")
    section_id: Optional[str] = Field(
        None, description="Section ID (required if type is 'section')"
    )
    index: int = Field(..., ge=0, description="Index position")

    @field_validator("section_id")
    @classmethod
    def validate_section_id_for_type(cls, v: Optional[str], info) -> Optional[str]:
        """Validate section_id is provided when type is 'section'."""
        if info.data.get("type") == "section" and not v:
            raise ValueError("section_id is required when type is 'section'")
        return v


class MoveBookmarkRequest(BaseModel):
    """Request model for moving a bookmark."""

    source: LocationSpec = Field(..., description="Source location")
    destination: LocationSpec = Field(..., description="Destination location")


class ReorderRequest(BaseModel):
    """Request model for reordering bookmarks."""

    indices: list[int] = Field(
        ..., min_length=1, description="New order as list of original indices"
    )

    @field_validator("indices")
    @classmethod
    def validate_indices(cls, v: list[int]) -> list[int]:
        """Validate indices are unique and non-negative."""
        if len(v) != len(set(v)):
            raise ValueError("Indices must be unique")
        if any(i < 0 for i in v):
            raise ValueError("Indices must be non-negative")
        return v


class ImportBookmarksRequest(BaseModel):
    """Request model for importing bookmarks."""

    data: dict[str, Any] = Field(..., description="Bookmark data to import")
    merge: bool = Field(
        False, description="Whether to merge with existing data or replace"
    )


class SuccessResponse(BaseModel):
    """Generic success response."""

    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Generic error response."""

    success: bool = False
    error: str
    details: Optional[str] = None
