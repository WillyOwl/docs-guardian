#!/usr/bin/env bash
# Render each raw log <dir>/*.txt to <name>.html and screenshot it to <name>.png
# with headless Chrome. Usage: render.sh <dir>
set -euo pipefail
dir=$1
for log in "$dir"/*.txt; do
  name=${log%.txt}
  lines=$(wc -l < "$log")
  height=$(( lines * 17 + 60 ))
  {
    printf '<!doctype html><meta charset="utf-8"><style>'
    printf 'body{margin:0;background:#1e1e1e;color:#e6e6e6}'
    printf 'pre{font:13px/17px "DejaVu Sans Mono",monospace;margin:20px;white-space:pre-wrap;word-break:break-all}'
    printf '</style><pre>'
    sed -e 's/\x1b\[[0-9;]*m//g' -e 's/&/\&amp;/g' -e 's/</\&lt;/g' -e 's/>/\&gt;/g' "$log"
    printf '</pre>'
  } > "$name.html"
  google-chrome --headless=new --no-sandbox --disable-gpu --hide-scrollbars \
    --window-size=1400,"$height" --screenshot="$name.png" "file://$name.html" 2> /dev/null
  echo "$name.png"
done
