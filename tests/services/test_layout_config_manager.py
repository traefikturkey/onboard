"""Unit tests for LayoutConfigManager service."""

import pytest
import yaml

from app.models.utils import calculate_sha1_hash


def make_manager(tmp_path, initial_data=None):
    """Helper to create a LayoutConfigManager with optional initial data."""
    config_file = tmp_path / "layout.yml"
    if initial_data is not None:
        with open(config_file, "w") as f:
            yaml.dump(initial_data, f, default_flow_style=False, sort_keys=False)
    from app.services.layout_config_manager import LayoutConfigManager

    return LayoutConfigManager(config_path=str(config_file))


@pytest.fixture
def sample_layout():
    """Sample layout with two tabs for testing."""
    return {
        "schema_version": 2,
        "tabs": [
            {
                "tab": "Home",
                "columns": [
                    {
                        "column": None,
                        "widgets": [
                            {
                                "name": "Test Feed",
                                "type": "feed",
                                "link": "https://example.com",
                                "feed_url": "https://example.com/feed",
                            }
                        ],
                    },
                    {"column": None, "widgets": []},
                ],
            },
            {"tab": "Tech", "columns": [{"column": None, "widgets": []}]},
        ],
    }


class TestGetTabNames:
    """Tests for get_tab_names method."""

    def test_returns_all_tab_names(self, tmp_path, sample_layout):
        """Should return list of all tab names."""
        manager = make_manager(tmp_path, sample_layout)
        names = manager.get_tab_names()

        assert names == ["Home", "Tech"]

    def test_empty_layout(self, tmp_path):
        """Should return empty list when no tabs exist."""
        manager = make_manager(tmp_path, {"schema_version": 2, "tabs": []})
        names = manager.get_tab_names()

        assert names == []


class TestAddTab:
    """Tests for add_tab method."""

    def test_creates_empty_tab_and_persists(self, tmp_path, sample_layout):
        """Should create new tab with empty column and persist to YAML."""
        manager = make_manager(tmp_path, sample_layout)
        result = manager.add_tab("News")

        # Check return value
        assert result["tab"] == "News"
        assert result["columns"] == [{"column": None, "widgets": []}]

        # Verify persisted to disk
        tab_names = manager.get_tab_names()
        assert "News" in tab_names
        assert len(tab_names) == 3

        # Verify YAML structure
        config_file = tmp_path / "layout.yml"
        with open(config_file, "r") as f:
            data = yaml.safe_load(f)
        assert len(data["tabs"]) == 3
        assert data["tabs"][2]["tab"] == "News"

    def test_duplicate_raises_valueerror(self, tmp_path, sample_layout):
        """Should raise ValueError when adding duplicate tab name."""
        manager = make_manager(tmp_path, sample_layout)

        with pytest.raises(ValueError, match="Tab 'Home' already exists"):
            manager.add_tab("Home")

    def test_case_insensitive_uniqueness(self, tmp_path, sample_layout):
        """Should raise ValueError when tab name differs only in case."""
        manager = make_manager(tmp_path, sample_layout)

        with pytest.raises(ValueError, match="Tab 'home' already exists"):
            manager.add_tab("home")

        with pytest.raises(ValueError, match="Tab 'TECH' already exists"):
            manager.add_tab("TECH")


class TestDeleteTab:
    """Tests for delete_tab method."""

    def test_removes_tab(self, tmp_path, sample_layout):
        """Should remove tab from layout."""
        manager = make_manager(tmp_path, sample_layout)
        manager.delete_tab("Tech")

        tab_names = manager.get_tab_names()
        assert "Tech" not in tab_names
        assert tab_names == ["Home"]

        # Verify persisted
        config_file = tmp_path / "layout.yml"
        with open(config_file, "r") as f:
            data = yaml.safe_load(f)
        assert len(data["tabs"]) == 1

    def test_last_tab_raises_valueerror(self, tmp_path):
        """Should raise ValueError when trying to delete the last tab."""
        single_tab = {
            "schema_version": 2,
            "tabs": [{"tab": "Only", "columns": [{"column": None, "widgets": []}]}],
        }
        manager = make_manager(tmp_path, single_tab)

        with pytest.raises(ValueError, match="Cannot delete the last tab"):
            manager.delete_tab("Only")

    def test_nonexistent_raises_valueerror(self, tmp_path, sample_layout):
        """Should raise ValueError when tab not found."""
        manager = make_manager(tmp_path, sample_layout)

        with pytest.raises(ValueError, match="Tab 'NonExistent' not found"):
            manager.delete_tab("NonExistent")


