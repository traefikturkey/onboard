from models.utils import from_list
import models.column
import models.widget

class Row:
	columns: list['models.column.Column'] = []
 
	@staticmethod
	def from_dict(dictionary: dict) -> 'Row':
		row = Row()
		if 'columns' in dictionary:
			row.columns = from_list(models.column.Column.from_dict, dictionary['columns'])
		else:
			column = models.column.Column()
			column.widgets = from_list(models.widget.Widget.from_dict, dictionary['widgets'])
			row.columns = [column]
		return row