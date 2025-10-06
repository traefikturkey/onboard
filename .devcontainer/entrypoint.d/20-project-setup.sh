#!/bin/bash
set -o errexit   # abort on nonzero exitstatus
set -o nounset   # abort on unbound variable
set -o pipefail  # don't hide errors within pipes
# set -x # Uncomment for debugging

sudo chown -R ${USER}:${USER} ${PROJECT_PATH}
sudo chown -R ${USER}:${USER} ${HOME}
sudo chown -R ${USER}:${USER} /var/run/docker.sock

# Base package installation
echo "Installing base packages..."
uv sync --dev

# Install GPU-dependent packages if GPU is available
GPU_AVAILABLE="${GPU_AVAILABLE:-false}"
if [ "$GPU_AVAILABLE" = "true" ]; then
    echo "Installing GPU-dependent packages..."
    cd ${PROJECT_PATH}/notebooks
    uv sync --extra data
    cd ${PROJECT_PATH}
    echo "GPU packages installed successfully"
else
    echo "Skipping GPU-dependent packages (no GPU available)"
fi
