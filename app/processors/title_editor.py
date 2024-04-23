from datetime import datetime, timedelta
import logging
import os
from pathlib import Path

from pytz import utc
from models.feed_article import FeedArticle
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate, PromptTemplate, HumanMessagePromptTemplate
from langchain_core.messages import SystemMessage
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain.callbacks.tracers import ConsoleCallbackHandler
from models.utils import calculate_sha1_hash

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class TitleEditor:
	def __init__(self):
		self.ollama_url = os.getenv('OLLAMA_URL')
		if self.ollama_url:
			parser = StructuredOutputParser.from_response_schemas(
				[ResponseSchema(name="title", description="title of the article")]
			)
			
			format_instructions = f"""
				{parser.get_format_instructions()}
				The contents of the markdown code snippet MUST be in VALID json format which includes proper quotes and escape characters!
				JSON property names are case sensitive, and MUST ONLY include the defined schema properties!
			"""

			prompt = PromptTemplate(
				template="""
					title: {title},
					summary: {summary},
					{format_instructions}
				""",
				input_variables=["title", "summary"],
				partial_variables={"format_instructions": format_instructions},
			)

			# format chat prompt
			system_prompt = SystemMessage(content=("""
				You are an expert news article title editor.
				Use the provided title and summary to write a concise and accurate title that is informative and avoids sounding like clickbait. 
				Do not include links or urls in the title.
				Do not editorialize the title, even if the provided title and summary do.                                 
				title MUST be as short as possible, aim to be less that 70 characters long.
				title MUST have an absolute minimum of punctuation. 
				title MUST NOT use words that are all capitalized. NO SHOUTING!
				Only return the title in the requested format!																	
				"""))
			user_prompt = HumanMessagePromptTemplate(prompt=prompt)
			
			chat_prompt = ChatPromptTemplate.from_messages([system_prompt, user_prompt])
			model_name = "dolphin-mistral"
			#model_name = "dolphin-llama3"
			model_temp = 0.0
			model = Ollama(base_url=self.ollama_url, model=model_name, keep_alive=5, temperature=model_temp)
			self.chain = chat_prompt | model | parser
			
			self.script_hash = calculate_sha1_hash(f"{system_prompt.content}{model_name}{model_temp}") 

	def process(self, articles: list[FeedArticle]) -> list[FeedArticle]:
		if self.ollama_url:
			
			needs_processed = list(filter(lambda article: article.processed != self.script_hash, articles))
			if len(needs_processed) > 10:
				needs_processed = list(filter(lambda article: article.pub_date.replace(tzinfo=utc) >= (datetime.now() - timedelta(days=1)).replace(tzinfo=utc), articles))

			
			total = len(needs_processed)
			for count, article in enumerate(needs_processed, start=1):
				try:
					logger.info(f"Processing title {count}/{total}: {article.original_title}")
					result = self.chain.invoke({"title": article.original_title, "summary": article.description}) #, config={'callbacks': [ConsoleCallbackHandler()]})
					article.title = result['title']
					article.processed = self.script_hash
				except Exception as ex:
					logger.error(f"Error: {ex} for {article.original_title}")
					#needs_processed.remove(article)
				
		return articles
