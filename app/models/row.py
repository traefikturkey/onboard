from models.utils import from_list


class Row:
	columns: list['Column'] = []
 
	@staticmethod
	def from_dict(dictionary: dict) -> 'Row':
		from models.column import Column
		from models.widget import Widget
		row = Row()
		if 'columns' in dictionary:
			row.columns = from_list(Column.from_dict, dictionary['columns'])
		else:
			column = Column()
			column.widgets = from_list(Widget.from_dict, dictionary['widgets'])
			row.columns = [column]
		return row