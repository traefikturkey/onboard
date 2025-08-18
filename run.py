from app.main import app
import os
import sys


if __name__ == "__main__":
  # Allow overriding the port via PORT or ONBOARD_PORT environment variable (default: 9830)
  port = int(os.getenv("PORT", os.getenv("ONBOARD_PORT", "9830")))
  # Allow toggling debug via DEBUG or FLASK_DEBUG (default: True)
  debug = os.getenv("DEBUG", os.getenv("FLASK_DEBUG", "True")).lower() in ("1", "true", "yes")
  app.run(host="0.0.0.0", port=port, debug=debug)
