"""Contract checks for the bookmark manager's browser/API payloads."""

from pathlib import Path

TEMPLATE = Path(__file__).parents[2] / "app" / "templates" / "bookmarks_manager.html"


def test_section_bookmarks_use_link_in_payload_and_display_url():
    template = TEMPLATE.read_text()

    assert "bookmark.href || bookmark.link || 'Click to expand folder'" in template
    assert "bookmark.href: bookmark.href || bookmark.link || ''" not in template
    assert "[this.currentContext === 'bar' ? 'href' : 'link']" in template


def test_section_creation_uses_api_field_and_preserves_id_before_close():
    template = TEMPLATE.read_text()

    assert "section_id: this.sectionForm.id" in template
    assert "const sectionId = this.sectionForm.id;" in template
    assert "this.switchContext(sectionId);" in template


def test_folder_payload_omits_disabled_multicolumn_and_sends_integer_when_enabled():
    template = TEMPLATE.read_text()

    assert "if (this.bookmarkForm.multiColumn)" in template
    assert "Number.isInteger(this.bookmarkForm.multiColumn)" in template
    assert ": 1;" in template
    assert (
        "bookmarkData.multiColumn = this.bookmarkForm.multiColumn || false"
        not in template
    )


def test_editing_section_populates_url_field_from_link():
    template = TEMPLATE.read_text()

    assert "href: bookmark.href || bookmark.link || ''" in template
