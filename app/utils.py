import logging
import os
import shutil
from pathlib import Path
from models.utils import pwd

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.propagate = False

# create console handler
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logging.Formatter(fmt='%(asctime)s - %(message)s'))

# Add console handler to logger
logger.addHandler(consoleHandler)

def copy_default_to_configs():
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
			logger.info(f"File {file} copied successfully from {default_dir} to {config_dir}.")
	
	if files_copied == 0:
		logger.info(f"No files copied from {default_dir} to {config_dir}.")    

