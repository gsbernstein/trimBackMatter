#!/bin/bash
mkdir -p trimmed
for f in episodes/*.mp3; do
  duration=$(ffmpeg -i "$f" 2>&1 | grep "Duration" | awk '{print $2}' | tr -d ,)
  seconds=$(echo "$duration" | awk -F: '{ printf "%.2f", ($1 * 3600) + ($2 * 60) + $3 - 71 }')
  out="trimmed/$(basename "$f")"
  ffmpeg -y -i "$f" -t "$seconds" "$out"
done