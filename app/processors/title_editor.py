import logging
import os
from pathlib import Path
from models.feed_article import FeedArticle
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate, PromptTemplate, HumanMessagePromptTemplate
from langchain_core.messages import SystemMessage
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from models.utils import calculate_sha1_hash


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = False

# create console handler
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logging.Formatter(fmt='%(asctime)s - %(message)s'))

# Add console handler to logger
logger.addHandler(consoleHandler)

class TitleEditor:
  def __init__(self):
    self.ollama_url = os.getenv('OLLAMA_URL')
    if self.ollama_url:
      parser = StructuredOutputParser.from_response_schemas(
        [ResponseSchema(name="title", description="title of the article")]
      )

      prompt = PromptTemplate(
        template="""
          title: {title},
          summary: {summary},
          {format_instructions}
        """,
        input_variables=["title", "summary"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
      )

      # format chat prompt
      system_prompt = SystemMessage(content=("""
        You are an expert news article title editor.
        Use the provided title and summary to write a concise and accurate title that is informative and avoids sounding like clickbait. 
        Do not include links or urls in the title.
        Do not editorialize the title, even if the title and description do.                                 
        Title must be as short as possible, aim to be less that 70 characters long.
        Title must have an absolute minimum of punctuation and NOT use words that are all upper case.
        """))
      user_prompt = HumanMessagePromptTemplate(prompt=prompt)
      
      chat_prompt = ChatPromptTemplate.from_messages([system_prompt, user_prompt])
      model_name = "dolphin-mistral"
      model_temp = 0.2
      model = Ollama(base_url=self.ollama_url, model=model_name, keep_alive=5, temperature=model_temp)
      self.chain = chat_prompt | model | parser
      
      self.script_hash = calculate_sha1_hash(f"{system_prompt.content}{model_name}{model_temp}") 

  def process(self, articles: list[FeedArticle]) -> list[FeedArticle]:
    if self.ollama_url:
      
      needs_processed = list(filter(lambda article: article.processed != self.script_hash, articles))
      
      total = len(needs_processed)
      for count, article in enumerate(needs_processed, start=1):
        try:
          logger.info(f"Processing title {count}/{total}: {article.original_title}")
          result = self.chain.invoke({"title": article.original_title, "summary": article.description})
          article.title = result['title']
          article.processed = self.script_hash
        except Exception as ex:
          logger.error(f"Error: {ex} for {article.original_title}")
          #needs_processed.remove(article)
        
    return articles
