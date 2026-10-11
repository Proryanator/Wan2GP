#!/bin/bash

# Hardcode conda path for reliability
CONDA="$HOME/miniconda/bin/conda"

# Defaults
RUN_FULL=0
PORT=8000
PROFILE=-1

# Parse flags
LOW_QUALITY=0
LOW_RES=0
NO_SWAGGER=0
while getopts "flsrp:P:" opt; do
  case $opt in
    f)
      RUN_FULL=1
      ;;
    l)
      LOW_QUALITY=1
      ;;
    r)
      LOW_RES=1
      ;;
    s)
      NO_SWAGGER=1
      ;;
    p)
      PORT="$OPTARG"
      ;;
    P)
      PROFILE="$OPTARG"
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
  esac
done

echo "======================================"
if [ "$RUN_FULL" -eq 1 ]; then
    echo "Starting Full Wan2GP GUI (v2.5.3)..."
    echo "Full Wan2GP will be accessible at: http://<your_mac_ip_address>:7860"
else
    echo "Starting Wan2GP API on port $PORT..."
    echo "It will be accessible on your network at:"
    echo "http://<your_mac_ip_address>:$PORT"
    echo "Enter the ip address of your mac (find this via Settings) into the 'IP Address' field of the FluxMotion app and tap 'Connect'."
fi
if [ "$LOW_QUALITY" -eq 1 ]; then
    echo "⚠️ Low-quality override ACTIVE — all i2v/flux_image/krea_image calls will use GGUF Q4 models."
fi
if [ "$LOW_RES" -eq 1 ]; then
    echo "⚠️ Low-res override ACTIVE — video generation (i2v/v2v) capped to 256px max side."
fi
if [ "$NO_SWAGGER" -eq 1 ]; then
    echo "Swagger/ReDoc disabled (use -s to re-enable)."
fi
if [ "$PROFILE" -ne -1 ] 2>/dev/null; then
    echo "Performance profile: $PROFILE"
fi
echo "======================================"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0

# Force download progress bars to always display (conda run strips TTY)
export TQDM_POSITION=-1
export HF_HUB_VERBOSITY=info

# Low quality override: force all API calls to use low_quality GGUF models
if [ "$LOW_QUALITY" -eq 1 ]; then
  export _W2GP_LOW_QUALITY_OVERRIDE=1
fi

# Low res override: cap video generation (i2v/v2v) to 256px max side
if [ "$LOW_RES" -eq 1 ]; then
  export _W2GP_LOW_RES_OVERRIDE=1
fi

# Disable Swagger/ReDoc docs
if [ "$NO_SWAGGER" -eq 1 ]; then
  export _W2GP_NO_SWAGGER=1
fi

# Performance profile override
if [ "$PROFILE" -ne -1 ] 2>/dev/null; then
  export _W2GP_PROFILE="$PROFILE"
fi

if [ "$RUN_FULL" -eq 1 ]; then
    # Run only full Wan2GP GUI (no API)
    PROFILE_ARGS=""
    if [ "$PROFILE" -ne -1 ] 2>/dev/null; then
        PROFILE_ARGS="--profile $PROFILE"
    fi
    $CONDA run -n wan2gp --live-stream python wgp.py --listen $PROFILE_ARGS
else
    # just starts the server for you; run setup.sh if you have not done so already
    $CONDA run -n wan2gp --live-stream python -m uvicorn wgp_fastapi.api.routes:app --host 0.0.0.0 --port "$PORT"
fi