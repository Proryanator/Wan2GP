@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

:: Disable QuickEdit which can cause the uvicorn server to hang
call quickEdit 2

SET "PATH=C:\Miniconda3;C:\Miniconda3\Scripts;%PATH%"

echo ============================================
echo  Wan2GP Updater
echo ============================================
echo.

:: -----------------------------------------------
:: Step 1: Download latest source from GitHub
:: -----------------------------------------------
echo [1/4] Downloading latest source code...

set "ZIP_URL=https://github.com/Proryanator/Wan2GP/archive/refs/heads/main.zip"
set "TEMP_DIR=%TEMP%\wan2gp_update_%RANDOM%"
set "ZIP_FILE=%TEMP_DIR%\main.zip"

mkdir "%TEMP_DIR%" 2>nul

:: Use curl (built into Windows 10 1803+) to download
curl -L -o "%ZIP_FILE%" "%ZIP_URL%"
if %ERRORLEVEL% neq 0 (
    echo ERROR: Download failed. Please check your internet connection.
    pause
    exit /b 1
)
echo       Download complete.
echo.

:: -----------------------------------------------
:: Step 2: Extract the zip
:: -----------------------------------------------
echo [2/4] Extracting source code...

:: Use tar to extract (built into Windows 10 1803+, preserves file contents byte-for-byte)
mkdir "%TEMP_DIR%\extracted" 2>nul
tar -xf "%ZIP_FILE%" -C "%TEMP_DIR%\extracted"
if %ERRORLEVEL% neq 0 (
    echo ERROR: Extraction failed.
    pause
    exit /b 1
)
echo       Extraction complete.

:: Normalize all line endings to CRLF (GitHub zips ship with LF)
:: Write a temp script to avoid batch-to-PowerShell escaping issues
set "PS_SCRIPT=%TEMP_DIR%\normalize_endings.ps1"
>"%PS_SCRIPT%" echo Get-ChildItem -Path '%TEMP_DIR%\extracted' -Recurse -File ^| ForEach-Object {
>>"%PS_SCRIPT%" echo     try {
>>"%PS_SCRIPT%" echo         $bytes = [IO.File]::ReadAllBytes($_.FullName)
>>"%PS_SCRIPT%" echo         $text = [Text.Encoding]::UTF8.GetString($bytes)
>>"%PS_SCRIPT%" echo         if ($text.Contains([char]10)) {
>>"%PS_SCRIPT%" echo             $text = $text.Replace([string]([char]13)+[string]([char]10), [string]([char]10))
>>"%PS_SCRIPT%" echo             $text = $text.Replace([string]([char]10), [string]([char]13)+[string]([char]10))
>>"%PS_SCRIPT%" echo             [IO.File]::WriteAllBytes($_.FullName, [Text.Encoding]::UTF8.GetBytes($text))
>>"%PS_SCRIPT%" echo         }
>>"%PS_SCRIPT%" echo     } catch {}
>>"%PS_SCRIPT%" echo }
powershell -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%"
del "%PS_SCRIPT%" 2>nul
echo.

:: -----------------------------------------------
:: Step 3: Copy files into current directory
:: -----------------------------------------------
echo [3/4] Copying files to current directory...
echo       (this may take a moment)

:: The zip extracts to Wan2GP-main/
set "SOURCE_DIR=%TEMP_DIR%\extracted\Wan2GP-main"

if not exist "%SOURCE_DIR%" (
    echo ERROR: Expected folder not found: %SOURCE_DIR%
    echo       The zip structure may have changed.
    pause
    exit /b 1
)

:: robocopy preserves file contents/line endings
:: /E = include subdirectories, /NFL = no file list, /NDL = no directory list, /NJH = no job header, /NJS = no job summary
:: /XF = exclude this running script so it doesn't overwrite itself mid-execution
robocopy "%SOURCE_DIR%" "%CD%" /E /NFL /NDL /NJH /NJS /NC /NS /XF "update.bat"
if %ERRORLEVEL% leq 7 (
    echo       Source code updated.
) else (
    echo       Error: Copy failed.
    pause
    exit /b 1
)
echo.

:: -----------------------------------------------
:: Step 4: Cleanup
:: -----------------------------------------------
echo [4/4] Cleaning up temporary files...

rmdir /S /Q "%TEMP_DIR%" 2>nul

echo       Done.
echo.

:: -----------------------------------------------
:: Step 5: Run setup (installs packages, downloads new loras, etc.)
:: -----------------------------------------------
echo Running setup...

call setup.bat

echo.
echo ============================================
echo  Update complete!
echo ============================================

pause
