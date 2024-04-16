from models.utils import from_list

class Row:
	columns: list['Column'] = []
 
	@staticmethod
	def from_dict(dictionary: dict) -> 'Row':
		from models.column import Column
		row = Row()
		if 'columns' in dictionary:
			row.columns = from_list(Column.from_dict, dictionary['columns'])
		return row