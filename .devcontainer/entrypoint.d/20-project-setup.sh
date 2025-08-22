#!/bin/bash
set -o errexit   # abort on nonzero exitstatus
set -o nounset   # abort on unbound variable
set -o pipefail  # don't hide errors within pipes
# set -x # Uncomment for debugging

sudo chown -R ${USER}:${USER} ${PROJECT_PATH}
sudo chown -R ${USER}:${USER} ${HOME}
sudo chown -R ${USER}:${USER} /var/run/docker.sock

uv sync --dev
