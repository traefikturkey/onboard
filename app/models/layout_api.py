"""Pydantic models for layout API request/response validation."""

import ipaddress
import re
from typing import List
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator


# YAML metacharacters that could enable injection when used at start of value
_YAML_META_CHARS = set("{}[]&*!|>%@`")


def _validate_safe_name(v: str) -> str:
    """Reject names containing control characters, newlines, or YAML metacharacters."""
    if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", v):
        raise ValueError("Name contains invalid control characters")
    if "\n" in v or "\r" in v:
        raise ValueError("Name must not contain newlines")
    if v and v[0] in _YAML_META_CHARS:
        raise ValueError(f"Name must not start with '{v[0]}'")
    return v


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
        v = v.strip()
        return _validate_safe_name(v)


class AddWidgetRequest(BaseModel):
    """Request model for adding a feed widget to a tab."""

    tab: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1, max_length=200)
    feed_url: str = Field(...)
    link: str = ""
    col_index: int = Field(default=0, ge=0)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Widget name cannot be empty")
        v = v.strip()
        return _validate_safe_name(v)

    @field_validator("feed_url")
    @classmethod
    def validate_feed_url(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Feed URL cannot be empty")
        v = v.strip()
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("Feed URL must start with http:// or https://")
        parsed = urlparse(v)
        hostname = parsed.hostname or ""
        if not hostname:
            raise ValueError("Feed URL must have a valid hostname")
        # Block localhost and loopback
        blocked_hosts = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}
        if hostname.lower() in blocked_hosts:
            raise ValueError("Feed URL must not point to localhost")
        # Block private/reserved IPs
        try:
            addr = ipaddress.ip_address(hostname)
            if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved:
                raise ValueError("Feed URL must not point to a private or reserved address")
        except ValueError as exc:
            # Not a raw IP — that's fine (it's a domain name)
            if "must not point" in str(exc):
                raise
        # Block cloud metadata endpoint
        if hostname == "169.254.169.254":
            raise ValueError("Feed URL must not point to a private or reserved address")
        return v


class MoveWidgetRequest(BaseModel):
    """Request model for moving a widget between tabs."""

    widget_id: str = Field(..., min_length=1)
    source_tab: str = Field(..., min_length=1)
    dest_tab: str = Field(..., min_length=1)
    dest_col_index: int = Field(default=0, ge=0)


class AddRowRequest(BaseModel):
    """Request model for adding a new row to a tab."""

    tab: str = Field(..., min_length=1)
    num_columns: int = Field(default=3, ge=1, le=12)

    @field_validator("tab")
    @classmethod
    def validate_tab(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Tab name cannot be empty")
        return v.strip()
