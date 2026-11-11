from . import row, widget
from .utils import from_list


class Column:
    def __init__(self):
        self.rows: list["row.Row"] = []
        self.widgets: list["widget.Widget"] = []

    @staticmethod
    def from_dict(dictionary: dict, bookmark_manager=None, scheduler=None) -> "Column":
        column_obj = Column()
        if "rows" in dictionary:
            column_obj.rows = [
                row.Row.from_dict(
                    r, bookmark_manager=bookmark_manager, scheduler=scheduler
                )
                for r in dictionary["rows"]
            ]
        if "widgets" in dictionary:
            column_obj.widgets = [
                widget.Widget.from_dict(
                    w, bookmark_manager=bookmark_manager, scheduler=scheduler
                )
                for w in dictionary["widgets"]
            ]
        return column_obj
