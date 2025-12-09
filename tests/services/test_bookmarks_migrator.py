"""Tests for BookmarksMigrator service."""

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from app.services.bookmarks_migrator import (
    BookmarksMigrator,
    CURRENT_SCHEMA_VERSION,
    DirectoryReport,
    MigrationReport,
)


@pytest.fixture
def temp_app_root():
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "defaults").mkdir()
        (root / "configs").mkdir()
        yield root


class TestMigrationReport:
    """Tests for MigrationReport dataclass."""

    def test_changed_true_when_created(self):
        """changed returns True when any directory was created."""
        report = MigrationReport(
            directories=[
                DirectoryReport(
                    scope="defaults",
                    old_bookmarks=Path("/old"),
                    new_bookmarks=Path("/new"),
                    layout=Path("/layout"),
                    created=True,
                    updated=False,
                    skipped=False,
                )
            ]
        )
        assert report.changed is True

    def test_changed_true_when_updated(self):
        """changed returns True when any directory was updated."""
        report = MigrationReport(
            directories=[
                DirectoryReport(
                    scope="defaults",
                    old_bookmarks=Path("/old"),
                    new_bookmarks=Path("/new"),
                    layout=Path("/layout"),
                    created=False,
                    updated=True,
                    skipped=False,
                )
            ]
        )
        assert report.changed is True

    def test_changed_false_when_all_skipped(self):
        """changed returns False when all directories were skipped."""
        report = MigrationReport(
            directories=[
                DirectoryReport(
                    scope="defaults",
                    old_bookmarks=Path("/old"),
                    new_bookmarks=Path("/new"),
                    layout=Path("/layout"),
                    created=False,
                    updated=False,
                    skipped=True,
                    reason="already up to date",
                )
            ]
        )
        assert report.changed is False


class TestBookmarksMigratorInit:
    """Tests for BookmarksMigrator initialization."""

    def test_default_parameters(self, temp_app_root):
        """Test migrator with default parameters."""
        migrator = BookmarksMigrator(temp_app_root)
        assert migrator.layout_filename == "layout.yml"
        assert migrator.old_filename == "bookmarks_bar.json"
        assert migrator.new_filename == "bookmarks.json"
        assert migrator.dry_run is False

    def test_custom_parameters(self, temp_app_root):
        """Test migrator with custom parameters."""
        migrator = BookmarksMigrator(
            temp_app_root,
            layout_filename="custom_layout.yml",
            old_filename="custom_old.json",
            new_filename="custom_new.json",
            dry_run=True,
        )
        assert migrator.layout_filename == "custom_layout.yml"
        assert migrator.old_filename == "custom_old.json"
        assert migrator.new_filename == "custom_new.json"
        assert migrator.dry_run is True


class TestMigrateDirectory:
    """Tests for _migrate_directory method."""

    def test_skip_when_schema_version_current(self, temp_app_root):
        """Skip migration when layout already at current schema version."""
        defaults_dir = temp_app_root / "defaults"

        # Create layout with current schema version
        layout = {"schema_version": CURRENT_SCHEMA_VERSION, "tabs": []}
        with open(defaults_dir / "layout.yml", "w") as f:
            yaml.dump(layout, f)

        # Create old bookmarks file
        with open(defaults_dir / "bookmarks_bar.json", "w") as f:
            json.dump([], f)

        migrator = BookmarksMigrator(temp_app_root)
        report = migrator.migrate()

        defaults_report = report.directories[0]
        assert defaults_report.skipped is True
        assert "already at schema version" in defaults_report.reason

    def test_skip_when_legacy_file_missing(self, temp_app_root):
        """Skip migration when legacy bookmarks file is missing."""
        # Don't create any files
        migrator = BookmarksMigrator(temp_app_root)
        report = migrator.migrate()

        defaults_report = report.directories[0]
        assert defaults_report.skipped is True
        assert "missing legacy bookmarks file" in defaults_report.reason

    def test_skip_when_invalid_json(self, temp_app_root):
        """Skip migration when legacy JSON is invalid."""
        defaults_dir = temp_app_root / "defaults"

        # Create invalid JSON
        with open(defaults_dir / "bookmarks_bar.json", "w") as f:
            f.write("not valid json")

        migrator = BookmarksMigrator(temp_app_root)
        report = migrator.migrate()

        defaults_report = report.directories[0]
        assert defaults_report.skipped is True
        assert "invalid legacy bookmarks JSON" in defaults_report.reason

    def test_skip_when_already_up_to_date(self, temp_app_root):
        """Skip migration when new file already matches payload."""
        defaults_dir = temp_app_root / "defaults"

        # Create empty bar
        bar_data = []
        with open(defaults_dir / "bookmarks_bar.json", "w") as f:
            json.dump(bar_data, f)

        # Create matching new file
        payload = {"bar": bar_data, "sections": {}}
        with open(defaults_dir / "bookmarks.json", "w") as f:
            json.dump(payload, f)

        migrator = BookmarksMigrator(temp_app_root)
        report = migrator.migrate()

        defaults_report = report.directories[0]
        assert defaults_report.skipped is True
        assert "already up to date" in defaults_report.reason

    def test_dry_run_mode(self, temp_app_root):
        """Test dry run doesn't write files."""
        defaults_dir = temp_app_root / "defaults"

        # Create legacy file
        with open(defaults_dir / "bookmarks_bar.json", "w") as f:
            json.dump([{"name": "Test", "href": "http://test.com"}], f)

        migrator = BookmarksMigrator(temp_app_root, dry_run=True)
        report = migrator.migrate()

        defaults_report = report.directories[0]
        assert defaults_report.created is True
        assert defaults_report.reason == "dry-run"
        # New file should not be created
        assert not (defaults_dir / "bookmarks.json").exists()

    def test_create_new_bookmarks_file(self, temp_app_root):
        """Test creating new bookmarks file from legacy."""
        defaults_dir = temp_app_root / "defaults"

        # Create legacy file
        bar_data = [{"name": "Google", "href": "https://google.com"}]
        with open(defaults_dir / "bookmarks_bar.json", "w") as f:
            json.dump(bar_data, f)

        migrator = BookmarksMigrator(temp_app_root)
        report = migrator.migrate()

        defaults_report = report.directories[0]
        assert defaults_report.created is True
        assert defaults_report.updated is False
        assert defaults_report.skipped is False

        # Check new file was created
        new_file = defaults_dir / "bookmarks.json"
        assert new_file.exists()
        with open(new_file) as f:
            data = json.load(f)
        assert data["bar"] == bar_data
        assert data["sections"] == {}


