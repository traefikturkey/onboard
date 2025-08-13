---
description: "Dockerfile and containerization best practices for Joyride DNS Service"
applyTo: "**/Dockerfile*"
---

# Dockerfile Best Practices

## Core Requirements

### Base Images
- Use Alpine Linux (`python:3.12-alpine`) for minimal attack surface
- Specify version tags for reproducible builds

### Multi-stage Builds
- Separate base/development/production stages
- Copy only necessary artifacts to final stage

### Security
- Create non-root users: `adduser -D -s /bin/sh username`
- Set USER directive before EXPOSE and CMD
- Never include secrets in layers

### Layer Optimization
- Group RUN commands to reduce layers
- Use `--no-cache` and clean package caches
- Copy requirements files separately for better caching
- Order commands from least to most frequently changing

### Package Organization  
- Maintain alphabetical order in `RUN apk add` commands

### Environment Variables
- Use ARG for build-time variables (PUID, PGID, USER, WORKDIR)
- Use ENV for runtime variables
- Provide sensible defaults

### Health Checks
- Include health checks for orchestration
- Use lightweight commands (curl/wget)
- Set appropriate intervals and timeouts

### BuildKit Features
- Use cache mounts for package managers
- Support multi-platform builds when needed

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
    CMD curl -f http://localhost:5000/health || exit 1
CMD ["python", "-m", "app.main"]
```
