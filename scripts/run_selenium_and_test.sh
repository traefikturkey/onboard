#!/usr/bin/env bash
# Start Selenium standalone Chrome (Docker) and run pytest for integration tests.
# Usage: ./scripts/run_selenium_and_test.sh

SEL_CONTAINER=selenium_chrome_test
APP_CONTAINER=onboard_test
SEL_IMAGE=selenium/standalone-chrome:115.0

# Start selenium container
docker rm -f ${SEL_CONTAINER} >/dev/null 2>&1 || true
# Use host network mapping: expose 4444
echo "Waiting for Selenium at http://127.0.0.1:4444/wd/hub"
docker run -d --name ${SEL_CONTAINER} -p 4444:4444 ${SEL_IMAGE}

# Determine the selenium container IP on the docker bridge network and wait until it's healthy.
echo "Waiting for Selenium container to be ready and discovering its container IP..."
SEL_IP=""
for i in $(seq 1 30); do
  SEL_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ${SEL_CONTAINER} 2>/dev/null || true)
  if [ -n "${SEL_IP}" ]; then
    # Try the container IP status endpoint
    if curl -sS --max-time 2 "http://${SEL_IP}:4444/status" >/dev/null 2>&1; then
      echo "Selenium up at ${SEL_IP}:4444"
      break
    fi
  fi

    sleep 1
  done

if [ -z "${SEL_IP}" ]; then
  echo "Warning: could not determine selenium container IP or it did not become healthy; falling back to localhost:4444"
fi
# Ensure the app container is running (if not, start it)

# Ensure the app container is running (if not, start it)
if ! docker ps --filter name=${APP_CONTAINER} --format '{{.Names}}' | grep -q ${APP_CONTAINER}; then
  echo "Starting ${APP_CONTAINER} from onboard:prod"
  docker run -d --name ${APP_CONTAINER} -p 9830:9830 onboard:prod || true
fi

# Discover app container IP on docker network
APP_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ${APP_CONTAINER} 2>/dev/null || true)
if [ -z "${APP_IP}" ]; then
  echo "Warning: could not determine app container IP; using localhost:9830"
  APP_URL=http://127.0.0.1:9830
else
  APP_URL="http://${APP_IP}:9830"
  echo "Discovered app at ${APP_URL}"
fi

# Use selenium container IP for SELENIUM_URL if available, else fall back to localhost
if [ -n "${SEL_IP}" ]; then
  SELENIUM_URL="http://${SEL_IP}:4444/wd/hub"
else
  SELENIUM_URL="http://127.0.0.1:4444/wd/hub"
fi

echo "Running pytest against SELENIUM_URL=${SELENIUM_URL} APP_URL=${APP_URL} using uv run"
# Use uv run to run pytest inside the project's environment (uv-managed)
SELENIUM_URL=${SELENIUM_URL} APP_URL=${APP_URL} uv run pytest -q -k integration tests/integration/test_selenium_prod.py

# Teardown Selenium container
# docker rm -f ${SEL_CONTAINER} || true
