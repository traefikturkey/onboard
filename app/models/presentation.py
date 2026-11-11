"""Validated presentation settings shared by layout models and templates."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

CssLength = Annotated[
    str,
    Field(pattern=r"^(?:0|(?:\d+(?:\.\d+)?|\.\d+)(?:px|rem|em|vh|vw|%))$"),
]
CssColor = Annotated[
    str,
    Field(
        pattern=r"^(?:#[0-9a-fA-F]{3}|#[0-9a-fA-F]{4}|#[0-9a-fA-F]{6}|#[0-9a-fA-F]{8}|transparent|currentColor)$"
    ),
]


def favicon_url(value: str | None) -> str | None:
    if value and not value.startswith(("/", "http://", "https://")):
        return "/static/img/" + value
    return value


class UISettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    header_icon_size: CssLength | None = None
    header_icon_gap: CssLength | None = None
    header_link_padding_x: CssLength | None = None
    header_link_padding_y: CssLength | None = None
    header_background: CssColor | None = None
    header_link_background: CssColor | None = None
    header_link_hover_background: CssColor | None = None
    header_text_color: CssColor | None = None
    page_background: CssColor | None = None
    text_color: CssColor | None = None
    link_color: CssColor | None = None
    link_hover_color: CssColor | None = None
    visited_link_color: CssColor | None = None
    bookmark_link_color: CssColor | None = None
    widget_header_background: CssColor | None = None
    widget_padding: CssLength | None = None
    list_item_margin: CssLength | None = None
    list_item_padding_bottom: CssLength | None = None
    feed_height: CssLength | None = None

    @property
    def css_variables(self) -> dict[str, str]:
        return {
            "--" + key.replace("_", "-"): value
            for key, value in self.model_dump(exclude_none=True).items()
        }


class BookmarkPresentation(BaseModel):
    favicon: str | None = None
    bookmarks_section: str | None = Field(None, min_length=1)
    multiColumn: int = Field(2, ge=1, le=10, strict=True)
    hover_delay_ms: int = Field(2000, ge=0, le=60000, strict=True)
    openInNewTab: bool = True


class ColumnPresentation(BaseModel):
    flex: float = Field(1, gt=0, allow_inf_nan=False, strict=True)


class BookmarkListPresentation(BaseModel):
    columns: int = Field(1, ge=1, le=10, strict=True)
    show_favicons: bool = False