class TestExtractSections:
    """Tests for _extract_sections method."""

    def test_extract_sections_from_layout(self, temp_app_root):
        """Test extracting sections from layout with inline bookmarks."""
        defaults_dir = temp_app_root / "defaults"

        layout = {
            "tabs": [
                {
                    "tab": "Main",
                    "rows": [
                        {
                            "columns": [
                                {
                                    "widgets": [
                                        {
                                            "type": "bookmarks",
                                            "name": "Work Links",
                                            "bookmarks": [
                                                {
                                                    "name": "GitHub",
                                                    "link": "https://github.com",
                                                }
                                            ],
                                        }
                                    ]
                                }
                            ]
                        }
                    ],
                }
            ]
        }
        with open(defaults_dir / "layout.yml", "w") as f:
            yaml.dump(layout, f)
        with open(defaults_dir / "bookmarks_bar.json", "w") as f:
            json.dump([], f)

        migrator = BookmarksMigrator(temp_app_root)
        sections = migrator._extract_sections(defaults_dir / "layout.yml")

        assert "work-links" in sections
        assert sections["work-links"]["displayName"] == "Work Links"
        assert len(sections["work-links"]["bookmarks"]) == 1

    def test_empty_sections_when_no_layout(self, temp_app_root):
        """Test returns empty sections when layout doesn't exist."""
        migrator = BookmarksMigrator(temp_app_root)
        sections = migrator._extract_sections(temp_app_root / "nonexistent.yml")
        assert sections == {}

    def test_empty_sections_on_yaml_error(self, temp_app_root):
        """Test returns empty sections on YAML parse error."""
        defaults_dir = temp_app_root / "defaults"
        with open(defaults_dir / "layout.yml", "w") as f:
            f.write("invalid: yaml: content: [[")

        migrator = BookmarksMigrator(temp_app_root)
        sections = migrator._extract_sections(defaults_dir / "layout.yml")
        assert sections == {}


class TestNormaliseBookmark:
    """Tests for _normalise_bookmark static method."""

    def test_normalise_with_link(self):
        """Test normalising bookmark with link field."""
        result = BookmarksMigrator._normalise_bookmark(
            {"name": "Test", "link": "http://test.com"}
        )
        assert result["name"] == "Test"
        assert result["link"] == "http://test.com"

    def test_normalise_with_href(self):
        """Test normalising bookmark with href field (converted to link)."""
        result = BookmarksMigrator._normalise_bookmark(
            {"name": "Test", "href": "http://test.com"}
        )
        assert result["name"] == "Test"
        assert result["link"] == "http://test.com"

    def test_normalise_with_favicon(self):
        """Test normalising bookmark with favicon."""
        result = BookmarksMigrator._normalise_bookmark(
            {"name": "Test", "link": "http://test.com", "favicon": "/icon.png"}
        )
        assert result["favicon"] == "/icon.png"

    def test_normalise_with_add_date(self):
        """Test normalising bookmark with add_date."""
        result = BookmarksMigrator._normalise_bookmark(
            {"name": "Test", "link": "http://test.com", "add_date": "12345"}
        )
        assert result["add_date"] == "12345"

    def test_normalise_non_dict_returns_empty(self):
        """Test normalising non-dict returns empty dict."""
        result = BookmarksMigrator._normalise_bookmark("not a dict")
        assert result == {}

    def test_normalise_empty_dict(self):
        """Test normalising empty dict."""
        result = BookmarksMigrator._normalise_bookmark({})
        assert result == {}


