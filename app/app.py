import os
from datetime import datetime

import feedparser
from datetime import datetime
from flask import Flask, render_template
from flask_caching import Cache
from post_processor import post_processor

from utils import clean_html, copy_default_to_configs, load_file

copy_default_to_configs()

app = Flask(__name__)

# 600 seconds = 10 minutes
cache = Cache(app, config={
  'CACHE_TYPE': 'simple',            
  'CACHE_DEFAULT_TIMEOUT': 600
})

@app.context_processor
def inject_current_date():
  return {'today_date': datetime.now()}

# Define route to render the template
@app.route('/')
@cache.cached(timeout=600)
def index():
  # Load feeds and bookmarks
  layout = load_file('layout.yml', cache)
  headers = layout['headers']
  widgets = layout['widgets']
  
  # Divide feeds into three columns
  columns = [[], [], []]

  # Add feeds to the appropriate column
  for widget in widgets:
    column_index = (widget['column'] - 1) % 3
    if widget['type'] == 'feed':
      parsed_feed = feedparser.parse(widget['url'])
      parsed_item = {
        'title': widget['name'],
        'link': widget['link'],
        'type': widget['type'],
        'summary_enabled': bool(widget.get('summary', True)),
        'articles': [{
          'title': " ".join(entry.get('title', 'No Title').split()).strip() , 
          'link': entry.link, 
          'summary': clean_html(entry.get('summary', ''))} for entry in parsed_feed.entries[:10]] if 'entries' in parsed_feed else []
      }
      parsed_item = post_processor.process(parsed_item['title'], parsed_item)
      columns[column_index].append(parsed_item)
    elif widget['type'] == 'bookmarks':
      columns[column_index].append({
        'title': widget['name'], 
        'type': widget['type'], 
        'articles': [{'title': entry['title'], 'link': entry['url']} for entry in widget['bookmarks']]
      })

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
