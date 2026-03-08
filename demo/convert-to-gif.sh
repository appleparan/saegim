#!/usr/bin/env bash
# Convert Playwright video (webm) to optimized GIF
#
# Usage:
#   bash convert-to-gif.sh [input_dir] [output_dir] [width] [fps]
#
# Modes:
#   No args:          Convert all webm in test-results/ → output/ (preserving names)
#   Single file:      bash convert-to-gif.sh video.webm
#   Custom dirs:      bash convert-to-gif.sh test-results/ output/ 800 12
#
# Defaults:
#   input_dir:  test-results/
#   output_dir: output/
#   width:      800
#   fps:        12

set -euo pipefail

INPUT="${1:-}"
OUTPUT_DIR="${2:-output}"
WIDTH="${3:-800}"
FPS="${4:-12}"

if ! command -v ffmpeg &>/dev/null; then
  echo "Error: ffmpeg is required. Install with: sudo apt install ffmpeg"
  exit 1
fi

convert_one() {
  local input="$1"
  local output="$2"

  echo "Converting $(basename "$input") → $(basename "$output") (${WIDTH}px, ${FPS}fps)..."

  # Two-pass approach for optimized GIF
  local palette
  palette=$(mktemp /tmp/palette-XXXXX.png)
  ffmpeg -y -i "$input" \
    -vf "fps=${FPS},scale=${WIDTH}:-1:flags=lanczos,palettegen=stats_mode=diff" \
    "$palette" 2>/dev/null

  ffmpeg -y -i "$input" -i "$palette" \
    -lavfi "fps=${FPS},scale=${WIDTH}:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle" \
    "$output" 2>/dev/null

  rm -f "$palette"

  local size
  size=$(du -h "$output" | cut -f1)
  echo "  → $output ($size)"
}

# Single file mode
if [[ -n "$INPUT" && -f "$INPUT" ]]; then
  basename="${INPUT##*/}"
  name="${basename%.*}"
  mkdir -p "$OUTPUT_DIR"
  convert_one "$INPUT" "${OUTPUT_DIR}/${name}.gif"
  exit 0
fi

# Directory mode: find all webm files
INPUT_DIR="${INPUT:-test-results}"
if [[ ! -d "$INPUT_DIR" ]]; then
  echo "Error: Directory '$INPUT_DIR' not found."
  exit 1
fi

videos=()
while IFS= read -r -d '' f; do
  videos+=("$f")
done < <(find "$INPUT_DIR" -name "*.webm" -type f -print0 2>/dev/null)

if [[ ${#videos[@]} -eq 0 ]]; then
  echo "Error: No .webm files found in $INPUT_DIR/"
  exit 1
fi

mkdir -p "$OUTPUT_DIR"
echo "Found ${#videos[@]} video(s) in $INPUT_DIR/"
echo ""

for video in "${videos[@]}"; do
  basename="${video##*/}"
  name="${basename%.*}"
  convert_one "$video" "${OUTPUT_DIR}/${name}.gif"
done

echo ""
echo "Done! All GIFs saved to $OUTPUT_DIR/"
echo ""
echo "Tips:"
echo "  - For smaller files: reduce fps (e.g., bash $0 '' output/ 640 8)"
echo "  - For GitHub README: keep under 10MB"
echo "  - For higher quality: increase width (e.g., bash $0 '' output/ 1024 15)"
