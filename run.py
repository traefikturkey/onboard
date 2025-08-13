from app.app import app
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "app")))

if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000, debug=True)
