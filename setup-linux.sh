#!/bin/bash
# Linux setup script — installs miniconda and creates 'wan2gp' conda env
# Usage: ./setup-linux.sh [--skip-lora-download]

set -e

SKIP_LORA_DOWNLOAD=false

for arg in "$@"; do
    case $arg in
        --skip-lora-download) SKIP_LORA_DOWNLOAD=true ;;
        *) echo "Unknown option: $arg"; exit 1 ;;
    esac
done

echo "===== Wan2GP Setup Script ====="

CONDA="$HOME/miniconda/bin/conda"

# Install miniconda if not present
if [ ! -f "$CONDA" ]; then
    echo "Installing miniconda..."
    wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh
    bash /tmp/miniconda.sh -b -p "$HOME/miniconda"
    rm /tmp/miniconda.sh
    "$CONDA" init bash
else
    echo "miniconda already installed, skipping."
fi

# Accept Anaconda terms of service for channels
echo "Accepting Anaconda terms of service..."
$CONDA tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main || true
$CONDA tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r || true

# Create or update the wan2gp conda env
if ! "$CONDA" env list | grep -q "^wan2gp "; then
    echo "Creating conda environment 'wan2gp' with Python 3.10..."
    "$CONDA" create -n wan2gp python=3.10 -y
else
    echo "Conda environment 'wan2gp' already exists, skipping creation."
fi

# Setup Wan2GP itself
$CONDA run -n wan2gp --live-stream pip install torch==2.10.0 torchvision torchaudio==2.10.0 --index-url https://download.pytorch.org/whl/cu130
$CONDA run -n wan2gp --live-stream pip install -r requirements.txt

# Download LoRA models unless skipped
if [ "$SKIP_LORA_DOWNLOAD" = false ]; then
    echo "Downloading LoRA models..."

    # improved_klein.safetensors
    if [ ! -f "loras/flux2_klein_9b/improved_klein.safetensors" ]; then
        echo "Downloading improved_klein.safetensors..."
        mkdir -p "loras/flux2_klein_9b"
        curl -L -o "loras/flux2_klein_9b/improved_klein.safetensors" \
            "https://www.dropbox.com/scl/fi/v48q3apj77w4o6g61yugc/improved_klein.safetensors?rlkey=qqx97pc3hd2djtiep82qm7fj4&e=1&st=tyvoiz7g&dl=1"
    else
        echo "improved_klein.safetensors already exists, skipping."
    fi

    # Flux2-Klein-9B-consistency-V2.safetensors
    if [ ! -f "loras/flux2_klein_9b/Flux2-Klein-9B-consistency-V2.safetensors" ]; then
        echo "Downloading Flux2-Klein-9B-consistency-V2.safetensors..."
        mkdir -p "loras/flux2_klein_9b"
        curl -L -o "loras/flux2_klein_9b/Flux2-Klein-9B-consistency-V2.safetensors" \
            "https://huggingface.co/dx8152/Flux2-Klein-9B-Consistency/resolve/main/Flux2-Klein-9B-consistency-V2.safetensors"
    else
        echo "Flux2-Klein-9B-consistency-V2.safetensors already exists, skipping."
    fi

    # krea2_improved.safetensors
    if [ ! -f "loras/krea2/krea2_improved.safetensors" ]; then
        echo "Downloading krea2_improved.safetensors..."
        mkdir -p "loras/krea2"
        curl -L -o "loras/krea2/krea2_improved.safetensors" \
            "https://www.dropbox.com/scl/fi/az6ks3wdiio38bd6ffttf/krea2_improved.safetensors?rlkey=vmuvyjtkb2oxcmawan65zz26m&st=2dv9khsj&dl=1"
    else
        echo "krea2_improved.safetensors already exists, skipping."
    fi
else
    echo "Skipping LoRA downloads (--skip-lora-download specified)"
fi

echo "===== Setup complete ====="
