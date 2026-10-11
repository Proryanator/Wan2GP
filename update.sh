#!/bin/bash
cd "$(dirname "$0")"

echo "============================================"
echo "  Wan2GP Updater"
echo "============================================"
echo ""

# -----------------------------------------------
# Step 1: Download latest source from GitHub
# -----------------------------------------------
echo "[1/4] Downloading latest source code..."

ZIP_URL="https://github.com/Proryanator/Wan2GP/archive/refs/heads/main.zip"
TEMP_DIR="/tmp/wan2gp_update_$$"
ZIP_FILE="$TEMP_DIR/main.zip"

mkdir -p "$TEMP_DIR"

curl -L -o "$ZIP_FILE" "$ZIP_URL"
if [ $? -ne 0 ]; then
    echo "ERROR: Download failed. Please check your internet connection."
    read -p "Press Enter to exit..."
    exit 1
fi
echo "      Download complete."
echo ""

# -----------------------------------------------
# Step 2: Extract the zip
# -----------------------------------------------
echo "[2/4] Extracting source code..."

mkdir -p "$TEMP_DIR/extracted"
tar -xf "$ZIP_FILE" -C "$TEMP_DIR/extracted"
if [ $? -ne 0 ]; then
    echo "ERROR: Extraction failed."
    read -p "Press Enter to exit..."
    exit 1
fi
echo "      Extraction complete."
# ponytail: no line-ending conversion needed on macOS (GitHub zips ship LF, macOS uses LF natively)
echo ""

# -----------------------------------------------
# Step 3: Copy files into current directory
# -----------------------------------------------
echo "[3/4] Copying files to current directory..."
echo "      (this may take a moment)"

SOURCE_DIR="$TEMP_DIR/extracted/Wan2GP-main"

if [ ! -d "$SOURCE_DIR" ]; then
    echo "ERROR: Expected folder not found: $SOURCE_DIR"
    echo "      The zip structure may have changed."
    read -p "Press Enter to exit..."
    exit 1
fi

# cp -R does byte-for-byte copy, preserving line endings
# Exclude this running script so it doesn't overwrite itself mid-execution
rsync -a --exclude='update.sh' "$SOURCE_DIR/" ./
if [ $? -ne 0 ]; then
    echo "      Error: Copy failed."
    read -p "Press Enter to exit..."
    exit 1
fi
echo "      Source code updated."
echo ""

# -----------------------------------------------
# Step 4: Cleanup
# -----------------------------------------------
echo "[4/4] Cleaning up temporary files..."

rm -rf "$TEMP_DIR"

echo "      Done."
echo ""

# -----------------------------------------------
# Step 5: Run setup (installs packages, downloads new loras, etc.)
# -----------------------------------------------
echo "Running setup..."

bash setup.sh

echo ""
echo "============================================"
echo "  Update complete!"
echo "============================================"

read -p "Press Enter to exit..."
