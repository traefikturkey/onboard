import html
import os
import re
import shutil

import yaml

from bs4 import BeautifulSoup

def copy_default_to_configs():
  pwd = os.path.dirname(os.path.abspath(__file__))
  default_dir = os.path.join(pwd, 'defaults') 
  config_dir = os.path.join(pwd, 'configs')
  
  # copy files from default directory to configs directory that are missing
  # track number of files copied in variable files_copied
  files_copied = 0
  for file in os.listdir(default_dir):
    if file not in os.listdir(config_dir):
      src = os.path.join(default_dir, file)
      dst = os.path.join(config_dir, file)
      shutil.copy2(src, dst)
      files_copied += 1
      print(f"File {file} copied successfully from {default_dir} to {config_dir}.")
  
  if files_copied > 0:
    print(f"Default files synced from {default_dir} to {config_dir}.")
  else:
    print(f"No files copied from {default_dir} to {config_dir}.")    
    
def clean_html(text):
  text = text.replace('\n', ' ').replace('\r', ' ')
  text = BeautifulSoup(html.unescape(text), 'lxml').text
  text = re.sub(r'\[.*?\].*$', '', text)
  # text = re.sub(r'http[s]?://\S+', '', text, flags=re.IGNORECASE)
  # text = ' '.join([x.capitalize() for x in text.split(' ')])

  return text.strip()

global last_modified_times
last_modified_times = {}

def load_file(file_name, cache):
  # Adjust file path for the configs subdirectory
  current_working_directory = os.path.dirname(os.path.realpath(__file__))
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