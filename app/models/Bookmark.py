class Bookmark:
	name: str
	link: str

	def __init__(self, name: str, link: str) -> None:
		self.name = name
		self.link = link

	@staticmethod
	def from_dict(dictionary: dict) -> 'Bookmark':
		return Bookmark(
			dictionary.get("name"),
			dictionary.get("link"))

	def to_dict(self) -> dict:
		return {
			'name': self.name,
			'link': self.link
		}