#!/usr/bin/env python3
"""Connect to Selenium remote, load the app root, wait 5 seconds, and save a screenshot.

Environment variables:
  SELENIUM_URL - full URL to selenium remote (e.g. http://172.17.0.4:4444/wd/hub)
  APP_URL - full URL to app root (e.g. http://172.17.0.3:9830)

Saves screenshot to .artifacts/screenshot.png under repo root.
"""
import os
import sys
import time
from pathlib import Path

SELENIUM_URL = os.environ.get("SELENIUM_URL")
APP_URL = os.environ.get("APP_URL")

if not SELENIUM_URL or not APP_URL:
  print("SELENIUM_URL and APP_URL environment variables must be set.\nExample: SELENIUM_URL=http://172.17.0.4:4444/wd/hub APP_URL=http://172.17.0.3:9830 python scripts/take_screenshot.py")
  sys.exit(2)

# Import selenium (raise a clear error if missing)
try:
  from selenium import webdriver
  from selenium.webdriver.chrome.options import Options
except Exception as exc:
  print("Unable to import selenium:", exc)
  sys.exit(3)

out_dir = Path(__file__).resolve().parents[1] / ".artifacts"
out_dir.mkdir(parents=True, exist_ok=True)
out_path = out_dir / "screenshot.png"

opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")

print(f"Connecting to Selenium at {SELENIUM_URL}")
try:
  driver = webdriver.Remote(command_executor=SELENIUM_URL, options=opts)
except Exception as exc:
  print(f"Failed to connect to Selenium at {SELENIUM_URL}: {exc}")
  sys.exit(4)

try:
  print(f"Loading {APP_URL}/")
  driver.set_page_load_timeout(30)
  driver.get(APP_URL + "/")
  print("Waiting 5 seconds to allow page assets to load...")
  time.sleep(5)
  print(f"Saving screenshot to {out_path}")
  ok = driver.save_screenshot(str(out_path))
  if not ok:
    print("save_screenshot returned False")
    sys.exit(5)
  size = out_path.stat().st_size
  print(f"Saved screenshot: {out_path} ({size} bytes)")
finally:
  try:
    driver.quit()
  except Exception:
    pass

print("Done")
