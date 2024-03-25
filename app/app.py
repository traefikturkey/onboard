import os
import html
import re
import string
import yaml
from datetime import datetime

import feedparser
import pprint
from datetime import datetime
from bs4 import BeautifulSoup
from docker import APIClient
from flask import Flask, render_template
from flask_caching import Cache
from post_processor import post_processor

import difflib
from utils import copy_default_to_configs

copy_default_to_configs()

app = Flask(__name__)


# 600 seconds = 10 minutes
cache = Cache(app, config={'CACHE_TYPE': 'simple',
              'CACHE_DEFAULT_TIMEOUT': 600})
#docker_client = APIClient(base_url='unix://var/run/docker.sock')
current_working_directory = os.path.dirname(os.path.realpath(__file__))

last_modified_times = {}
pp = pprint.PrettyPrinter(indent=2)


def load_file(file_name):
  global last_modified_times

  # Adjust file path for the configs subdirectory
  file_path = os.path.join(current_working_directory, 'configs', file_name)

  # Check the last modification time of the file
  current_modified_time = os.path.getmtime(file_path)
  current_data = cache.get(file_path)

  # If the file has been modified since the last check, reload it
  if current_modified_time != last_modified_times.get(file_path) or not current_data:
    last_modified_times[file_path] = current_modified_time
    with open(file_path, 'r') as file:
      current_data = yaml.safe_load(file)
      cache.set(file_path, current_data)

  return current_data


def clean_html(text):
  text = text.replace('\n', ' ').replace('\r', ' ')
  text = BeautifulSoup(html.unescape(text), 'lxml').text
  text = re.sub(r'\[.*?\].*$', '', text)
  # text = re.sub(r'http[s]?://\S+', '', text, flags=re.IGNORECASE)
  # text = ' '.join([x.capitalize() for x in text.split(' ')])

  return text.strip()

def process_duplicates(data):
  for article in data['articles']:
    if difflib.SequenceMatcher(None, article['title'], article['summary']).ratio() == 0.0:
      print(article['title'])
      article['summary'] = ''
    
      
  return data

@app.context_processor
def inject_current_date():
  return {'today_date': datetime.now()}

# def docker_event_stream():
#   events = docker_client.events()
#   for event in events:
#     yield 'data: {}\n\n'.format(event)

# @app.route('/events')
# def events():
#   return app.response_class(
#     docker_event_stream(),
#     mimetype='text/event-stream'
# )

# Define route to render the template
@app.route('/')
def index():
  # Load feeds and bookmarks
  layout = load_file('layout.yml')
  feeds = layout['feeds']
  headers = layout['headers']
  bookmarks = load_file('bookmarks.yml')['bookmarks']

  # Divide feeds into three columns
  columns = [[], [], []]

  # Add bookmarks to the second column
  columns[1].append({
    'title': 'Bookmarks',
    'type': 'bookmarks',
    'articles': [{'title': entry['title'], 'link': entry['url']} for entry in bookmarks]
  })

  # Add feeds to the appropriate column
  for feed in feeds:
    column_index = (feed['column'] - 1) % 3
    columns[column_index].append({
      'title': feed['name'], 
      'link': feed['link'], 
      'url': feed['url'], 'summary_enabled': bool(feed.get('summary', True))
    })

  # Parse feeds and extract titles, links, summaries, and columns
  for column in columns:
    for item in column:
      if 'url' in item:  # If it's a bookmark or a feed with a URL
        # Check if the item data is already cached
        cache_key = f"{item['url']}_parsed_data"
        parsed_item = cache.get(cache_key)
        if not parsed_item:
          parsed_feed = feedparser.parse(item['url'])
          parsed_item = {
            'title': item['title'],
            'articles': [{
              'title': " ".join(entry.get('title', 'No Title').strip().split()) , 
              'link': entry.link, 
              'summary': clean_html(entry.get('summary', ''))} for entry in parsed_feed.entries[:10]] if 'entries' in parsed_feed else []
          }

          #parsed_item = process_duplicates(parsed_item)
          parsed_item = post_processor.process(parsed_item['title'], parsed_item)
          
          # Cache parsed item data for 10 minutes
          cache.set(cache_key, parsed_item, timeout=600)

        item['title'] = parsed_item['title'] if parsed_item['title'] else item.get('name', 'Untitled')
        item['articles'] = parsed_item['articles']
        item['type'] = 'feed'

  # Pass column data to the template
  return render_template('index.html', columns=columns, headers=headers)


if __name__ == '__main__':
  port = int(os.environ.get("ONBOARD_PORT", 9830))
  if os.environ.get("FLASK_DEBUG", "False") == "True":
    app.run(port=port, debug=True)
  else:
    import asyncio
    from hypercorn.config import Config
    from hypercorn.asyncio import serve
    config = Config()
    config.bind = [f"0.0.0.0:{port}"]
    asyncio.run(serve(app, config))
