from models.utils import from_list

class Tab:
	name: str = ''
	rows: list['Row'] = []

	@staticmethod
	def from_dict(dictionary: dict) -> 'Tab':
		from models.column import Column
		from models.row import Row
		tab = Tab()
		if 'rows' in dictionary:
			tab.rows = from_list(Row.from_dict, dictionary['rows'])
		else:
			row = Row()
			row.columns = from_list(Column.from_dict, dictionary['columns'])
			tab.rows = [row]
		return tab