class TestUniqueSlug:
    """Tests for _unique_slug static method."""

    def test_first_slug_is_base(self):
        """First slug uses base without suffix."""
        from collections import defaultdict

        counters = defaultdict(int)
        slug, count = BookmarksMigrator._unique_slug("Work Links", counters)
        assert slug == "work-links"
        assert count == 1

    def test_second_slug_has_suffix(self):
        """Second occurrence gets numbered suffix."""
        from collections import defaultdict

        counters = defaultdict(int)
        BookmarksMigrator._unique_slug("Work", counters)
        slug, count = BookmarksMigrator._unique_slug("Work", counters)
        assert slug == "work-2"
        assert count == 2

    def test_empty_name_defaults_to_section(self):
        """Empty name defaults to 'section'."""
        from collections import defaultdict

        counters = defaultdict(int)
        slug, count = BookmarksMigrator._unique_slug("", counters)
        assert slug == "section"
        assert count == 1


class TestDisplayName:
    """Tests for _display_name static method."""

    def test_display_name_first_occurrence(self):
        """First occurrence shows plain name."""
        result = BookmarksMigrator._display_name("Work", 1)
        assert result == "Work"

    def test_display_name_subsequent_occurrences(self):
        """Subsequent occurrences show name with count."""
        result = BookmarksMigrator._display_name("Work", 2)
        assert result == "Work (2)"


class TestUpdateLayoutWithSections:
    """Tests for _update_layout_with_sections method."""

    def test_update_layout_replaces_inline_bookmarks(self, temp_app_root):
        """Test that inline bookmarks are replaced with section references."""
        defaults_dir = temp_app_root / "defaults"

        layout = {
            "tabs": [
                {
                    "widgets": [
                        {
                            "type": "bookmarks",
                            "name": "Work",
                            "bookmarks": [{"name": "Test", "link": "http://test.com"}],
                        }
                    ]
                }
            ]
        }
        with open(defaults_dir / "layout.yml", "w") as f:
            yaml.dump(layout, f)

        sections = {"work": {"displayName": "Work", "bookmarks": []}}

        migrator = BookmarksMigrator(temp_app_root)
        migrator._update_layout_with_sections(defaults_dir / "layout.yml", sections)

        # Reload and check
        with open(defaults_dir / "layout.yml") as f:
            updated = yaml.safe_load(f)

        widget = updated["tabs"][0]["widgets"][0]
        assert "bookmarks" not in widget
        assert widget["bookmarks_section"] == "work"
        assert updated["schema_version"] == CURRENT_SCHEMA_VERSION

    def test_dry_run_no_update(self, temp_app_root):
        """Test dry run doesn't update layout file."""
        defaults_dir = temp_app_root / "defaults"

        layout = {
            "tabs": [
                {
                    "widgets": [
                        {
                            "type": "bookmarks",
                            "name": "Work",
                            "bookmarks": [{"name": "Test", "link": "http://test.com"}],
                        }
                    ]
                }
            ]
        }
        with open(defaults_dir / "layout.yml", "w") as f:
            yaml.dump(layout, f)

        sections = {"work": {"displayName": "Work", "bookmarks": []}}

        migrator = BookmarksMigrator(temp_app_root, dry_run=True)
        migrator._update_layout_with_sections(defaults_dir / "layout.yml", sections)

        # Reload and check - should still have inline bookmarks
        with open(defaults_dir / "layout.yml") as f:
            original = yaml.safe_load(f)

        widget = original["tabs"][0]["widgets"][0]
        assert "bookmarks" in widget


