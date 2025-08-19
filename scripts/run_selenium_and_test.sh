#!/usr/bin/env bash
# Start Selenium standalone Chrome (Docker) and run pytest for integration tests.
# Usage: ./scripts/run_selenium_and_test.sh

SEL_CONTAINER=selenium_chrome_test
APP_CONTAINER=onboard_test
SEL_IMAGE=selenium/standalone-chrome:115.0

# Start selenium container
docker rm -f ${SEL_CONTAINER} >/dev/null 2>&1 || true
# Use host network mapping: expose 4444
docker run -d --name ${SEL_CONTAINER} -p 4444:4444 ${SEL_IMAGE}

# Wait for Selenium to come up
echo "Waiting for Selenium at http://127.0.0.1:4444/wd/hub"
for i in $(seq 1 30); do
  if curl -sS --max-time 2 http://127.0.0.1:4444/status >/dev/null 2>&1; then
    echo "Selenium up"
    break
  fi
  sleep 1
done

# Ensure the app container is running (if not, start it)
if ! docker ps --filter name=${APP_CONTAINER} --format '{{.Names}}' | grep -q ${APP_CONTAINER}; then
  echo "Starting ${APP_CONTAINER} from onboard:prod"
  docker run -d --name ${APP_CONTAINER} -p 9830:9830 onboard:prod || true
fi

# Run pytest integration tag
pytest -q -k integration tests/integration/test_selenium_prod.py

# Teardown Selenium container
# docker rm -f ${SEL_CONTAINER} || true
