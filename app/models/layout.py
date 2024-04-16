import yaml
from models.utils import from_list

class Layout:
	tabs: list['Tab'] = []

	def tab(self, name: str):
		return next((tab for tab in self.tabs if tab.name.lower() == name.lower()), self.tabs[0])
 
	@staticmethod
	def load(filename: str):
		from models.tab import Tab
		layout = Layout()
		with open(filename, 'r') as file:
			contents = yaml.safe_load(file)
			layout.tabs =  from_list(Tab.from_dict, contents.get("tabs"))
   
		return layout
	
