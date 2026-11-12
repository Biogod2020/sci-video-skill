#!/usr/bin/env bash
# Encode the rendered frames and put the sound under them. Run from the film folder after render.mjs frames.
#   mux.sh OUT_PREFIX VOICE.wav [FPS] [--rhythm]
# -> OUT_PREFIX_silent.mp4, OUT_PREFIX_voice_only.mp4 and, with --rhythm, OUT_PREFIX_voice_rhythm.mp4
# The voice is normalised to -17 LUFS. The rhythm bed (rhythm.py, next to this script) sits about 10 dB under it and is
# limited together with it, so the voice is never masked. Compare the two versions by ear before choosing.
set -euo pipefail
out="$1"; voice="$2"; fps="${3:-30}"; here="$(cd "$(dirname "$0")" && pwd)"
ffmpeg -y -loglevel error -framerate "$fps" -i frames/f%05d.jpg -c:v libx264 -crf 17 -preset slow -pix_fmt yuv420p -movflags +faststart "${out}_silent.mp4"
dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "${out}_silent.mp4")
ffmpeg -y -loglevel error -i "$voice" -af "loudnorm=I=-17:TP=-1.5:LRA=11,apad=whole_dur=$dur" -ar 48000 -ac 2 "${out}_voice_n.wav"
ffmpeg -y -loglevel error -i "${out}_silent.mp4" -i "${out}_voice_n.wav" -c:v copy -c:a aac -b:a 192k -shortest "${out}_voice_only.mp4"
if [ "${4:-}" = "--rhythm" ]; then
  "${PYTHON:-python3}" "$here/rhythm.py" "${out}_rhythm.wav" "$dur"
  ffmpeg -y -loglevel error -i "${out}_voice_n.wav" -i "${out}_rhythm.wav" -filter_complex "[1:a]volume=-9.8dB[r];[0:a][r]amix=inputs=2:normalize=0,alimiter=limit=0.89[a]" -map "[a]" -ar 48000 "${out}_mix.wav"
  ffmpeg -y -loglevel error -i "${out}_silent.mp4" -i "${out}_mix.wav" -c:v copy -c:a aac -b:a 192k -shortest "${out}_voice_rhythm.mp4"
fi
for f in "${out}"_*.mp4; do echo "$f $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f") s"; done