class TestAddWidget:
    """Tests for add_widget method."""

    def test_adds_feed_to_column_and_returns_widget_id(self, tmp_path, sample_layout):
        """Should add widget to column and return computed widget_id."""
        manager = make_manager(tmp_path, sample_layout)

        widget_data = {
            "name": "New Feed",
            "type": "feed",
            "link": "https://newsite.com",
            "feed_url": "https://newsite.com/rss",
        }
        widget_id = manager.add_widget("Tech", widget_data, col_index=0)

        # Check widget_id matches SHA1 hash of link
        expected_id = calculate_sha1_hash("https://newsite.com")
        assert widget_id == expected_id

        # Verify persisted
        config_file = tmp_path / "layout.yml"
        with open(config_file, "r") as f:
            data = yaml.safe_load(f)

        tech_tab = next(t for t in data["tabs"] if t["tab"] == "Tech")
        widgets = tech_tab["columns"][0]["widgets"]
        assert len(widgets) == 1
        assert widgets[0]["name"] == "New Feed"
        assert widgets[0]["link"] == "https://newsite.com"

    def test_nonexistent_tab_raises_valueerror(self, tmp_path, sample_layout):
        """Should raise ValueError if tab not found."""
        manager = make_manager(tmp_path, sample_layout)

        widget_data = {"name": "Test", "type": "feed", "link": "https://test.com"}

        with pytest.raises(ValueError, match="Tab 'Missing' not found"):
            manager.add_widget("Missing", widget_data)

    def test_invalid_col_index_raises_valueerror(self, tmp_path, sample_layout):
        """Should raise ValueError if col_index out of range."""
        manager = make_manager(tmp_path, sample_layout)

        widget_data = {"name": "Test", "type": "feed", "link": "https://test.com"}

        with pytest.raises(ValueError, match="Column index 5 out of range"):
            manager.add_widget("Tech", widget_data, col_index=5)

    def test_widget_id_matches_calculate_sha1_hash(self, tmp_path, sample_layout):
        """Should return widget_id that matches calculate_sha1_hash of link."""
        manager = make_manager(tmp_path, sample_layout)

        test_link = "https://verification-test.com"
        widget_data = {
            "name": "Verification",
            "type": "feed",
            "link": test_link,
        }

        widget_id = manager.add_widget("Home", widget_data, col_index=0)
        expected_id = calculate_sha1_hash(test_link)

        assert widget_id == expected_id


class TestMoveWidget:
    """Tests for move_widget method."""

    def test_moves_widget_between_tabs(self, tmp_path, sample_layout):
        """Should move widget from source tab to destination tab."""
        manager = make_manager(tmp_path, sample_layout)

        # Get widget_id from existing widget in Home tab
        widget_link = "https://example.com"
        widget_id = calculate_sha1_hash(widget_link)

        # Move from Home to Tech
        manager.move_widget(widget_id, "Home", "Tech", dest_col_index=0)

        # Verify persisted
        config_file = tmp_path / "layout.yml"
        with open(config_file, "r") as f:
            data = yaml.safe_load(f)

        home_tab = next(t for t in data["tabs"] if t["tab"] == "Home")
        tech_tab = next(t for t in data["tabs"] if t["tab"] == "Tech")

        # Widget should be removed from Home
        home_widgets = home_tab["columns"][0]["widgets"]
        assert len(home_widgets) == 0

        # Widget should be added to Tech
        tech_widgets = tech_tab["columns"][0]["widgets"]
        assert len(tech_widgets) == 1
        assert tech_widgets[0]["name"] == "Test Feed"
        assert tech_widgets[0]["link"] == widget_link

    def test_widget_not_found_raises_valueerror(self, tmp_path, sample_layout):
        """Should raise ValueError if widget not found in source tab."""
        manager = make_manager(tmp_path, sample_layout)

        fake_id = calculate_sha1_hash("https://nonexistent.com")

        with pytest.raises(ValueError, match=f"Widget '{fake_id}' not found"):
            manager.move_widget(fake_id, "Home", "Tech")

    def test_same_tab_raises_valueerror(self, tmp_path, sample_layout):
        """Should raise ValueError if source and destination tabs are the same."""
        manager = make_manager(tmp_path, sample_layout)

        widget_id = calculate_sha1_hash("https://example.com")

        with pytest.raises(ValueError, match="Source and destination tabs are the same"):
            manager.move_widget(widget_id, "Home", "Home")

    def test_nonexistent_dest_tab_raises_valueerror(self, tmp_path, sample_layout):
        """Should raise ValueError if destination tab not found."""
        manager = make_manager(tmp_path, sample_layout)

        widget_id = calculate_sha1_hash("https://example.com")

        with pytest.raises(ValueError, match="Destination tab 'Missing' not found"):
            manager.move_widget(widget_id, "Home", "Missing")
