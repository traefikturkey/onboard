import time
import aiohttp
import feedparser
import html
import requests
import re

from post_processor import post_processor
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
import warnings

warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

class Rss:
  
  def clean_html(self, text: str) -> str:
    """
    Removes HTML tags, decode HTML entities, and strip leading and trailing
    whitespace from the given text.

    Args:
        text (str): The text to clean.

    Returns:
        str: The cleaned text.
    """
    text = text.replace('\n', ' ').replace('\r', ' ').strip()
    
    if not text:
      return text
    
    text = BeautifulSoup(html.unescape(text), 'lxml').text
    text = re.sub(r'\[.*?\].*$', '', text)
    # text = re.sub(r'http[s]?://\S+', '', text, flags=re.IGNORECASE)
    # text = ' '.join([x.capitalize() for x in text.split(' ')])
    return text

  async def load_feed(self, widget, column):
    start_time = time.time()
    async with aiohttp.ClientSession() as session:
      async with session.get(widget['url']) as response:
        parsed_feed = feedparser.parse(await response.text())
        widget['summary_enabled'] = widget.get('summary_enabled', True)
        widget['articles'] = [{
            'title': " ".join(entry.get('title', 'No Title').split()).strip() , 
            'link': entry.link, 
            'summary': self.clean_html(entry.get('summary', ''))} for entry in parsed_feed.entries[:10]] if 'entries' in parsed_feed else []
        widget = post_processor.process(widget['name'], widget)
        column.append(widget)
        return (time.time() - start_time)
  
  def find_feed_links(self, url):
    response = requests.get(url)
    
    if response.status_code == 200:
      soup = BeautifulSoup(response.content, 'html.parser')
      links = soup.find_all('link', type=["application/rss+xml", "application/atom+xml"])
      
      feed_links = []
      for link in links:
        feed_links.append(link.get('href'))
      
      return feed_links
    else:
      print(f"Failed to retrieve content from {url}")
      return None

rss = Rss()   



if __name__ == "__main__":
  webpage_url = "https://blog.langchain.dev/automating-web-research/"# input("Enter the URL of the webpage: ")
  
  rss = Rss()
  feed_links = rss.find_feed_links(webpage_url)
  
  if feed_links:
    print("Feed Links Found:")
    for feed_link in feed_links:
      enties = feedparser.parse(feed_link)
      for entry in enties.entries:
        print(entry.title)
        print(rss.clean_html(entry.get('summary', '')))
        print()

      print(feed_link)
else:
    print("No Feed Links Found on the provided page.")

