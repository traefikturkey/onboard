import re


class Instapundit:
	def process(self, widget):
		for article in widget['articles'][:]:
			if '#CommissionEarned' in article['title']:
				widget['articles'].remove(article)
				next
			article['title'] = re.sub(r'http[s]?://\S+', '', article['title'], flags=re.IGNORECASE)

		return widget
