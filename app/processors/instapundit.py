import os
import re
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate

class Instapundit:
	def __init__(self):
		ollama_url = os.getenv('OLLAMA_URL')
		if ollama_url:
			_prompt = ChatPromptTemplate.from_messages([
				("human", """
					Title: {title}
					Summary: {summary}
				"""),
				("system", """
					you are and news article title editor that reviews and provides a concise and accurate title when given
					an existing Title and article Summary. 
					Remove all links from the title.
					Title should be as short as possible, aim to be less that 70 characters long.
					Title should have an absolute minimum of punctuation.
					Do your best to keep the existing title if possible.
					DO NOT provide any additional text or thoughts before or after the title.
					DO NOT put notes in parentheses.
					Provide the title only!
					"""),
				])

			_model = Ollama(base_url=ollama_url, model="dolphin-mistral", keep_alive=5, temperature=0.0)

			self.chain = _prompt | _model

	def process(self, widget):
		for article in widget['articles'][:]:
			if '#CommissionEarned' in article['title'] or re.search('Open Thread', article['title'], re.IGNORECASE):
				widget['articles'].remove(article)
				next
			if self.chain:
				title = self.chain.invoke({"title": article['original_title'], "summary": article['original_summary']})
				title = title.strip().strip('""')
				article['title'] = title
			else:
				article['title'] = article['title'].strip().strip('""')

		return widget
