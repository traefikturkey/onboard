import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.models.layout import Layout
from app.models.noop_feed_processor import NoOpFeedProcessor

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


class TestNoOpFeedProcessor(unittest.TestCase):
  def test_process_returns_same_feed(self):
    processor = NoOpFeedProcessor()
    feed = object()
    result = processor.process(feed)
    self.assertIs(result, feed)

  def make_layout(self):
