from app.models.tab import Tab
import unittest
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


class TestTab(unittest.TestCase):
  def test_tab_default(self):
    """Test Tab default initialization"""
    tab = Tab()
    self.assertEqual(tab.name, "")
    self.assertEqual(tab.rows, [])

  @patch('app.models.tab.from_list')
  @patch('app.models.row.Row')
  def test_from_dict_with_rows(self, mock_row_class, mock_from_list):
    """Test Tab.from_dict when dictionary contains 'rows' key"""
    # Setup mocks
    mock_row_instance = MagicMock()
    mock_row_class.from_dict = MagicMock(return_value=mock_row_instance)

    # Configure from_list to return two row instances
    mock_from_list.return_value = [mock_row_instance, mock_row_instance]

    dictionary = {"tab": "TestTab", "rows": ["row1", "row2"]}

    # Execute
    tab = Tab.from_dict(dictionary)

    # Verify
    self.assertEqual(tab.name, "TestTab")
    self.assertEqual(len(tab.rows), 2)
    self.assertEqual(tab.rows, [mock_row_instance, mock_row_instance])
    mock_from_list.assert_called_once_with(mock_row_class.from_dict, dictionary["rows"])

  @patch('app.models.tab.from_list')
  @patch('app.models.row.Row')
  @patch('app.models.column.Column')
  def test_from_dict_with_columns(self, mock_column_class, mock_row_class, mock_from_list):
    """Test Tab.from_dict when dictionary contains 'columns' key (creates single row with columns)"""
    # Setup mocks
    mock_column_instance = MagicMock()
    mock_column_class.from_dict = MagicMock(return_value=mock_column_instance)

    mock_row_instance = MagicMock()
    mock_row_class.return_value = mock_row_instance

    # Configure from_list to return two column instances
    mock_from_list.return_value = [mock_column_instance, mock_column_instance]

    dictionary = {"tab": "TestTab", "columns": ["col1", "col2"]}

    # Execute
    tab = Tab.from_dict(dictionary)

    # Verify
    self.assertEqual(tab.name, "TestTab")
    self.assertEqual(len(tab.rows), 1)
    self.assertEqual(tab.rows[0], mock_row_instance)
    # Verify that row.columns was set to the result of from_list
    self.assertEqual(mock_row_instance.columns, [mock_column_instance, mock_column_instance])
    mock_from_list.assert_called_once_with(mock_column_class.from_dict, dictionary["columns"])

  def test_from_dict_missing_tab_key(self):
    """Test Tab.from_dict raises KeyError when 'tab' key is missing"""
    dictionary = {"rows": ["row1", "row2"]}

    with self.assertRaises(KeyError):
      Tab.from_dict(dictionary)

  def test_from_dict_empty_dictionary(self):
    """Test Tab.from_dict raises KeyError when dictionary is empty"""
    dictionary = {}

    with self.assertRaises(KeyError):
      Tab.from_dict(dictionary)

  @patch('app.models.tab.from_list')
  @patch('app.models.row.Row')
  def test_from_dict_empty_rows(self, mock_row_class, mock_from_list):
    """Test Tab.from_dict with empty rows list"""
    mock_from_list.return_value = []

    dictionary = {"tab": "EmptyTab", "rows": []}

    tab = Tab.from_dict(dictionary)

    self.assertEqual(tab.name, "EmptyTab")
    self.assertEqual(tab.rows, [])
    mock_from_list.assert_called_once_with(mock_row_class.from_dict, [])

  @patch('app.models.tab.from_list')
  @patch('app.models.row.Row')
  @patch('app.models.column.Column')
  def test_from_dict_empty_columns(self, mock_column_class, mock_row_class, mock_from_list):
    """Test Tab.from_dict with empty columns list"""
    mock_row_instance = MagicMock()
    mock_row_class.return_value = mock_row_instance
    mock_from_list.return_value = []

    dictionary = {"tab": "EmptyColTab", "columns": []}

    tab = Tab.from_dict(dictionary)

    self.assertEqual(tab.name, "EmptyColTab")
    self.assertEqual(len(tab.rows), 1)
    self.assertEqual(tab.rows[0], mock_row_instance)
    self.assertEqual(mock_row_instance.columns, [])
    mock_from_list.assert_called_once_with(mock_column_class.from_dict, [])


if __name__ == '__main__':
  unittest.main()
