from . import column
from . import widget
from .utils import from_list


class Row:
  columns: list["column.Column"] = []

  @staticmethod
  def from_dict(dictionary: dict) -> "Row":
    row = Row()
    if "columns" in dictionary:
      row.columns = from_list(
        column.Column.from_dict, dictionary["columns"]
      )
    else:
      col = column.Column()
      col.widgets = from_list(
        widget.Widget.from_dict, dictionary["widgets"]
      )
      row.columns = [col]
    return row
