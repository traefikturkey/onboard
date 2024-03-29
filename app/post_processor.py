import importlib
import re
import os

class NoOpClass:
	def process(self, data):
		return data

class PostProcessor:
	def __init__(self):
		self.loaded_classes = {}

	def to_snake_case(self, input_string):
		# Replace non-alphanumeric characters and apostrophes with spaces and split the string into words
		words = re.findall(r"[a-zA-Z0-9]+(?:'[a-zA-Z0-9]+)?", input_string)

		# Remove apostrophes from the words
		words = [word.replace("'", "") for word in words]

		# Convert words to lowercase and join them with underscores
		snake_case_string = '_'.join(word.lower() for word in words)

		return snake_case_string

	def process(self, class_name, data):
		class_name = self.to_snake_case(class_name)
		# Check if the class has already been loaded
		if class_name in self.loaded_classes:
			instance = self.loaded_classes[class_name]
		else:
			# Construct file path to the "processors" subdirectory
			file_path = os.path.join("processors", class_name + ".py")
			if os.path.exists(file_path):
				module = importlib.import_module(f"processors.{class_name}")
				cls = getattr(module, ''.join(word.title() for word in class_name.split('_')))
				instance = cls()
			else:
				instance = NoOpClass()

			self.loaded_classes[class_name] = instance

		# Call process() method of the instance with the provided data
		result = instance.process(data)
		return result

# Instantiate loader when the module is imported
post_processor = PostProcessor()
