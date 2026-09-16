#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/docs"
echo "GitHub Pages source folder is docs/"
echo "Enable: repo Settings → Pages → Deploy from branch → /docs"
echo "Local preview: http://127.0.0.1:8765/"
python3 -m http.server 8765
