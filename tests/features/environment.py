import os
import subprocess
import time


def before_all(context):
    # Start the app using uv run python run.py
    env = os.environ.copy()
    env["PYTHONPATH"] = "app"
    # Disable scheduling and RSS feed updates during testing
    env["ONBOARD_DISABLE_SCHEDULER"] = "True"
    env["ONBOARD_FEED_FORCE_UPDATE"] = "False"
    # Force the app to bind to the test port (9830)
    env["ONBOARD_PORT"] = "9830"
    env["FLASK_PORT"] = "9830"
    context.app_process = subprocess.Popen(["uv", "run", "python", "run.py"], env=env)
    # Wait for the app to start
    time.sleep(12)  # Adjust as needed for startup time


def after_all(context):
    # Terminate the app process
    if hasattr(context, "app_process") and context.app_process:
        context.app_process.terminate()
        context.app_process.wait()
