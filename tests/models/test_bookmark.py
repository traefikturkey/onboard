from app.models.bookmark import Bookmark
import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


class MockWidget:
  def __init__(self):
    self.id = 'parent123'


class TestBookmark(unittest.TestCase):
  def test_bookmark_creation(self):
    parent = MockWidget()
    bookmark = Bookmark(name='Example', link='https://example.com', parent=parent)
    self.assertEqual(bookmark.name, 'Example')
    self.assertEqual(bookmark.link, 'https://example.com')
    self.assertEqual(bookmark.parent.id, 'parent123')

  def test_from_dict_with_two_args(self):
    """Test from_dict static method with (dict, parent) format"""
    parent = MockWidget()
    bookmark_dict = {
      "name": "Test Bookmark",
      "link": "https://test.com"
    }

    bookmark = Bookmark.from_dict(bookmark_dict, parent)

    self.assertEqual(bookmark.name, "Test Bookmark")
    self.assertEqual(bookmark.link, "https://test.com")
    self.assertEqual(bookmark.parent.id, "parent123")

  def test_from_dict_with_tuple_arg(self):
    """Test from_dict static method with ((dict, parent),) format"""
    parent = MockWidget()
    bookmark_dict = {
      "name": "Tuple Test",
      "link": "https://tuple-test.com"
    }

    bookmark = Bookmark.from_dict((bookmark_dict, parent))

    self.assertEqual(bookmark.name, "Tuple Test")
    self.assertEqual(bookmark.link, "https://tuple-test.com")
    self.assertEqual(bookmark.parent.id, "parent123")

  def test_from_dict_with_missing_keys(self):
    """Test from_dict handles missing name key gracefully"""
    parent = MockWidget()
    bookmark_dict = {
      "link": "https://test.com"  # Provide link but no name
    }

    bookmark = Bookmark.from_dict(bookmark_dict, parent)

    self.assertIsNone(bookmark.name)  # name will be None from dict.get
    self.assertEqual(bookmark.link, "https://test.com")
    self.assertEqual(bookmark.parent.id, "parent123")

  def test_from_dict_with_partial_data(self):
    """Test from_dict with only some fields provided"""
    parent = MockWidget()
    bookmark_dict = {
      "link": "https://only-link.com"  # Provide link but no name
    }

    bookmark = Bookmark.from_dict(bookmark_dict, parent)

    self.assertIsNone(bookmark.name)
    self.assertEqual(bookmark.link, "https://only-link.com")
    self.assertEqual(bookmark.parent.id, "parent123")

  def test_from_dict_invalid_args_count(self):
    """Test from_dict raises TypeError with invalid arguments"""
    parent = MockWidget()
    bookmark_dict = {"name": "Test", "link": "https://test.com"}

    # Test with no arguments
    with self.assertRaises(TypeError) as context:
      Bookmark.from_dict()
    self.assertIn("from_dict expects (dict, parent) or ((dict, parent),)", str(context.exception))

    # Test with three arguments
    with self.assertRaises(TypeError) as context:
      Bookmark.from_dict(bookmark_dict, parent, "extra")
    self.assertIn("from_dict expects (dict, parent) or ((dict, parent),)", str(context.exception))

  def test_from_dict_invalid_tuple_format(self):
    """Test from_dict raises TypeError with invalid tuple format"""
    # Test with single argument that's not a valid tuple
    with self.assertRaises(TypeError) as context:
      Bookmark.from_dict("not a tuple")
    self.assertIn("from_dict expects (dict, parent) or ((dict, parent),)", str(context.exception))

    # Test with tuple that has wrong length
    with self.assertRaises(TypeError) as context:
      Bookmark.from_dict(("only one element",))
    self.assertIn("from_dict expects (dict, parent) or ((dict, parent),)", str(context.exception))


if __name__ == '__main__':
  unittest.main()

if __name__ == '__main__':
  unittest.main()
