---
name: webm-to-mp4
description: Convert a .webm video to .mp4 (H.264/AAC), automatically handling the odd-dimension failure that makes VLC report "could not open the h264 video encoder". Use whenever the user wants to convert a webm to mp4, fix a screencast recording, or hits an h264 encoder error while transcoding.
---

## Purpose

Convert `.webm` video to `.mp4` reliably, without hitting the odd-dimension trap.

## The problem this solves

H.264 in `yuv420p` stores chroma planes at half resolution on each axis, so a
video with an **odd width or height cannot be encoded**. x264 refuses to
initialize and VLC surfaces this as a misleading generic error:

```
VLC could not open the h264 video encoder.
```

The real error, only visible with `-vv`, is:

```
x264 encoder error: height not divisible by 2 (756x769)
```

GNOME's screencast recorder triggers this routinely — it captures the window at
whatever odd pixel size it happened to be. The fix is to round the dimensions
down to the nearest even number.

**Do not** tell the user their VLC is missing the x264 encoder without checking.
On Ubuntu the plugin is normally present and linked; the file is usually at fault.

## How to run it

Take the path to the `.webm` from the user and run:

```bash
~/.claude/skills/webm-to-mp4/scripts/convert.sh "<input.webm>" [output.mp4]
```

- Output defaults to the input path with `.mp4` extension, alongside the source.
- The script **refuses to overwrite** an existing output file. If the user wants
  to replace one, pass an explicit output path or remove the old file first —
  confirm with them before deleting anything.
- Quote the path. These files very often contain spaces
  (`Screencast From 2026-07-18 12-26-42.webm`).

The script prefers `ffmpeg` and falls back to `vlc` automatically. It rounds odd
dimensions down and reports when it does so.

## Reporting back

Tell the user:

1. The output path and file size.
2. **If the source had odd dimensions**, say so explicitly and note that a row or
   column of pixels was dropped (e.g. `756x769 -> 756x768`). It is imperceptible
   for a screencast, but it is not a pixel-exact conversion and they should know.

If the conversion fails, run the underlying command again with verbose logging
(`ffmpeg` without `-loglevel warning`, or `vlc -vv`) and read the actual encoder
error rather than guessing.

## Notes

- `ffmpeg` gives better quality per byte and is the preferred path. If it is
  missing, it is reasonable to suggest `sudo apt install ffmpeg` — but never run
  a system install without the user agreeing to it.
- Encoding is CPU-bound and can take a while on long recordings. Do not assume a
  slow run has hung.
