"""Pydantic models for layout API request/response validation."""

from typing import List

from pydantic import BaseModel, Field, field_validator


class ColumnReorderItem(BaseModel):
    """Model for a single column's widget order."""

    col_key: str = Field(
        ..., description="Column key in format 'row_path.col_index', e.g. '0.0'"
    )
    widget_ids: List[str] = Field(..., description="Ordered list of widget IDs")

    @field_validator("col_key")
    @classmethod
    def validate_col_key(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("col_key cannot be empty")
        return v.strip()


class ReorderWidgetsRequest(BaseModel):
    """Request model for reordering widgets across columns."""

    tab: str = Field(..., min_length=1, description="Tab name")
    columns: List[ColumnReorderItem] = Field(
        ..., min_length=1, description="Column reorder data"
    )

    @field_validator("tab")
    @classmethod
    def validate_tab(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Tab name cannot be empty")
        return v.strip()


class AddTabRequest(BaseModel):
    """Request model for adding a new tab."""

    name: str = Field(..., min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Tab name cannot be empty")
        return v.strip()


class AddWidgetRequest(BaseModel):
    """Request model for adding a feed widget to a tab."""

    tab: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1, max_length=200)
    feed_url: str = Field(...)
    link: str = ""
    col_index: int = Field(default=0, ge=0)

    @field_validator("feed_url")
    @classmethod
    def validate_feed_url(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Feed URL cannot be empty")
        v = v.strip()
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("Feed URL must start with http:// or https://")
        return v


class MoveWidgetRequest(BaseModel):
    """Request model for moving a widget between tabs."""

    widget_id: str = Field(..., min_length=1)
    source_tab: str = Field(..., min_length=1)
    dest_tab: str = Field(..., min_length=1)
    dest_col_index: int = Field(default=0, ge=0)
