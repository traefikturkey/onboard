import base64
import hashlib
import logging
import os
from functools import cached_property
from models.feed_article import FeedArticle
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate, PromptTemplate, HumanMessagePromptTemplate
from langchain_core.messages import SystemMessage
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from models.utils import calculate_sha1_hash

logger = logging.getLogger(__name__)

class TitleEditor:
  def __init__(self):
    self.ollama_url = os.getenv('OLLAMA_URL')
    logger.setLevel(logging.DEBUG)
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
        Title should be as short as possible, aim to be less that 70 characters long.
        Title should have an absolute minimum of punctuation and use at most one all capitalized word at the start of the title.
        """))
      user_prompt = HumanMessagePromptTemplate(prompt=prompt)
      
      chat_prompt = ChatPromptTemplate.from_messages([system_prompt, user_prompt])
      model_name = "dolphin-mistral"
      model_temp = 0.0
      model = Ollama(base_url=self.ollama_url, model=model_name, keep_alive=5, temperature=model_temp)
      self.chain = chat_prompt | model | parser
      
      self.script_hash = calculate_sha1_hash(f"{system_prompt.content}{model_name}{model_temp}") 

  def process(self, articles: list[FeedArticle]) -> list[FeedArticle]:
    if self.ollama_url:
      
      needs_processed = list(filter(lambda article: article.processed != self.script_hash, articles))
      
      total = len(needs_processed)
      for count, article in enumerate(needs_processed, start=1):
        try:
          logger.debug(f"{count}/{total}: {article.processed != self.script_hash} current hash: {self.script_hash} processed hash: {article.processed}")
          result = self.chain.invoke({"title": article.original_title, "summary": article.description})
          article.title = result['title']
          article.processed = self.script_hash
        except Exception as ex:
          print(f"Error: {ex} for {article.original_title}")
          needs_processed.remove(article)
        
    return articles
