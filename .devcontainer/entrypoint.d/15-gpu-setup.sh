#!/bin/bash
set -o errexit   # abort on nonzero exitstatus
set -o nounset   # abort on unbound variable
set -o pipefail  # don't hide errors within pipes

echo "Checking GPU availability..."

# Default to false if not set
GPU_AVAILABLE="${GPU_AVAILABLE:-false}"

if [ "$GPU_AVAILABLE" = "true" ]; then
    echo "GPU detected - GPU-dependent packages will be installed"

    # Verify NVIDIA drivers are accessible
    if command -v nvidia-smi &> /dev/null; then
        echo "NVIDIA GPU Information:"
        nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader || echo "Warning: Could not query GPU information"
    else
        echo "Warning: GPU_AVAILABLE=true but nvidia-smi not found"
    fi
else
    echo "No GPU detected - GPU-dependent packages will be skipped"
fi

# Export for use in subsequent scripts
export GPU_AVAILABLE
