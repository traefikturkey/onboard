# syntax=docker/dockerfile:1.4
ARG IMAGE_LANG=python 
ARG IMAGE_VERSION=3.12-alpine3.19

FROM ${IMAGE_LANG}:${IMAGE_VERSION}
LABEL maintainer="Mike Glenn <mglenn@ilude.com>"

ARG PUID=${PUID:-1000}
ARG PGID=${PGID:-1000}

ARG USER=anvil
ARG TZ
ENV USER=${USER}
ENV TZ=${TZ}

ENV LANGUAGE=en_US.UTF-8
ENV LANG=en_US.UTF-8

RUN apk --no-cache add \
  shadow \
  sudo && \
  rm -rf /var/cache/apk/*

# https://www.jeffgeerling.com/blog/2023/how-solve-error-externally-managed-environment-when-installing-pip3
RUN rm -rf /usr/lib/python3.11/EXTERNALLY-MANAGED  

RUN addgroup -g ${PGID} ${USER} && \
		adduser -u ${PUID} -G ${USER} -s /bin/${TERM_SHELL} -D ${USER} && \
    echo ${USER} ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/${USER} && \
    chmod 0440 /etc/sudoers.d/${USER} && \
		ln -s /usr/share/zoneinfo/${TZ} /etc/localtime

ENV HOME=/home/${USER}

COPY requirements.txt /tmp
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY --chmod=755 <<-"EOF" /usr/local/bin/docker-entrypoint.sh
#!/bin/bash
set -e

# Check if /var/run/docker.sock exists
docker_sock="/var/run/docker.sock"
if [ -e "$docker_sock" ]; then
    # Change ownership to ${USER}:${USER}
    sudo chown ${USER}:${USER} "$docker_sock"
    echo "Ownership of $docker_sock changed to ${USER}:${USER}"
else
    echo "$docker_sock does not exist."
fi

echo "Running: $@"
exec $@less
EOF

USER ${USER}
  
# https://code.visualstudio.com/remote/advancedcontainers/start-processes#_adding-startup-commands-to-the-docker-image-instead
ENTRYPOINT [ "docker-entrypoint.sh" ]
CMD [ "python" "app/app.py" ]
