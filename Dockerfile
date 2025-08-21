# syntax=docker/dockerfile:1.4
ARG PYTHON_VERSION=3.12-slim-bookworm

FROM python:${PYTHON_VERSION} as base
LABEL maintainer="Mike Glenn <mglenn@ilude.com>"

ARG TZ=America/New_York
ENV TZ=${TZ}

ENV DEBIAN_FRONTEND=noninteractive
ENV DEBCONF_NONINTERACTIVE_SEEN=true

RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt/lists \
    apt-get update && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    curl \
    gosu \
    libopenblas-dev \
    locales \
    tzdata && \
    # cleanup
    apt-get autoremove -fy && \
    apt-get clean && \
    apt-get autoclean -y && \
    rm -rf /var/lib/apt/lists/*

RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# ----------------------------------------------------------------------
# User setup
# Sets up the non-root user, group, home directory, project path, and shell
# This section is responsible for creating the runtime user and permissions
# ----------------------------------------------------------------------

# User management setup (previously in user_base stage)
ARG PUID=${PUID:-1000}
ARG PGID=${PGID:-1000}

ARG USER=anvil
ENV USER=${USER}

ENV HOME=/home/${USER}

ARG PROJECT_PATH=/srv
ENV PROJECT_PATH=${PROJECT_PATH}

WORKDIR $PROJECT_PATH

RUN sed -i 's/UID_MAX .*/UID_MAX    100000/' /etc/login.defs && \
    groupadd --gid ${PGID} ${USER} && \
    useradd --uid ${PUID} --gid ${PGID} -s /bin/sh -m ${USER} && \
    mkdir -p ${PROJECT_PATH} && \
    chown -R ${USER}:${USER} ${PROJECT_PATH} && \
    chown -R ${USER}:${USER} ${HOME}

# ----------------------------------------------------------------------
# --- docker-entrypoint setup section ---
# ----------------------------------------------------------------------

COPY --chmod=755 <<-"EOF" /usr/local/bin/docker-entrypoint.sh
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
    chown -R ${USER}:${USER} ${PROJECT_PATH}

    echo "Running as user ${USER}: $@"
    exec gosu ${USER} "$@"
else
    # If not running as root, attempt to chown docker.sock using sudo if available
    if command -v sudo >/dev/null 2>&1; then
        sudo chown ${USER}:${USER} /var/run/docker.sock >/dev/null 2>&1 || true
        sudo chown -R ${USER}:${USER} ${HOME}
        sudo chown -R ${USER}:${USER} ${PROJECT_PATH}
    fi
fi

echo "Running: $@"
exec "$@"
EOF

ENTRYPOINT [ "/usr/local/bin/docker-entrypoint.sh" ]



### Remove legacy vendor/deps path usage; rely on system site-packages managed by uv
ENV PYTHONUNBUFFERED=TRUE
ENV UV_LINK_MODE=copy
ENV UV_SYSTEM_PYTHON=1
# Install project dependencies into the system Python prefix instead of a project .venv
# See: https://docs.astral.sh/uv/concepts/projects/config/#project-environment-path
ENV UV_PROJECT_ENVIRONMENT=/usr/local
# Allow modifying the system environment inside containers
ENV UV_BREAK_SYSTEM_PACKAGES=1

ENV ONBOARD_PORT=${ONBOARD_PORT:-9830}

# ----------------------------------------------------------------------
# --- Build-base image stage
# ----------------------------------------------------------------------
FROM base as build-base

