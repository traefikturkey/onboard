#!/usr/bin/env python3
"""Load the app root, wait for content, and save a screenshot.

Environment variables:
  APP_URL - full URL to app root (e.g. http://172.17.0.3:9830)

Saves screenshot to .artifacts/screenshot.png under repo root.
"""
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

APP_URL = os.environ.get("APP_URL")

if not APP_URL:
    print(
        "APP_URL environment variable must be set.\n"
        "Example: APP_URL=http://172.17.0.3:9830 python scripts/take_screenshot.py"
    )
    sys.exit(2)

out_dir = Path(__file__).resolve().parents[1] / ".artifacts"
out_dir.mkdir(parents=True, exist_ok=True)
out_path = out_dir / "screenshot.png"

print(f"Launching Playwright Chromium (headless)")
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    page = context.new_page()

    print(f"Loading {APP_URL}/")
    page.goto(f"{APP_URL}/", timeout=30000)

    # Wait for network to settle so assets load
    page.wait_for_load_state("networkidle")

    print(f"Saving screenshot to {out_path}")
    page.screenshot(path=str(out_path), full_page=True)

    size = out_path.stat().st_size
    print(f"Saved screenshot: {out_path} ({size} bytes)")

    browser.close()

print("Done")
