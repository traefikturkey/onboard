class FileData:
	def __init__(self, last_modified=0, contents=None):
		self.last_modified = last_modified
		self.contents = contents

	def __getitem__(self, key, default=None):
		return self.contents.get(key, default)