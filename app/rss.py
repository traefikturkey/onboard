import feedparser
import html
import requests
from bs4 import BeautifulSoup

class Rss:
  def clean_html(self, text):
    return BeautifulSoup( html.unescape(text), 'lxml').get_text()
  
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

