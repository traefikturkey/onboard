from . import row, widget
from .utils import from_list


class Column:
    rows: list["row.Row"] = []
    widgets: list["widget.Widget"] = []

    @staticmethod
    def from_dict(dictionary: dict) -> "Column":
        column_obj = Column()
        if "rows" in dictionary:
            column_obj.rows = from_list(row.Row.from_dict, dictionary["rows"])
        if "widgets" in dictionary:
            column_obj.widgets = from_list(
                widget.Widget.from_dict, dictionary["widgets"]
            )
        return column_obj
