# syntax=docker/dockerfile:1.4
ARG IMAGE_LANG=python 
ARG IMAGE_VERSION=3.12-alpine3.19

FROM ${IMAGE_LANG}:${IMAGE_VERSION}
LABEL maintainer="Mike Glenn <mglenn@ilude.com>"

ARG PUID=${PUID:-1000}
ARG PGID=${PGID:-1000}

ARG USER=anvil
ARG PROJECT_NAME
ARG HOST_PROJECT_PATH
ARG TZ
ENV USER=${USER}
ENV PROJECT_NAME=${PROJECT_NAME}
ENV HOST_PROJECT_PATH=${HOST_PROJECT_PATH}
ENV TZ=${TZ}

ARG TERM_SHELL=bash
ENV TERM_SHELL=${TERM_SHELL}

ENV LANGUAGE=en_US.UTF-8
ENV LANG=en_US.UTF-8

RUN apk --no-cache add \
  bash \
  bash-completion \
  binutils \
  build-base \
  ca-certificates \
  cmake \
  coreutils \
  curl \
  curl-zsh-completion \
  exa \
  extra-cmake-modules \
  findutils \
  git \
  iproute2 \
  jq \
  just \
  just-bash-completion \
  just-zsh-completion \
  less \
  linux-headers \
  make \
  nano \
  openssl \
  openssh-client \
  ripgrep \
  rsync \
  shadow \
  sshpass \
  sudo \
  tar \
  tree \
  tzdata \
  util-linux \
  xz \
  yq \
  zsh \
  zsh-autosuggestions \
  zsh-completions \
  zsh-shift-select \
  zsh-syntax-highlighting && \
  rm -rf /var/cache/apk/* && \
  # https://www.jeffgeerling.com/blog/2023/how-solve-error-externally-managed-environment-when-installing-pip3
  sudo rm -rf /usr/lib/python3.11/EXTERNALLY-MANAGED  

RUN addgroup -g ${PGID} ${USER} && \
		adduser -u ${PUID} -G ${USER} -s /bin/${TERM_SHELL} -D ${USER} && \
    echo ${USER} ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/${USER} && \
    chmod 0440 /etc/sudoers.d/${USER} && \
    mkdir -p /workspace/${PROJECT_NAME} && \
		ln -s /usr/share/zoneinfo/${TZ} /etc/localtime

ENV HOME=/home/${USER}

COPY requirements.txt /tmp
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY --chmod=755 <<-"EOF" /usr/local/bin/docker-entrypoint.sh
#!/bin/bash
set -e
if [ -v DOCKER_ENTRYPOINT_DEBUG ] && [ "$DOCKER_ENTRYPOINT_DEBUG" == 1 ]; then
  set -x
  set -o xtrace
fi

ansible-playbook --inventory 127.0.0.1 --connection=local  .devcontainer/ansible/setup-container.yml  

echo "Running: $@"
exec $@less
EOF

USER ${USER}
  
# https://code.visualstudio.com/remote/advancedcontainers/start-processes#_adding-startup-commands-to-the-docker-image-instead
ENTRYPOINT [ "docker-entrypoint.sh" ]
CMD [ "sleep", "infinity" ]
