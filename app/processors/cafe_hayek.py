# cafe_hayek.py
import re


class CafeHayek:
	def process(self, widget):
		for article in widget['articles'][:]:
			article['summary'] = re.sub(r'^Tweet\s*\.{0,3}|\…\s+', '', article['summary'])
			
		return widget
