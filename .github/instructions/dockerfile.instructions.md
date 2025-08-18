---
description: "Dockerfile and containerization best practices for Joyride DNS Service"
applyTo: "**/Dockerfile*"
---

# Dockerfile Core Requirements

### Base Images
- Use Alpine Linux containers for minimal attack surface, unless there are issues installing a needed package, then use Debian Slim based containers.
- Specify version tags for reproducible builds

### Multi-stage Builds
- Separate base/development/production stages
- Copy only necessary artifacts to final stage

### Security
- Create non-root users: 
- Set USER directive before EXPOSE and CMD
- Never include secrets in layers

### Layer Optimization
- Group RUN commands to reduce layers
- Use `--no-cache` and clean package caches
- Copy requirements files separately for better caching
- Order commands from least to most frequently changing

### Package Organization  
- Maintain alphabetical order in apk and apt packages

### Environment Variables
- Use ARG for build-time variables (PUID, PGID, USER, WORKDIR)
- Use ENV for runtime variables
- Provide sensible defaults

### Health Checks
- Include health checks for orchestration
- Use lightweight commands (curl/wget)
- Set appropriate intervals and timeouts

### BuildKit Features
- Use cache mounts for RUN commands

## Example Pattern

```dockerfile
FROM python:3.12-alpine AS base
# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
ARG PUID=1000 PGID=1000 USER=appuser WORKDIR=/app
RUN addgroup -g ${PGID} ${USER} && \
    adduser -D -u ${PGID} -G ${USER} -s /bin/sh ${USER}
WORKDIR ${WORKDIR}

FROM base AS production
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system --no-cache -r requirements.txt
COPY app/ ./app/
USER ${USER}
HEALTHCHECK --interval=30s --timeout=10s \
    CMD curl -f http://localhost:9830/health || exit 1
CMD ["python", "-m", "app.main"]
```

## Signal Handling and Entrypoint Scripts

### Production Containers
- Use `gosu` with `exec` in production entrypoint scripts to drop privileges and forward signals
- Ensure CMD uses direct command execution (not shell wrapping) for proper signal delivery
- When docker.sock is mounted, fix permissions in entrypoint with: `chown ${USER}:${USER} /var/run/docker.sock >/dev/null 2>&1 || true`

### Development Containers
- Sudo is acceptable for devcontainer usage
- After 2 failures: stop and analyze the root cause completely, then apply full solution once

### Example Entrypoint Script
```bash
#!/bin/bash
set -o errexit   # abort on nonzero exitstatus
set -o nounset   # abort on unbound variable
set -o pipefail  # do not hide errors within pipes
if [ -v DOCKER_ENTRYPOINT_DEBUG ] && [ "$DOCKER_ENTRYPOINT_DEBUG" == 1 ]; then
    set -x
    set -o xtrace
fi

# If running as root, adjust the ${USER} user's UID/GID and drop to that user
if [ "$(id -u)" = "0" ]; then
    groupmod -o -g ${PGID:-1000} ${USER} 2>&1 >/dev/null|| true
    usermod -o -u ${PUID:-1000} ${USER} 2>&1 >/dev/null|| true

    # Ensure docker.sock is owned by the target user when running as root
    chown ${USER}:${USER} /var/run/docker.sock >/dev/null 2>&1 || true

    echo "Running as user ${USER}: $@"
    exec gosu ${USER} "$@"
fi

echo "Running: $@"
exec "$@"
```
