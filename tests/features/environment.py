import subprocess
import time
import os


def before_all(context):
  # Start the app using uv run python run.py
  env = os.environ.copy()
  env["PYTHONPATH"] = "app"
  context.app_process = subprocess.Popen([
      "uv", "run", "python", "run.py"
  ], env=env)
  # Wait for the app to start
  time.sleep(10)  # Adjust as needed for startup time


def after_all(context):
  # Terminate the app process
  if hasattr(context, "app_process") and context.app_process:
    context.app_process.terminate()
    context.app_process.wait()
