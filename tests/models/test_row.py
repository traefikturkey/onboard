from unittest.mock import MagicMock, patch

import pytest

from app.models.row import Row


@pytest.fixture
def row_dict_with_columns():
    return {"columns": [{"widgets": ["w1", "w2"]}, {"widgets": ["w3"]}]}


@pytest.fixture
def row_dict_with_widgets():
    return {"widgets": ["w1", "w2", "w3"]}


def test_from_dict_with_columns(row_dict_with_columns):
    mock_column = MagicMock()
    with patch(
        "app.models.row.column.Column.from_dict", return_value=mock_column
    ) as mock_column_from_dict:
        row = Row.from_dict(row_dict_with_columns)
        assert isinstance(row, Row)
        assert row.columns == [mock_column, mock_column]
        # Verify from_dict was called for each column with bookmark_manager=None
        assert mock_column_from_dict.call_count == 2
        mock_column_from_dict.assert_any_call(
            row_dict_with_columns["columns"][0], bookmark_manager=None
        )
        mock_column_from_dict.assert_any_call(
            row_dict_with_columns["columns"][1], bookmark_manager=None
        )


def test_from_dict_with_widgets(row_dict_with_widgets):
    mock_widget = MagicMock()
    mock_column = MagicMock()
    with (
        patch(
            "app.models.row.widget.Widget.from_dict", return_value=mock_widget
        ) as mock_widget_from_dict,
        patch(
            "app.models.row.column.Column", return_value=mock_column
        ) as mock_column_class,
    ):
        row = Row.from_dict(row_dict_with_widgets)
        assert isinstance(row, Row)
        assert row.columns == [mock_column]
        mock_column.widgets = [mock_widget, mock_widget, mock_widget]
        # Verify from_dict was called for each widget with bookmark_manager=None
        assert mock_widget_from_dict.call_count == 3
        for widget_data in row_dict_with_widgets["widgets"]:
            mock_widget_from_dict.assert_any_call(widget_data, bookmark_manager=None)
        mock_column_class.assert_called_once()
