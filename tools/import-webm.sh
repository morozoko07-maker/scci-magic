#!/usr/bin/env bash
# Import Type Garden WebM exports into static/media with canonical names.
#
#   tools/import-webm.sh [download-dir]
#
# Files are expected to be named garden-<clip>-<motion>*.webm (clip: events|clubs).
# The palette is detected from the top-left pixel, so the browser download
# suffixes "(1)", "(2)" do not matter.
set -uo pipefail

SRC="${1:-$HOME/Downloads}"
OUT="$(cd "$(dirname "$0")/.." && pwd)/static/media"
mkdir -p "$OUT"

declare -A BG=(
  ["rose"]="0,0,0"
  ["paper"]="242,239,227"
  ["tomato"]="254,21,0"
  ["butter"]="255,234,168"
  ["blush"]="249,212,216"
)

for f in "$SRC"/garden-*.webm; do
  [ -e "$f" ] || continue
  base=$(basename "$f")
  clip=$(echo "$base" | sed -n 's/^garden-\(events\|clubs\)-.*/\1/p')
  [ -n "$clip" ] || continue
  motion=$(echo "$base" | sed -n 's/^garden-[a-z]*-\([a-z]*\).*/\1/p')
  case "$motion" in breathe|grow|wither|typed|wind|reach|scatter|visit) ;; *) motion="breathe" ;; esac

  rgb=$(ffmpeg -v error -i "$f" -frames:v 1 -vf "crop=8:8:0:0,scale=1:1" -f rawvideo -pix_fmt rgb24 - 2>/dev/null | od -An -tu1 | tr -s ' \n' ' ' | sed 's/^ *//;s/ *$//' | tr ' ' ',')
  palette=""
  for name in "${!BG[@]}"; do
    [ "$rgb" = "${BG[$name]}" ] && palette="$name"
  done
  if [ -z "$palette" ]; then
    # nearest known background
    best=999999; palette="rose"
    IFS=',' read -r r g b <<< "$rgb"
    for name in "${!BG[@]}"; do
      IFS=',' read -r R G B <<< "${BG[$name]}"
      d=$(( (r-R)*(r-R) + (g-G)*(g-G) + (b-B)*(b-B) ))
      if [ "$d" -lt "$best" ]; then best=$d; palette="$name"; fi
    done
  fi

  dest="$OUT/hero-$clip-$motion-$palette.webm"
  if [ -e "$dest" ]; then
    echo "skip  $(basename "$dest")"
  else
    cp "$f" "$dest"
    echo "import $(basename "$dest")  ($rgb)"
  fi
done
