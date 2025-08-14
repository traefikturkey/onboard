import unittest

from app.models.noop_feed_processor import NoOpFeedProcessor


class TestNoOpFeedProcessor(unittest.TestCase):
    def test_process_returns_same_feed(self):
        processor = NoOpFeedProcessor()
        feed = object()
        result = processor.process(feed)
        self.assertIs(result, feed)
