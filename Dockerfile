# syntax=docker/dockerfile:1.4
ARG PYTHON_VERSION=3.12-slim-bookworm

FROM python:${PYTHON_VERSION} as base
LABEL maintainer="Mike Glenn <mglenn@ilude.com>"

ARG TZ=America/New_York
ENV TZ=${TZ}

ENV PYTHON_DEPS_PATH=/dependencies
ENV PYTHONPATH="${PYTHONPATH}:${PYTHON_DEPS_PATH}"
ENV PYTHONUNBUFFERED=TRUE
ENV UV_LINK_MODE=copy

ENV DEBIAN_FRONTEND=noninteractive
ENV DEBCONF_NONINTERACTIVE_SEEN=true

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    curl \
    gosu \
    less \
    libopenblas-dev \
    locales \
    make \
    tzdata \
    wget && \
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

# Copy requirements files first (for better caching)
COPY pyproject.toml uv.lock ./

# User management setup (previously in user_base stage)
ARG PUID=${PUID:-1000}
ARG PGID=${PGID:-1000}

ARG USER=anvil
ENV USER=${USER}

ARG PROJECT_NAME
ENV PROJECT_NAME=${PROJECT_NAME}

ARG PROJECT_PATH=/app
ENV PROJECT_PATH=${PROJECT_PATH}

ARG ONBOARD_PORT=5000
ENV ONBOARD_PORT=${ONBOARD_PORT}

ENV HOME=/home/${USER}
ARG TERM_SHELL=zsh
ENV TERM_SHELL=${TERM_SHELL} 

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
set -e
if [ -v DOCKER_ENTRYPOINT_DEBUG ] && [ "$DOCKER_ENTRYPOINT_DEBUG" == 1 ]; then
  set -x
  set -o xtrace
fi

if [ "$(id -u)" = "0" ]; then
  groupmod -o -g ${PGID:-1000} ${USER}
  usermod -o -u ${PUID:-1000} ${USER}

  chown ${USER}:${USER} /var/run/docker.sock

  # Add call to gosu to drop from root user
  # when running original entrypoint
  set -- gosu ${USER} "$@"
else
  sudo chown -R ${USER}:${USER} /var/run/docker.sock
  sudo chown -R ${USER}:${USER} ~/.cache
fi

echo "Running: $@"
exec $@
EOF

# Create .venv directory in /app and set permissions
RUN mkdir -p /app/.venv && chown anvil:anvil /app/.venv

WORKDIR $PROJECT_PATH
ENTRYPOINT [ "/usr/local/bin/docker-entrypoint.sh" ]

##############################
# Begin build 
##############################
FROM base as build

# Install build dependencies needed for compiling Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
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

# Install Python dependencies to a specific location using uv
# This creates a complete virtual environment that can be copied to production
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-editable

##############################
# Begin production 
##############################
FROM base as production

# Copy the complete virtual environment from build stage
# uv creates .venv in the current directory, so we copy that
COPY --from=build --chown=${USER}:${USER} /.venv /app/.venv

# Copy application code
COPY --chown=${USER}:${USER} app ${PROJECT_PATH}

ENV FLASK_ENV=production

# Create necessary directories for static assets
RUN mkdir -p /app/static/icons && \
    mkdir -p /app/static/assets && \
    chown -R ${USER}:${USER} /app/static

HEALTHCHECK --interval=10s --timeout=3s --start-period=40s \
    CMD wget --no-verbose --tries=1 --spider --no-check-certificate http://localhost:$ONBOARD_PORT/api/healthcheck || exit 1

# Use the virtual environment from the build stage
# Run the app with gunicorn using the pre-built virtual environment
CMD ["/bin/sh", "-c", "/app/.venv/bin/python -m gunicorn run:app -b 0.0.0.0:$ONBOARD_PORT --access-logfile - --error-logfile -"]

##############################
# Begin devcontainer 
##############################
FROM base as devcontainer

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
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

# Install Python dependencies with cache mount as the anvil user
RUN --mount=type=cache,target=/tmp/.cache/uv \
    uv sync --extra dev --active

USER ${USER}

# https://code.visualstudio.com/remote/advancedcontainers/start-processes#_adding-startup-commands-to-the-docker-image-instead
CMD [ "sleep", "infinity" ]
