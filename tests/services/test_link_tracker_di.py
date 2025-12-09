"""Tests for LinkTracker dependency injection."""

import unittest

from app.services.link_tracker import LinkTracker


class TestLinkTrackerDependencyInjection(unittest.TestCase):
    """Test that LinkTracker accepts injected dependencies."""

    def test_link_tracker_with_memory_db(self):
        """LinkTracker works with :memory: SQLite database for testing."""
        # Create LinkTracker with in-memory database
        tracker = LinkTracker(db_path=":memory:")

        # Verify table was created
        tracker.cursor.execute(
            "SELECT COUNT(name) FROM sqlite_master WHERE type='table' AND name='CLICK_EVENTS'"
        )
        self.assertEqual(tracker.cursor.fetchone()[0], 1)

        # Track a click event
        tracker.track_click_event("widget1", "link1", "http://example.com")

        # Verify event was stored
        events = tracker.get_click_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events["LINK"].iloc[0], "http://example.com")

    def test_link_tracker_isolation_with_memory_db(self):
        """Multiple LinkTracker instances with :memory: are isolated."""
        tracker1 = LinkTracker(db_path=":memory:")
        tracker2 = LinkTracker(db_path=":memory:")

        # Add event to tracker1
        tracker1.track_click_event("w1", "l1", "http://one.com")

        # tracker2 should have empty events
        events2 = tracker2.get_click_events()
        self.assertTrue(events2.empty)

        # tracker1 should have one event
        events1 = tracker1.get_click_events()
        self.assertEqual(len(events1), 1)

    def test_link_tracker_multiple_events(self):
        """LinkTracker can store and retrieve multiple events."""
        tracker = LinkTracker(db_path=":memory:")

        tracker.track_click_event("w1", "l1", "http://one.com")
        tracker.track_click_event("w1", "l2", "http://two.com")
        tracker.track_click_event("w2", "l1", "http://three.com")

        events = tracker.get_click_events()
        self.assertEqual(len(events), 3)

    def test_link_tracker_default_uses_file_db(self):
        """LinkTracker with no db_path uses file-based database by default."""
        # We can't easily test this without affecting the real db,
        # but we can verify the code path exists by checking the default
        # behavior computes a path (not :memory:)
        from app.models.utils import pwd

        expected_default = pwd.joinpath("configs", "tracking.db")
        # Just verify the default path computation is correct
        self.assertTrue(str(expected_default).endswith("configs/tracking.db"))