# Install build dependencies needed for compiling Python packages
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt/lists \
    apt-get update && apt-get install -y --no-install-recommends \
    bash \
    binutils \
    build-essential \
    pkg-config \
    gfortran \
    cmake \
    git \
    openssl \
    openssh-client \
    sqlite3 \
    libsqlite3-dev \
    # Additional build deps that some Python packages might need
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt-dev \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev && \
    apt-get autoremove -fy && \
    apt-get clean && \
    apt-get autoclean -y && \
    rm -rf /var/lib/apt/lists/*

# ----------------------------------------------------------------------
# --- Build-base image stage
# ----------------------------------------------------------------------
FROM build-base as build

# Copy lockfile and root pyproject for reproducible resolution
COPY uv.lock* pyproject.toml ${PROJECT_PATH}/
# Copy source needed to build the package (setuptools expects run.py and app/)
COPY app ${PROJECT_PATH}/app
COPY run.py ${PROJECT_PATH}/run.py

# Install Python dependencies into the system environment using uv
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=cache,target=/root/.cache/pip \
    uv sync --no-editable --no-dev


# ----------------------------------------------------------------------
# --- Production image stage ---
# ----------------------------------------------------------------------
FROM base as production

# Copy application code into the project directory root (creates ${PROJECT_PATH}/app)
COPY --chown=${USER}:${USER} app ${PROJECT_PATH}/app
# Copy the run script at project root so gunicorn can import `run:app`
COPY --chown=${USER}:${USER} run.py ${PROJECT_PATH}/run.py

# Bring in dependencies installed into the system prefix from the build stage
COPY --from=build /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=build /usr/local/bin /usr/local/bin

ENV FLASK_ENV=production
# Use default Python import paths; rely on ${PROJECT_PATH} as the working dir

# Create necessary directories for static assets
RUN mkdir -p ${PROJECT_PATH}/static/icons && \
    mkdir -p ${PROJECT_PATH}/static/assets && \
    chown -R ${USER}:${USER} ${PROJECT_PATH}

# Run the app with gunicorn via uv without a shell
CMD ["uv", "run", "--no-sync", "-m", "gunicorn", "run:app", "--bind", "0.0.0.0:9830", "--access-logfile", "-", "--error-logfile", "-"]

# ----------------------------------------------------------------------
# --- development os packages image stage ---
# ----------------------------------------------------------------------
FROM build-base as development-base

RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt/lists \
    apt-get update && apt-get install -y --no-install-recommends \
    bash-completion \
    coreutils \
    docker.io \
    dnsutils \
    exa \
    gh \
    gnuplot \
    gnuplot-x11 \
    graphviz \
    imagemagick \
    iproute2 \
    iputils-ping \
    jq \
    less \
    libpq-dev \
    libzmq3-dev \
    make \
    nodejs \
    npm \
    passwd \
    python3-pip \
    python3-setuptools \
    ripgrep \
    rsync \
    sshpass \
    sudo \
    tar \
    tree \
    util-linux \
    yarnpkg \
    yq \
    zsh \
    zsh-autosuggestions \
    zsh-syntax-highlighting && \
    apt-get autoremove -fy && \
    apt-get clean && \
    apt-get autoclean -y && \
    rm -rf /var/lib/apt/lists/* && \
    echo ${USER} ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/${USER} && \
    chmod 0440 /etc/sudoers.d/${USER} && \
    # set the shell for $USER and root
    chsh -s "$(which zsh)" ${USER}  && \
    chsh -s "$(which zsh)" root

# ----------------------------------------------------------------------
# --- development os packages image stage ---
# ----------------------------------------------------------------------
FROM development-base as devcontainer

# Copy lockfile and root pyproject for reproducible resolution
COPY uv.lock* pyproject.toml ${PROJECT_PATH}/

# Install Python dependencies into the system environment (run as root)
RUN --mount=type=cache,target=/tmp/.cache/uv \
    --mount=type=cache,target=/root/.cache/pip \
    --mount=type=cache,target=/root/.cache/uv \
    uv sync --dev && \
    chown -R $USER:$USER /usr/local/lib/python3.12/site-packages/ && \
    chown -R $USER:$USER /usr/local/bin


# Switch to non-root user for development
USER ${USER}

# Note: For production images, don't set DOCKER_BUILDKIT/COMPOSE_DOCKER_CLI_BUILD.
# We set DOCKER_BUILDKIT=1 only in the devcontainer stage to affect the docker CLI inside the container.

# Enable BuildKit for docker CLI inside the devcontainer
ENV DOCKER_BUILDKIT=1

# https://code.visualstudio.com/remote/advancedcontainers/start-processes#_adding-startup-commands-to-the-docker-image-instead
CMD [ "sleep", "infinity" ]
