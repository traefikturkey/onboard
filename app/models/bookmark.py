from models.widget_item import WidgetItem

class Bookmark(WidgetItem):
	from models.widget import Widget
	
	def __init__(self, name: str, link: str, parent: Widget) -> None:
		super().__init__(name, link, parent)