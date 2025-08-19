#!/usr/bin/env bash
# Lightweight smoke-test for the production Docker image.
# This script deliberately does NOT use `set -e` so it won't kill your interactive
# terminal on failures while we iterate inside a devcontainer.
# Usage (from repo root):
#   chmod +x scripts/smoke_test_prod_image.sh
#   scripts/smoke_test_prod_image.sh

IMAGE=onboard:prod
CONTAINER=onboard_test
PORT=9830
# If running inside a container as root (UID 0), pass a non-root UID/GID to the image build
# because the Dockerfile will try to create a user/group with those IDs which fails for 0.
HOST_UID=$(id -u)
HOST_GID=$(id -g)
if [ "${HOST_UID}" -eq 0 ]; then
  BUILD_PUID=1000
else
  BUILD_PUID=${HOST_UID}
fi
if [ "${HOST_GID}" -eq 0 ]; then
  BUILD_PGID=1000
else
  BUILD_PGID=${HOST_GID}
fi
BUILD_ARGS=("--build-arg" "PUID=${BUILD_PUID}" "--build-arg" "PGID=${BUILD_PGID}" "--build-arg" "PROJECT_NAME=onboard")
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "[info] repo root: ${REPO_ROOT}"

build_failed=0
run_failed=0
http_ok=0

echo "[info] Building production image ${IMAGE} (this may take a while)..."
# Ensure BuildKit env vars are sane for the docker CLI (some devcontainers export weird values)
DOCKER_BUILDKIT=1 COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_SCAN_SUGGEST=0 \
  docker build --target production -t "${IMAGE}" "${BUILD_ARGS[@]}" "${REPO_ROOT}" || build_failed=1

echo "[info] Removing any previous container named ${CONTAINER}..."
docker rm -f "${CONTAINER}" >/dev/null 2>&1 || true

echo "[info] Starting container ${CONTAINER} (publishing ${PORT}:${PORT})..."
docker run -d --name "${CONTAINER}" -p "${PORT}:${PORT}" "${IMAGE}" >/dev/null 2>&1 || run_failed=1

echo "[info] Waiting for HTTP service to respond on 127.0.0.1:${PORT} (up to 60s)..."
attempt=0
max_attempts=60
while [ ${attempt} -lt ${max_attempts} ]; do
  # Try a quick curl; give it 2s timeout so we don't block too long
  if curl -sS --max-time 2 "http://127.0.0.1:${PORT}/" -o /tmp/onboard_index.html; then
    if [ -s /tmp/onboard_index.html ]; then
      echo "[ok] HTTP response received (127.0.0.1:${PORT})"
      http_ok=1
      break
    fi
  fi
  attempt=$((attempt+1))
  sleep 1
done

if [ ${http_ok} -ne 1 ]; then
  echo "[warn] No response on 127.0.0.1:${PORT}, attempting container network diagnostics..."
  container_ip=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "${CONTAINER}" 2>/dev/null || true)
  echo "[info] Container IP: ${container_ip:-<none>}"
  if [ -n "${container_ip}" ]; then
    echo "[info] Trying HTTP against container IP ${container_ip}:${PORT}"
    curl -sS --max-time 3 "http://${container_ip}:${PORT}/" -o /tmp/onboard_index.html || true
    if [ -s /tmp/onboard_index.html ]; then
      echo "[ok] HTTP response received from container IP"
      http_ok=1
    else
      echo "[warn] No HTTP body fetched from container IP"
    fi
  fi
fi

echo "\n--- Final diagnostics ---"
echo "Image build failed: ${build_failed}";
echo "Container run failed: ${run_failed}";
echo "HTTP OK: ${http_ok}";

echo "--- docker ps (matching container) ---"
docker ps --filter name="${CONTAINER}" --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'

echo "--- last container logs (tail 200) ---"
docker logs --tail 200 "${CONTAINER}" 2>&1 || true

echo "--- docker network: bridge inspect (gateway) ---"
docker network inspect bridge 2>&1 || true

echo "--- host network interfaces (brief) ---"
ip -brief addr 2>&1 || true

if [ -s /tmp/onboard_index.html ]; then
  echo "--- fetched / (first 200 bytes) ---"
  head -c 200 /tmp/onboard_index.html || true
  echo "\n(complete body saved to /tmp/onboard_index.html)"
fi

# Exit code summary: 0 if build+run+http succeeded; 2 otherwise. Do not use `set -e` so caller's shell survives.
if [ ${build_failed} -eq 0 ] && [ ${run_failed} -eq 0 ] && [ ${http_ok} -eq 1 ]; then
  echo "[result] SMOKE TEST PASSED"
  exit 0
else
  echo "[result] SMOKE TEST FAILED"
  exit 2
fi
