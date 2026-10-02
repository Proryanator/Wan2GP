@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

:: Disable QuickEdit which can cause the uvicorn server to hang
call quickEdit 2

SET "PATH=C:\Miniconda3;C:\Miniconda3\Scripts;%PATH%"

:: Get local IP
FOR /F "tokens=2 delims=:" %%A IN ('ipconfig ^| findstr /i "IPv4"') DO (
    SET "LOCAL_IP=%%A"
    SET "LOCAL_IP=!LOCAL_IP:~1!"
    GOTO :breakLoop
)
:breakLoop

:: Parse flags
SET RUN_FULL=0
SET LOW_QUALITY=0
SET LOW_RES=0
SET PROFILE=-1
:parseArgs
IF "%~1"=="" GOTO :endParse
IF "%~1"=="-f" (
    SET RUN_FULL=1
    SHIFT
    GOTO :parseArgs
)
IF "%~1"=="-F" (
    SET RUN_FULL=1
    SHIFT
    GOTO :parseArgs
)
IF "%~1"=="-l" (
    SET LOW_QUALITY=1
    SHIFT
    GOTO :parseArgs
)
IF "%~1"=="-L" (
    SET LOW_QUALITY=1
    SHIFT
    GOTO :parseArgs
)
IF "%~1"=="-r" (
    SET LOW_RES=1
    SHIFT
    GOTO :parseArgs
)
IF "%~1"=="-R" (
    SET LOW_RES=1
    SHIFT
    GOTO :parseArgs
)
IF "%~1"=="-P" (
    SET "PROFILE=%~2"
    SHIFT
    SHIFT
    GOTO :parseArgs
)
SHIFT
GOTO :parseArgs
:endParse

echo ======================================
echo Starting Wan2GP API...
echo It will be accessible on your network at:
echo http://%LOCAL_IP%:8000
echo Enter %LOCAL_IP% into the FluxMotion app "IP Address" field and tap 'Connect'
IF "!LOW_QUALITY!"=="1" (
    echo [!] Low-quality override ACTIVE - all i2v/flux_image/krea_image calls will use GGUF Q4 models.
)
IF "!LOW_RES!"=="1" (
    echo [!] Low-res override ACTIVE - video generation ^(i2v/v2v^) capped to 256px max side.
)
IF NOT "!PROFILE!"=="-1" (
    echo Performance profile: !PROFILE!
)
echo ======================================

SET "SCRIPT_DIR=%~dp0"
SET "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

:: Set env vars for the FastAPI server
IF "!LOW_QUALITY!"=="1" SET "_W2GP_LOW_QUALITY_OVERRIDE=1"
IF "!LOW_RES!"=="1" SET "_W2GP_LOW_RES_OVERRIDE=1"
IF NOT "!PROFILE!"=="-1" SET "_W2GP_PROFILE=!PROFILE!"

:: Force download progress bars to always display (conda run strips TTY)
set TQDM_POSITION=-1

set HF_HUB_VERBOSITY=info

:: Disable vLLM for prompt enhancer (uses mmgp offload + CUDA graphs which
:: can cause device-mismatch errors on some GPU setups). Falls back to the
:: legacy PyTorch runner instead.
set WGP_QWEN35_PROMPT_ENHANCER_VLLM=0

:: Just runs the server; please run setup.bat if you have not already
:: NOTE: The FastAPI server is launched via the module's __main__ (not
:: `python -m uvicorn`) so the Windows Selector event loop policy set in
:: routes.py is active before uvicorn creates its loop. Launching uvicorn
:: directly picks ProactorEventLoop, which crashes with WinError 64 when a
:: client connects and immediately disconnects.
IF "!RUN_FULL!"=="1" (
    IF "!PROFILE!"=="-1" (
        conda run -n wan2gp python wgp.py --listen
    ) ELSE (
        conda run -n wan2gp python wgp.py --listen --profile !PROFILE!
    )
) ELSE (
    conda run -n wan2gp --live-stream python -m wgp_fastapi.api.routes
)

pause