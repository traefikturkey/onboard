
from models.utils import from_list

class Column:
	rows: list['Row'] = []
	widgets: list['Widget'] = []
 
	@property
	def has_rows(self) -> bool:
		return len(self.rows) > 0

	@staticmethod
	def from_dict(dictionary: dict) -> 'Column':
		from models.row import Row
		from models.widget import Widget
		column = Column()
		if 'rows' in dictionary:
			column.rows = from_list(Row.from_dict, dictionary['rows'])
		if	'widgets' in dictionary:
			column.widgets = from_list(Widget.from_dict, dictionary['widgets'])
		return column
