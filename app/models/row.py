from . import column, widget
from .utils import from_list


class Row:
    def __init__(self):
        self.columns: list["column.Column"] = []

    @staticmethod
    def from_dict(dictionary: dict, bookmark_manager=None, scheduler=None) -> "Row":
        row = Row()
        if "columns" in dictionary:
            row.columns = [
                column.Column.from_dict(
                    c, bookmark_manager=bookmark_manager, scheduler=scheduler
                )
                for c in dictionary["columns"]
            ]
        else:
            col = column.Column()
            col.widgets = [
                widget.Widget.from_dict(
                    w, bookmark_manager=bookmark_manager, scheduler=scheduler
                )
                for w in dictionary["widgets"]
            ]
            row.columns = [col]
        return row
