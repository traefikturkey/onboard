import yaml
from dataclasses import dataclass, field
from models.utils import from_list
from models.widget import Widget

class Tab:
	name: str = ''
	rows: list['Row'] = []

	@staticmethod
	def from_dict(dictionary: dict) -> 'Tab':
		tab = Tab()
		if 'rows' in dictionary:
			tab.rows = from_list(Row.from_dict, dictionary['rows'])
		else:
			row = Row()
			row.columns = from_list(Column.from_dict, dictionary['columns'])
			tab.rows = [row]
		return tab


class Row:
	columns: list['Column'] = []
 
	@staticmethod
	def from_dict(dictionary: dict) -> 'Row':
		row = Row()
		if 'columns' in dictionary:
			row.columns = from_list(Column.from_dict, dictionary['columns'])
		return row

class Column:
	rows: list['Row'] = []
	widgets: list[Widget] = []
 
	@property
	def has_rows(self) -> bool:
		return len(self.rows) > 0

	@staticmethod
	def from_dict(dictionary: dict) -> 'Column':
		column = Column()
		if 'rows' in dictionary:
			column.rows = from_list(Row.from_dict, dictionary['rows'])
		if	'widgets' in dictionary:
			column.widgets = from_list(Widget.from_dict, dictionary['widgets'])
		return column


class Layout:
	tabs: list[Tab] = field(default_factory=list, init=False)


	def tab(self, name: str):
		return next((tab for tab in self.tabs if tab.name.lower() == name.lower()), self.tabs[0])
 
	@staticmethod
	def load(filename: str):
		layout = Layout()
		with open(filename, 'r') as file:
			contents = yaml.safe_load(file)
			layout.tabs =  from_list(Tab.from_dict, contents.get("tabs"))
   
		return layout
	
