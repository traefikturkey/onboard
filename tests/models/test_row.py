import pytest
from unittest.mock import patch, MagicMock
from app.models.row import Row

@pytest.fixture
def row_dict_with_columns():
    return {
        "columns": [
            {"widgets": ["w1", "w2"]},
            {"widgets": ["w3"]}
        ]
    }

@pytest.fixture
def row_dict_with_widgets():
    return {
        "widgets": ["w1", "w2", "w3"]
    }

def test_from_dict_with_columns(row_dict_with_columns):
    mock_column = MagicMock()
    with patch("app.models.row.column.Column.from_dict", return_value=mock_column) as mock_column_from_dict, \
         patch("app.models.row.from_list", return_value=[mock_column, mock_column]) as mock_from_list:
        row = Row.from_dict(row_dict_with_columns)
        assert isinstance(row, Row)
        assert row.columns == [mock_column, mock_column]
        mock_from_list.assert_called_once_with(mock_column_from_dict, row_dict_with_columns["columns"])

def test_from_dict_with_widgets(row_dict_with_widgets):
    mock_widget = MagicMock()
    mock_column = MagicMock()
    with patch("app.models.row.widget.Widget.from_dict", return_value=mock_widget) as mock_widget_from_dict, \
         patch("app.models.row.from_list", return_value=[mock_widget, mock_widget, mock_widget]) as mock_from_list, \
         patch("app.models.row.column.Column", return_value=mock_column) as mock_column_class:
        row = Row.from_dict(row_dict_with_widgets)
        assert isinstance(row, Row)
        assert row.columns == [mock_column]
        mock_column.widgets = [mock_widget, mock_widget, mock_widget]
        mock_from_list.assert_called_once_with(mock_widget_from_dict, row_dict_with_widgets["widgets"])
        mock_column_class.assert_called_once()
