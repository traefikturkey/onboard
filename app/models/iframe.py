from models.widget import Widget

class Iframe(Widget):
	src: str
	
	def __init__(self, widget) -> None:
		super().__init__(widget)
		self.src = widget['src']