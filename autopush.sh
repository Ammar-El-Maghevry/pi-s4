#!/bin/bash
cd "$(dirname "$0")"

echo "Watching $(pwd) for changes... Ctrl+C to stop"

while inotifywait -r -e modify,create,delete,move --exclude '\.git' . ; do
  git add -A
  if ! git diff --cached --quiet; then
    git commit -m "auto: update $(date '+%Y-%m-%d %H:%M:%S')"
    git push origin main
  fi
done
