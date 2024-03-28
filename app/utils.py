import os
import shutil
import yaml

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

class FileData:
    def __init__(self, last_modified=0, contents=None):
        self.last_modified = last_modified
        self.contents = contents

    def __getitem__(self, key, default=None):
        return self.contents.get(key, default)

file_cache = {}

def load_file(file_name, cache=None):
    current_working_directory = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(current_working_directory, 'configs', file_name)

    # Check the last modification time of the file
    current_modified_time = os.path.getmtime(file_path)

    # Only load the file if it has been modified since the last check or if there is no value for that file in the dict
    if current_modified_time > file_cache.get(file_path, FileData()).last_modified or file_path not in file_cache:
        with open(file_path, 'r') as file:
            contents = yaml.safe_load(file)
        file_cache[file_path] = FileData(current_modified_time, contents)

    return file_cache[file_path].contents
