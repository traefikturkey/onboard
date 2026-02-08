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