class TestLayoutHasInlineBookmarks:
    """Tests for _layout_has_inline_bookmarks method."""

    def test_returns_true_for_inline_bookmarks(self, temp_app_root):
        """Returns True when layout has inline bookmarks."""
        defaults_dir = temp_app_root / "defaults"

        layout = {
            "tabs": [
                {
                    "widgets": [
                        {
                            "type": "bookmarks",
                            "name": "Work",
                            "bookmarks": [{"name": "Test", "link": "http://test.com"}],
                        }
                    ]
                }
            ]
        }
        with open(defaults_dir / "layout.yml", "w") as f:
            yaml.dump(layout, f)

        migrator = BookmarksMigrator(temp_app_root)
        assert migrator._layout_has_inline_bookmarks(defaults_dir / "layout.yml") is True

    def test_returns_false_for_section_references(self, temp_app_root):
        """Returns False when layout uses section references."""
        defaults_dir = temp_app_root / "defaults"

        layout = {
            "tabs": [
                {
                    "widgets": [
                        {"type": "bookmarks", "name": "Work", "bookmarks_section": "work"}
                    ]
                }
            ]
        }
        with open(defaults_dir / "layout.yml", "w") as f:
            yaml.dump(layout, f)

        migrator = BookmarksMigrator(temp_app_root)
        assert migrator._layout_has_inline_bookmarks(defaults_dir / "layout.yml") is False

    def test_returns_false_when_file_missing(self, temp_app_root):
        """Returns False when layout file is missing."""
        migrator = BookmarksMigrator(temp_app_root)
        assert (
            migrator._layout_has_inline_bookmarks(temp_app_root / "nonexistent.yml")
            is False
        )


class TestGetLayoutSchemaVersion:
    """Tests for _get_layout_schema_version method."""

    def test_returns_version_from_file(self, temp_app_root):
        """Returns schema_version from layout file."""
        defaults_dir = temp_app_root / "defaults"

        layout = {"schema_version": 5, "tabs": []}
        with open(defaults_dir / "layout.yml", "w") as f:
            yaml.dump(layout, f)

        migrator = BookmarksMigrator(temp_app_root)
        assert migrator._get_layout_schema_version(defaults_dir / "layout.yml") == 5

    def test_returns_1_when_missing(self, temp_app_root):
        """Returns 1 when schema_version not in file."""
        defaults_dir = temp_app_root / "defaults"

        layout = {"tabs": []}
        with open(defaults_dir / "layout.yml", "w") as f:
            yaml.dump(layout, f)

        migrator = BookmarksMigrator(temp_app_root)
        assert migrator._get_layout_schema_version(defaults_dir / "layout.yml") == 1

    def test_returns_1_when_file_missing(self, temp_app_root):
        """Returns 1 when layout file doesn't exist."""
        migrator = BookmarksMigrator(temp_app_root)
        assert migrator._get_layout_schema_version(temp_app_root / "nonexistent.yml") == 1

    def test_returns_1_on_yaml_error(self, temp_app_root):
        """Returns 1 on YAML parse error."""
        defaults_dir = temp_app_root / "defaults"

        with open(defaults_dir / "layout.yml", "w") as f:
            f.write("invalid: yaml: [[")

        migrator = BookmarksMigrator(temp_app_root)
        assert migrator._get_layout_schema_version(defaults_dir / "layout.yml") == 1


class TestFullMigration:
    """Integration tests for full migration flow."""

    def test_migrate_both_directories(self, temp_app_root):
        """Test migration runs on both defaults and configs."""
        # Create files in both directories
        for scope in ("defaults", "configs"):
            scope_dir = temp_app_root / scope
            with open(scope_dir / "bookmarks_bar.json", "w") as f:
                json.dump([{"name": "Test", "href": "http://test.com"}], f)

        migrator = BookmarksMigrator(temp_app_root)
        report = migrator.migrate()

        assert len(report.directories) == 2
        assert report.directories[0].scope == "defaults"
        assert report.directories[1].scope == "configs"

    def test_migration_is_idempotent(self, temp_app_root):
        """Running migration twice produces same result."""
        defaults_dir = temp_app_root / "defaults"

        # Create legacy file with layout
        bar_data = [{"name": "Google", "href": "https://google.com"}]
        with open(defaults_dir / "bookmarks_bar.json", "w") as f:
            json.dump(bar_data, f)

        layout = {
            "tabs": [
                {
                    "widgets": [
                        {
                            "type": "bookmarks",
                            "name": "Work",
                            "bookmarks": [{"name": "Test", "link": "http://test.com"}],
                        }
                    ]
                }
            ]
        }
        with open(defaults_dir / "layout.yml", "w") as f:
            yaml.dump(layout, f)

        migrator = BookmarksMigrator(temp_app_root)

        # First migration
        report1 = migrator.migrate()
        assert report1.changed is True

        # Read first result
        with open(defaults_dir / "bookmarks.json") as f:
            first_result = json.load(f)

        # Second migration - should skip
        report2 = migrator.migrate()
        defaults_report = report2.directories[0]
        assert defaults_report.skipped is True
        # Should be skipped due to schema version, not "already up to date"
        assert "already at schema version" in defaults_report.reason

        # Verify file unchanged
        with open(defaults_dir / "bookmarks.json") as f:
            second_result = json.load(f)
        assert first_result == second_result
