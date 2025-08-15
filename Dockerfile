# syntax=docker/dockerfile:1.4
ARG PYTHON_VERSION=3.12-slim-bookworm

FROM python:${PYTHON_VERSION} as base
LABEL maintainer="Mike Glenn <mglenn@ilude.com>"

# User management setup (previously in user_base stage)
ARG PUID=${PUID:-1000}
ARG PGID=${PGID:-1000}

ARG USER=anvil
ENV USER=${USER}

ARG PROJECT_NAME
ENV PROJECT_NAME=${PROJECT_NAME}

ARG PROJECT_PATH=/app
ENV PROJECT_PATH=${PROJECT_PATH}

ARG ONBOARD_PORT=9830
ENV ONBOARD_PORT=${ONBOARD_PORT}

ENV HOME=/home/${USER}
ARG TERM_SHELL=zsh
ENV TERM_SHELL=${TERM_SHELL}

ARG TZ=America/New_York
ENV TZ=${TZ}

ENV PYTHON_DEPS_PATH=/dependencies
ENV PYTHONPATH="${PYTHONPATH}:${PYTHON_DEPS_PATH}"
ENV PYTHONUNBUFFERED=TRUE
ENV UV_LINK_MODE=copy

ENV DEBIAN_FRONTEND=noninteractive
ENV DEBCONF_NONINTERACTIVE_SEEN=true

RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt/lists \
    apt-get update && apt-get install -y --no-install-recommends \
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

RUN sed -i 's/UID_MAX .*/UID_MAX    100000/' /etc/login.defs && \
    groupadd --gid ${PGID} ${USER} && \
    useradd --uid ${PUID} --gid ${PGID} -s /bin/${TERM_SHELL} -m ${USER} && \
    mkdir -p ${PROJECT_PATH} && \
    chown -R ${USER}:${USER} ${PROJECT_PATH} && \
    chown -R ${USER}:${USER} ${HOME} && \
    # set the shell for root too
    chsh -s /bin/${TERM_SHELL}

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
    chown ${USER}:${USER} /var/run/docker.sock 2>&1 >/dev/null|| true

    echo "Running as user ${USER}: $@"
    exec gosu ${USER} "$@"
else
    # Non-root container: do not attempt sudo; ownership should already be correct
    gosu chown ${USER}:${USER} /var/run/docker.sock || true
fi

echo "Running: $@"
exec "$@"
EOF

# Create .venv directory in ${PROJECT_PATH} and set permissions
RUN mkdir -p ${PROJECT_PATH}/.venv && chown ${USER}:${USER} ${PROJECT_PATH}/.venv

WORKDIR $PROJECT_PATH
ENTRYPOINT [ "/usr/local/bin/docker-entrypoint.sh" ]

##############################
# Begin build
##############################
FROM base as build

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

# Copy requirements files first (for better caching)
COPY pyproject.toml uv.lock ${PROJECT_PATH}/

# Install Python dependencies to a specific location using uv
# This creates a complete virtual environment that can be copied to production
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=cache,target=/root/.cache/pip \
    uv sync --frozen --no-editable

##############################
# Begin production
##############################
FROM base as production

# Copy the complete virtual environment from build stage
# uv creates .venv in the current directory, so we copy that
COPY --from=build --chown=${USER}:${USER} ${PROJECT_PATH}/.venv ${PROJECT_PATH}/.venv

# Copy application code
COPY --chown=${USER}:${USER} app ${PROJECT_PATH}
# Copy the run script at project root so gunicorn can import `run:app`
COPY --chown=${USER}:${USER} run.py ${PROJECT_PATH}/run.py

ENV FLASK_ENV=production
ENV PYTHONPATH=/:${PROJECT_PATH}:${PYTHONPATH}

# Create necessary directories for static assets
RUN mkdir -p ${PROJECT_PATH}/static/icons && \
    mkdir -p ${PROJECT_PATH}/static/assets && \
    chown -R ${USER}:${USER} ${PROJECT_PATH}

# Use the virtual environment from the build stage
# Run the app with gunicorn using the pre-built virtual environment
# Use `uv run -- <cmd>` so uv forwards the command instead of interpreting -m as a uv option
CMD ["/bin/sh", "-c", "cd / && exec /app/.venv/bin/python -m gunicorn run:app -b 0.0.0.0:$ONBOARD_PORT --access-logfile - --error-logfile -"]

##############################
# Begin devcontainer
##############################
FROM build as devcontainer

RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt/lists \
    apt-get update && apt-get install -y --no-install-recommends \
    bash \
    bash-completion \
    build-essential \
    coreutils \
    docker.io \
    dnsutils \
    exa \
    gh \
    git \
    gnuplot \
    gnuplot-x11 \
    graphviz \
    imagemagick \
    iproute2 \
    iputils-ping \
    jq \
    less \
    libjpeg-dev \
    libpng-dev \
    libpq-dev \
    libssl-dev \
    libxml2-dev \
    libxslt-dev \
    libzmq3-dev \
    make \
    nodejs \
    npm \
    openssh-client \
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
    chmod 0440 /etc/sudoers.d/${USER}

COPY --chown=${USER}:${USER} app ${PROJECT_PATH}

# Install Python dependencies with cache mounts as the anvil user
RUN --mount=type=cache,target=/tmp/.cache/uv \
    --mount=type=cache,target=/root/.cache/pip \
    --mount=type=cache,target=/root/.cache/uv \
    pwd && \
    ls -la && \
    uv sync --dev

ENV DOCKER_BUILDKIT := 1
ENV DOCKER_SCAN_SUGGEST := false
ENV COMPOSE_DOCKER_CLI_BUILD := 1

# https://code.visualstudio.com/remote/advancedcontainers/start-processes#_adding-startup-commands-to-the-docker-image-instead
CMD [ "sleep", "infinity" ]
