from .widget_item import WidgetItem


class Bookmark(WidgetItem):
  @staticmethod
  def from_dict(*args) -> "Bookmark":
    # Accept either (dict, parent) or ((dict, parent),)
    if len(args) == 1 and isinstance(args[0], tuple) and len(args[0]) == 2:
      dictionary, parent = args[0]
    elif len(args) == 2:
      dictionary, parent = args
    else:
      raise TypeError("from_dict expects (dict, parent) or ((dict, parent),)")
    name = dictionary.get("name")
    link = dictionary.get("link")
    return Bookmark(name, link, parent)
  from .widget import Widget

  def __init__(self, name: str, link: str, parent: Widget) -> None:
    super().__init__(name, link, parent)
