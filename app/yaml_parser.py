import os
import yaml
from datetime import datetime, timedelta

class YamlParser:
	def __init__(self):
		self.pwd = os.path.dirname(os.path.realpath(__file__))
		self.layout = os.path.join(self.pwd, "configs/layout.yml")
		self.layout_mtime = os.path.getmtime(self.layout)

	def load_layout(self):
		file_path = self.layout
		with open(file_path, 'r') as file:
				contents = yaml.safe_load(file)
		self.layout_mtime = os.path.getmtime(self.layout)
		return contents

	def is_layout_modified(self):
		result = os.path.getmtime(self.layout) > self.layout_mtime
		print("========== Layout modified: " + str(result))
		return result

yaml_parser = YamlParser()