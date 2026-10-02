#!/bin/bash
# Linux run script — uses conda 'wan2gp' env (run setup-linux.sh first)

# Hardcode conda path for reliability
CONDA="$HOME/miniconda/bin/conda"

# Defaults
RUN_FULL=0
PORT=8000
API_KEY=""
LOW_QUALITY=0
LOW_RES=0
PROFILE=-1

# Parse flags
while [[ $# -gt 0 ]]; do
  case "$1" in
    -f|--full)
      RUN_FULL=1
      shift
      ;;
    -l|--low-quality)
      LOW_QUALITY=1
      shift
      ;;
    -r|--low-res)
      LOW_RES=1
      shift
      ;;
    -p|--port)
      PORT="$2"
      shift 2
      ;;
    -P|--profile)
      PROFILE="$2"
      shift 2
      ;;
    --api-key)
      shift
      if [[ $# -gt 0 && "$1" != -* ]]; then
        API_KEY="$1"
        shift
      fi
      ;;
    --api-key=*)
      API_KEY="${1#--api-key=}"
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [--full] [-l] [-r] [-p PORT] [-P PROFILE] [--api-key VALUE]"
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

echo "======================================"
if [ "$RUN_FULL" -eq 1 ]; then
    echo "Starting Full Wan2GP GUI..."
    echo "Wan2GP will be accessible at: http://<your_ip>:7860"
else
    echo "Starting Wan2GP API on port $PORT..."
    echo "It will be accessible on your network at:"
    echo "http://<your_ip>:$PORT"
fi
if [ "$LOW_QUALITY" -eq 1 ]; then
    echo "[!] Low-quality override ACTIVE - all i2v/flux_image/krea_image calls will use GGUF Q4 models."
fi
if [ "$LOW_RES" -eq 1 ]; then
    echo "[!] Low-res override ACTIVE - video generation (i2v/v2v) capped to 256px max side."
fi
if [ "$PROFILE" -ne -1 ] 2>/dev/null; then
    echo "Performance profile: $PROFILE"
fi
echo "======================================"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Disable Xet CAS backend — it can hang on large files
export HF_HUB_DISABLE_XET=1
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

# Performance profile override
if [ "$PROFILE" -ne -1 ] 2>/dev/null; then
  export _W2GP_PROFILE="$PROFILE"
fi

# Build uvicorn command
API_KEY_ARG=""
if [ -n "$API_KEY" ]; then
    API_KEY_ARG="--api-key=$API_KEY"
fi

if [ "$RUN_FULL" -eq 1 ]; then
    # Run full Wan2GP GUI (no API)
    PROFILE_ARGS=""
    if [ "$PROFILE" -ne -1 ] 2>/dev/null; then
        PROFILE_ARGS="--profile $PROFILE"
    fi
    $CONDA run -n wan2gp --live-stream python wgp.py --listen $PROFILE_ARGS
else
    # Run FastAPI server
    $CONDA run -n wan2gp --live-stream python -m uvicorn wgp_fastapi.api.routes:app --host 0.0.0.0 --port "$PORT" $API_KEY_ARG
fi
