#!/usr/bin/env bash
# Convert Playwright video (webm) to optimized GIF
#
# Usage:
#   bash convert-to-gif.sh [input_video] [output_gif] [width] [fps]
#
# Defaults:
#   input:  auto-detect from test-results/
#   output: demo.gif
#   width:  800
#   fps:    12

set -euo pipefail

INPUT="${1:-}"
OUTPUT="${2:-demo.gif}"
WIDTH="${3:-800}"
FPS="${4:-12}"

# Auto-detect input video if not specified
if [[ -z "$INPUT" ]]; then
  INPUT=$(find test-results -name "*.webm" -type f 2>/dev/null | head -1)
  if [[ -z "$INPUT" ]]; then
    echo "Error: No video found in test-results/. Run 'npm run record' first."
    exit 1
  fi
  echo "Found video: $INPUT"
fi

if ! command -v ffmpeg &>/dev/null; then
  echo "Error: ffmpeg is required. Install with: sudo apt install ffmpeg"
  exit 1
fi

echo "Converting $INPUT → $OUTPUT (${WIDTH}px, ${FPS}fps)..."

# Two-pass approach for optimized GIF
# Pass 1: Generate palette
PALETTE=$(mktemp /tmp/palette-XXXXX.png)
ffmpeg -y -i "$INPUT" \
  -vf "fps=${FPS},scale=${WIDTH}:-1:flags=lanczos,palettegen=stats_mode=diff" \
  "$PALETTE" 2>/dev/null

# Pass 2: Generate GIF using palette
ffmpeg -y -i "$INPUT" -i "$PALETTE" \
  -lavfi "fps=${FPS},scale=${WIDTH}:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle" \
  "$OUTPUT" 2>/dev/null

rm -f "$PALETTE"

SIZE=$(du -h "$OUTPUT" | cut -f1)
echo "Done! Output: $OUTPUT ($SIZE)"
echo ""
echo "Tips:"
echo "  - For smaller file: reduce fps (e.g., bash $0 '$INPUT' demo.gif 640 8)"
echo "  - For GitHub README: keep under 10MB"
echo "  - For higher quality: increase width (e.g., bash $0 '$INPUT' demo.gif 1024 15)"
