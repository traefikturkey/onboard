import unittest
from unittest.mock import patch, MagicMock
from app.models.widget_item import WidgetItem


class MockWidget:
  def __init__(self):
    self.id = 'parent123'


class TestWidgetItem(unittest.TestCase):
  @patch('app.models.widget_item.calculate_sha1_hash')
  def test_widget_item_creation_and_link(self, mock_hash):
    mock_hash.return_value = 'fakehash'
    parent = MockWidget()
    item = WidgetItem('TestName', 'https://example.com?utm_source=foo&bar=1', parent)
    self.assertEqual(item.name, 'TestName')
    self.assertEqual(item.parent.id, 'parent123')
    self.assertEqual(item.id, 'fakehash')
    self.assertEqual(item.tracking_link, '/redirect/parent123/fakehash')
    # Should clean out utm_source
    self.assertEqual(item.link, 'https://example.com?bar=1')

  def test_to_dict_and_str(self):
    parent = MockWidget()
    item = WidgetItem('TestName', 'https://example.com?foo=bar', parent)
    d = item.to_dict()
    self.assertEqual(d['name'], 'TestName')
    self.assertTrue('link' in d)
    s = str(item)
    self.assertTrue('TestName' in s)
    self.assertTrue('link' in s)

  def test_from_dict_two_args(self):
    parent = MockWidget()
    d = {'name': 'TestName', 'link': 'https://example.com'}
    item = WidgetItem.from_dict(d, parent)
    self.assertEqual(item.name, 'TestName')
    self.assertEqual(item.link, 'https://example.com')
    self.assertEqual(item.parent.id, 'parent123')

  def test_from_dict_tuple_arg(self):
    parent = MockWidget()
    d = {'name': 'TestName', 'link': 'https://example.com'}
    item = WidgetItem.from_dict((d, parent))
    self.assertEqual(item.name, 'TestName')
    self.assertEqual(item.link, 'https://example.com')
    self.assertEqual(item.parent.id, 'parent123')

  def test_from_dict_invalid_args(self):
    with self.assertRaises(TypeError):
      WidgetItem.from_dict({'name': 'TestName'})
    with self.assertRaises(TypeError):
      WidgetItem.from_dict({'name': 'TestName'}, None, 'extra')

  def test_clean_url_removes_tracking(self):
    url = 'https://foo.com?utm_source=bar&_ga=123&vx=456&fbclid=789&bar=1'
    cleaned = WidgetItem.clean_url(url)
    self.assertEqual(cleaned, 'https://foo.com?bar=1')

  def test_clean_url_no_query(self):
    url = 'https://foo.com/path'
    cleaned = WidgetItem.clean_url(url)
    self.assertEqual(cleaned, url)


if __name__ == '__main__':
  unittest.main()
