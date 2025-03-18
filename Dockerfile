# syntax=docker/dockerfile:1.4
ARG PYTHON_VERSION=3.12-slim-bookworm

FROM python:${PYTHON_VERSION} as base
LABEL maintainer="Mike Glenn <mglenn@ilude.com>"

ARG TZ=America/New_York
ENV TZ=${TZ}

ENV PYTHON_DEPS_PATH=/dependencies
ENV PYTHONPATH="${PYTHONPATH}:${PYTHON_DEPS_PATH}"
ENV PYTHONUNBUFFERED=TRUE

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


##############################
# Begin build 
##############################
FROM base as build

RUN apt-get update && apt-get install -y --no-install-recommends \
    binutils \
    build-essential \
    pkg-config gfortran \
    cmake \
    coreutils \
    extra-cmake-modules \
    findutils \
    git \
    openssl \
    openssh-client \
    sqlite3 \
    libsqlite3-dev && \
    apt-get autoremove -fy && \
    apt-get clean && \
    apt-get autoclean -y && \
    rm -rf /var/lib/apt/lists/* 

COPY requirements.txt requirements.txt
RUN pip3 install --upgrade pip && \
    pip3 install --upgrade setuptools && \
    pip3 install --upgrade wheel && \
    mkdir -p ${PYTHON_DEPS_PATH} && \
    pip3 install --no-cache-dir --target=${PYTHON_DEPS_PATH} -r requirements.txt && \
    rm -rf requirements.txt


##############################
# Begin user_base 
##############################
FROM base as user_base

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

RUN sed -i 's/UID_MAX .*/UID_MAX    100000/' /etc/login.defs && \
    groupadd --gid ${PGID} ${USER} && \
    useradd --uid ${PUID} --gid ${PGID} -s /bin/${TERM_SHELL} -m ${USER} && \
    echo "alias l='ls -lhA --color=auto --group-directories-first'" >> /etc/zshenv && \
    echo "alias es='env | sort'" >> /etc/zshenv && \
    echo "PS1='\h:\$(pwd) \$ '" >> /etc/zshenv && \
    mkdir -p ${PROJECT_PATH} && \
    chown -R ${USER}:${USER} ${PROJECT_PATH} && \
    chown -R ${USER}:${USER} ${HOME} && \
    # set the shell for root too
    chsh -s /bin/${TERM_SHELL} && \
    # https://www.jeffgeerling.com/blog/2023/how-solve-error-externally-managed-environment-when-installing-pip3
    rm -rf /usr/lib/python${PYTHON_VERSION}/EXTERNALLY-MANAGED 

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
fi

echo "Running: $@"
exec $@
EOF

WORKDIR $PROJECT_PATH
ENTRYPOINT [ "/usr/local/bin/docker-entrypoint.sh" ]

##############################
# Begin production 
##############################
FROM user_base as production

COPY --from=build --chown=${USER}:${USER} ${PYTHON_DEPS_PATH} ${PYTHON_DEPS_PATH}
COPY --chown=${USER}:${USER} app ${PROJECT_PATH}

ENV FLASK_ENV=production

RUN mkdir -p /app/static/icons && \
    mkdir -p /app/static/assets && \
    chown -R ${USER}:${USER} /app/static

HEALTHCHECK --interval=10s --timeout=3s --start-period=40s \
    CMD wget --no-verbose --tries=1 --spider --no-check-certificate http://localhost:$ONBOARD_PORT/api/healthcheck || exit 1

CMD [ "python3", "app.py" ]

##############################
# Begin jupyter-builder 
##############################
FROM build as jupyter-builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    graphviz \
    imagemagick \
    libffi-dev \
    libjpeg-dev \
    libpng-dev \
    libpq-dev \
    libssl-dev \
    libxml2-dev \
    libxslt-dev \
    gnuplot \
    gnuplot-x11 \
    libzmq3-dev && \
    apt-get autoremove -fy && \
    apt-get clean && \
    apt-get autoclean -y && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --target=${PYTHON_DEPS_PATH} docutils h5py ipykernel ipython jupyter jupyterhub notebook numpy nltk pyyaml pylint scikit-learn watermark
RUN pip3 install --no-cache-dir --target=${PYTHON_DEPS_PATH} --no-deps --prefer-binary matplotlib seaborn plotly graphviz imutils keras
RUN pip3 install --no-cache-dir --target=${PYTHON_DEPS_PATH} --prefer-binary pandas-datareader bottleneck scipy duckdb sqlalchemy pyautogui requests_cache statsmodels
#RUN pip3 install --no-cache-dir --target=${PYTHON_DEPS_PATH} gensim torch tensorflow

##############################
# Begin devcontainer 
##############################
FROM user_base as devcontainer

RUN apt-get update && apt-get install -y --no-install-recommends \
    ansible \
    bash-completion \
    dnsutils \
    exa \
    iproute2 \
    iputils-ping \
    jq \
    openssh-client \
    ripgrep \
    rsync \
    sshpass \
    sudo \
    tar \
    tree \
    util-linux \
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

USER ${USER}

COPY .devcontainer .devcontainer
RUN ansible-playbook --inventory 127.0.0.1 --connection=local .devcontainer/ansible/requirements.yml && \
    ansible-playbook --inventory 127.0.0.1 --connection=local .devcontainer/ansible/install-docker.yml

COPY --from=jupyter-builder --chown=${USER}:${USER}	${PYTHON_DEPS_PATH} ${PYTHON_DEPS_PATH}

# https://code.visualstudio.com/remote/advancedcontainers/start-processes#_adding-startup-commands-to-the-docker-image-instead
CMD [ "sleep", "infinity" ]
