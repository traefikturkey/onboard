import os
import shutil

def copy_default_to_configs():
    pwd = os.path.dirname(os.path.abspath(__file__))
    default_dir = os.path.join(pwd, 'defaults') 
    config_dir = os.path.join(pwd, 'configs')

    # Check if the config directory is empty
    if not os.listdir(config_dir):
        # Get a list of files in the default directory
        files = os.listdir(default_dir)

        # Copy each file from the default directory to the config directory
        for file in files:
            src = os.path.join(default_dir, file)
            dst = os.path.join(config_dir, file)
            shutil.copy2(src, dst)
        
        print(f"Files copied successfully from {default_dir} to {config_dir}.")
    else:
        print(f"Directory {config_dir} is not empty. No action taken.")