from app.app import app
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "app")))

if __name__ == "__main__":
  # Allow overriding the port via PORT or ONBOARD_PORT environment variable (default: 5000)
  port = int(os.getenv("PORT", os.getenv("ONBOARD_PORT", "5000")))
  # Allow toggling debug via DEBUG or FLASK_DEBUG (default: True)
  debug = os.getenv("DEBUG", os.getenv("FLASK_DEBUG", "True")).lower() in ("1", "true", "yes")
  app.run(host="0.0.0.0", port=port, debug=debug)
