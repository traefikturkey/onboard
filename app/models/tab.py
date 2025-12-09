from .row import Row  # Import Row for type hinting
from .utils import from_list


class Tab:
    def __init__(self):
        self.name: str = ""
        self.rows: list["Row"] = []

    @staticmethod
    def from_dict(dictionary: dict, bookmark_manager=None) -> "Tab":
        from .column import Column
        from .row import Row

        tab = Tab()
        tab.name = dictionary["tab"]
        if "rows" in dictionary:
            tab.rows = [
                Row.from_dict(r, bookmark_manager=bookmark_manager)
                for r in dictionary["rows"]
            ]
        else:
            row = Row()
            row.columns = [
                Column.from_dict(c, bookmark_manager=bookmark_manager)
                for c in dictionary["columns"]
            ]
            tab.rows = [row]
        return tab
