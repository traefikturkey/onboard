import os
import sys
import unittest
from unittest.mock import MagicMock, patch

from app.models.tab import Tab

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


class TestTab(unittest.TestCase):
    def test_tab_default(self):
        """Test Tab default initialization"""
        tab = Tab()
        self.assertEqual(tab.name, "")
        self.assertEqual(tab.rows, [])

    @patch("app.models.row.Row")
    def test_from_dict_with_rows(self, mock_row_class):
        """Test Tab.from_dict when dictionary contains 'rows' key"""
        # Setup mocks
        mock_row_instance = MagicMock()
        mock_row_class.from_dict = MagicMock(return_value=mock_row_instance)

        dictionary = {"tab": "TestTab", "rows": ["row1", "row2"]}

        # Execute
        tab = Tab.from_dict(dictionary)

        # Verify
        self.assertEqual(tab.name, "TestTab")
        self.assertEqual(len(tab.rows), 2)
        self.assertEqual(tab.rows, [mock_row_instance, mock_row_instance])
        # Verify from_dict was called for each row with bookmark_manager=None
        assert mock_row_class.from_dict.call_count == 2
        mock_row_class.from_dict.assert_any_call(
            dictionary["rows"][0], bookmark_manager=None
        )
        mock_row_class.from_dict.assert_any_call(
            dictionary["rows"][1], bookmark_manager=None
        )

    @patch("app.models.row.Row")
    @patch("app.models.column.Column")
    def test_from_dict_with_columns(self, mock_column_class, mock_row_class):
        """Test Tab.from_dict when dictionary contains 'columns' key (creates single row with columns)"""
        # Setup mocks
        mock_column_instance = MagicMock()
        mock_column_class.from_dict = MagicMock(return_value=mock_column_instance)

        mock_row_instance = MagicMock()
        mock_row_class.return_value = mock_row_instance

        dictionary = {"tab": "TestTab", "columns": ["col1", "col2"]}

        # Execute
        tab = Tab.from_dict(dictionary)

        # Verify
        self.assertEqual(tab.name, "TestTab")
        self.assertEqual(len(tab.rows), 1)
        self.assertEqual(tab.rows[0], mock_row_instance)
        # Verify that row.columns was set
        self.assertEqual(
            mock_row_instance.columns, [mock_column_instance, mock_column_instance]
        )
        # Verify from_dict was called for each column with bookmark_manager=None
        assert mock_column_class.from_dict.call_count == 2
        mock_column_class.from_dict.assert_any_call(
            dictionary["columns"][0], bookmark_manager=None
        )
        mock_column_class.from_dict.assert_any_call(
            dictionary["columns"][1], bookmark_manager=None
        )

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

    @patch("app.models.row.Row")
    def test_from_dict_empty_rows(self, mock_row_class):
        """Test Tab.from_dict with empty rows list"""
        dictionary = {"tab": "EmptyTab", "rows": []}

        tab = Tab.from_dict(dictionary)

        self.assertEqual(tab.name, "EmptyTab")
        self.assertEqual(tab.rows, [])
        # Verify from_dict was not called since rows list is empty
        mock_row_class.from_dict.assert_not_called()

    @patch("app.models.row.Row")
    @patch("app.models.column.Column")
    def test_from_dict_empty_columns(self, mock_column_class, mock_row_class):
        """Test Tab.from_dict with empty columns list"""
        mock_row_instance = MagicMock()
        mock_row_class.return_value = mock_row_instance

        dictionary = {"tab": "EmptyColTab", "columns": []}

        tab = Tab.from_dict(dictionary)

        self.assertEqual(tab.name, "EmptyColTab")
        self.assertEqual(len(tab.rows), 1)
        self.assertEqual(tab.rows[0], mock_row_instance)
        self.assertEqual(mock_row_instance.columns, [])
        # Verify from_dict was not called since columns list is empty
        mock_column_class.from_dict.assert_not_called()


if __name__ == "__main__":
    unittest.main()
