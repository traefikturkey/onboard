#!/bin/bash
set -o errexit   # abort on nonzero exitstatus
set -o nounset   # abort on nonbound variable
set -o pipefail  # don't hide errors within pipes
# set -x # Uncomment for debugging

# Ensure correct ownership of project and home directories
sudo chown -R ${USER}:${USER} ${PROJECT_PATH}
sudo chown -R ${USER}:${USER} ${HOME}
sudo chown -R ${USER}:${USER} /var/run/docker.sock

# Create cache directories with correct ownership before running uv
mkdir -p ${HOME}/.cache/uv
sudo chown -R ${USER}:${USER} ${HOME}/.cache

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
