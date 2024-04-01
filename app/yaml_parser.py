
import os
from file_data import FileData
import yaml
# from types import SimpleNamespace
# from yamlpath.common import Parsers
# from yamlpath.wrappers import ConsolePrinter
# from yamlpath import Processor
# from yamlpath import YAMLPath
# from yamlpath.exceptions import YAMLPathException

class YamlParser:
	def __init__(self):
		self.file_cache = {}
		self.pwd = os.path.dirname(os.path.realpath(__file__))
		self.layout = os.path.join(self.pwd, "configs/layout.yml")

	# 	logging_args = SimpleNamespace(quiet=True, verbose=False, debug=False)
	# 	log = ConsolePrinter(logging_args)
	# 	parser = Parsers.get_yaml_editor()

	# 	# At this point, you'd load or parse your YAML file, stream, or string.  This
	# 	# example demonstrates loading YAML data from an external file.  You could also
	# 	# use the same function to load data from STDIN or even a String variable.  See
	# 	# the Parser class for more detail.
	# 	(yaml_data, doc_loaded) = Parsers.get_yaml_data(parser, log, self.layout)
	# 	if not doc_loaded:
	# 			# There was an issue loading the file; an error message has already been
	# 			# printed via ConsolePrinter.
	# 			exit(1)

	# 	# Pass the logging facility and parsed YAML data to the YAMLPath Processor
	# 	self.processor = Processor(log, yaml_data)

	# def find_widget(self, widget_name):
	# 	yaml_path = YAMLPath(f"/tabs/*/widgets[name = '{widget_name}']")

	# 	try:
	# 		for node in self.processor.get_nodes(yaml_path, return_coordinates=True, return_node=True, mustexist=True):
	# 			return node.node
	# 	except YAMLPathException as ex:
	# 			print(ex)
		
	# 	return None
				

	def load_layout(self):
		file_path = self.layout

		# Check the last modification time of the file
		current_modified_time = os.path.getmtime(file_path)

		# Only load the file if it has been modified since the last check or if there is no value for that file in the dict
		if current_modified_time > self.file_cache.get(file_path, FileData()).last_modified or file_path not in self.file_cache:
				with open(file_path, 'r') as file:
						contents = yaml.safe_load(file)
				self.file_cache[file_path] = FileData(current_modified_time, contents)

		return self.file_cache[file_path].contents

yaml_parser = YamlParser()