#!/usr/bin/env bash
# Convert a .webm to .mp4 (H.264/AAC), forcing even dimensions so x264 can open.
#
# x264 in yuv420p stores chroma at half resolution per axis, so odd width or
# height is unrepresentable and the encoder refuses to initialize. VLC reports
# this as the misleading "VLC could not open the h264 video encoder."
# GNOME screencasts hit this constantly (e.g. 756x769).
#
# Usage: convert.sh <input.webm> [output.mp4]

set -euo pipefail

INPUT="${1:-}"
if [[ -z "$INPUT" ]]; then
  echo "usage: convert.sh <input.webm> [output.mp4]" >&2
  exit 2
fi
if [[ ! -f "$INPUT" ]]; then
  echo "error: no such file: $INPUT" >&2
  exit 1
fi

OUTPUT="${2:-${INPUT%.*}.mp4}"

if [[ -e "$OUTPUT" ]]; then
  echo "error: output already exists, refusing to overwrite: $OUTPUT" >&2
  echo "       pass an explicit output path to convert anyway." >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# Preferred path: ffmpeg. Rounds odd dimensions down in-filter, no probing.
# ---------------------------------------------------------------------------
if command -v ffmpeg >/dev/null 2>&1; then
  echo "==> encoding with ffmpeg"
  ffmpeg -nostdin -hide_banner -loglevel warning -stats \
    -i "$INPUT" \
    -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" \
    -c:v libx264 -preset medium -crf 23 -pix_fmt yuv420p \
    -c:a aac -b:a 128k \
    -movflags +faststart \
    "$OUTPUT"

# ---------------------------------------------------------------------------
# Fallback: VLC. Needs explicit even width/height, so probe the source first.
# ---------------------------------------------------------------------------
elif command -v vlc >/dev/null 2>&1; then
  echo "==> ffmpeg not found, falling back to VLC"

  # VLC logs the visible size as: "... vsz 756x769, 4cc I420 ..."
  DIMS="$(vlc -I dummy -vv --no-audio --stop-time=1 "$INPUT" vlc://quit 2>&1 \
          | grep -o 'vsz [0-9]\+x[0-9]\+' | head -1 | cut -d' ' -f2 || true)"

  if [[ -z "$DIMS" ]]; then
    echo "error: could not determine video dimensions from VLC output." >&2
    echo "       install ffmpeg for a more reliable conversion:" >&2
    echo "         sudo apt install ffmpeg" >&2
    exit 1
  fi

  W="${DIMS%x*}"
  H="${DIMS#*x}"
  EVEN_W=$(( W / 2 * 2 ))
  EVEN_H=$(( H / 2 * 2 ))

  if [[ "$W" != "$EVEN_W" || "$H" != "$EVEN_H" ]]; then
    echo "    source is ${W}x${H} (odd) -> encoding at ${EVEN_W}x${EVEN_H}"
  else
    echo "    source is ${W}x${H}"
  fi

  vlc -I dummy "$INPUT" \
    --sout "#transcode{vcodec=h264,vb=2000,width=${EVEN_W},height=${EVEN_H},acodec=mp4a,ab=128,channels=2}:std{access=file,mux=mp4,dst=${OUTPUT}}" \
    vlc://quit 2>&1 | grep -Ei 'x264 encoder error|cannot open' >&2 || true

else
  echo "error: neither ffmpeg nor vlc found." >&2
  echo "       sudo apt install ffmpeg" >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# Verify we produced something real, not a zero-byte stub from a failed encode.
# ---------------------------------------------------------------------------
if [[ ! -s "$OUTPUT" ]]; then
  echo "error: conversion failed, output is empty: $OUTPUT" >&2
  rm -f "$OUTPUT"
  exit 1
fi

SIZE="$(du -h "$OUTPUT" | cut -f1)"
echo "==> wrote $OUTPUT ($SIZE)"
