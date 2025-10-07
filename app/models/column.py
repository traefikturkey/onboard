from . import row, widget
from .utils import from_list


class Column:
    rows: list["row.Row"] = []
    widgets: list["widget.Widget"] = []

    @staticmethod
    def from_dict(dictionary: dict, bookmark_manager=None) -> "Column":
        column_obj = Column()
        if "rows" in dictionary:
            column_obj.rows = [
                row.Row.from_dict(r, bookmark_manager=bookmark_manager)
                for r in dictionary["rows"]
            ]
        if "widgets" in dictionary:
            column_obj.widgets = [
                widget.Widget.from_dict(w, bookmark_manager=bookmark_manager)
                for w in dictionary["widgets"]
            ]
        return column_obj
