import os
import shutil
from pathlib import Path

def copy_default_to_configs():
	pwd = os.path.dirname(os.path.abspath(__file__))
	default_dir = os.path.join(pwd, 'defaults') 
	config_dir = os.path.join(pwd, 'configs')
 
 
	Path(config_dir).mkdir(parents=True, exist_ok=True)
	
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

