import models.row
import models.widget
from models.utils import from_list


class Column:
    rows: list["models.row.Row"] = []
    widgets: list["models.widget.Widget"] = []

    @staticmethod
    def from_dict(dictionary: dict) -> "Column":
        column = Column()
        if "rows" in dictionary:
            column.rows = from_list(models.row.Row.from_dict, dictionary["rows"])
        if "widgets" in dictionary:
            column.widgets = from_list(
                models.widget.Widget.from_dict, dictionary["widgets"]
            )
        return column
