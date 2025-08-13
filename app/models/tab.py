from .row import Row  # Import Row for type hinting
from .utils import from_list


class Tab:
    name: str = ""
    rows: list["Row"] = []

    @staticmethod
    def from_dict(dictionary: dict) -> "Tab":
        from .column import Column
        from .row import Row

        tab = Tab()
        tab.name = dictionary["tab"]
        if "rows" in dictionary:
            tab.rows = from_list(Row.from_dict, dictionary["rows"])
        else:
            row = Row()
            row.columns = from_list(Column.from_dict, dictionary["columns"])
            tab.rows = [row]
        return tab
