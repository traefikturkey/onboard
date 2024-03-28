import os
import yaml
import asyncio
from datetime import datetime

from flask import Flask, request, render_template
from flask_caching import Cache

from utils import copy_default_to_configs, load_file
from rss import rss

copy_default_to_configs()

app = Flask(__name__)

if os.environ.get("FLASK_DEBUG", "False") == "True":
  cache_config={
    'CACHE_TYPE': 'null'
  }
else:
  # 600 seconds = 10 minutes
  cache_config={
    'CACHE_TYPE': 'simple',            
    'CACHE_DEFAULT_TIMEOUT': 600
  }
  from flask_minify import Minify
  Minify(app=app, html=True, js=True, cssless=True)
  
  
cache = Cache(app, config=cache_config)

@app.context_processor
def inject_current_date():
  return {'today_date': datetime.now()}

@app.route('/save_tab_name', methods=['POST'])
def save_tab_name():
    data = request.get_json()
    tab_name = data.get('tab_name')
    tab_index = data.get('tab_index')
    column_count = data.get('column_count')

    if tab_name and column_count >= 1 and column_count <= 6:
        with open('configs/layout.yml', 'r') as file:
            layout = yaml.safe_load(file)

        tabs = layout['tabs']

        if tab_index is not None:
            # Edit an existing tab
            tabs[tab_index]['name'] = tab_name
            tabs[tab_index]['columns'] = column_count
        else:
            # Add a new tab
            tabs.append({'name': tab_name, 'columns': column_count, 'widgets': []})

        with open('configs/layout.yml', 'w') as file:
            yaml.safe_dump(layout, file)

        return {'message': f'Tab name "{tab_name}" with {column_count} columns saved successfully'}
    else:
        return {'error': 'Invalid tab name or column count'}, 400

# Define route to render the template
@app.route('/')
@app.route('/<tab_name>')
@cache.cached(timeout=600)
async def index(tab_name=None):
  # Load feeds and bookmarks
  layout = load_file('layout.yml', cache)
  headers = layout['headers']
  
  tabs = layout['tabs']
  if tab_name is None:
    tab = tabs[0]
  else:
    tab = next((tab for tab in tabs if tab["name"].lower() == tab_name.lower()), tabs[0])
  current_tab = tab['name']
  
  column_count = tab['columns']
  columns = [[] for _ in range(column_count)]
  
  tasks = []
    
  # Add feeds to the appropriate column
  if tab['widgets']:
    for widget in tab['widgets']:
      column_index = (widget['column'] - 1) % column_count
      if widget['type'] == 'feed':
        tasks.append(asyncio.create_task(rss.load_feed(widget, columns[column_index])))
      elif widget['type'] == 'bookmarks':
        widget['articles'] = [{'title': entry['title'], 'link': entry['url']} for entry in widget['bookmarks']]
        columns[column_index].append(widget)

  await asyncio.wait(tasks)
  for column in columns:
    column.sort(key = lambda x: x['position'])
    
  # Pass column data to the template
  return render_template('index.html', tabs=tabs, columns=columns, headers=headers, current_tab=current_tab)

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
