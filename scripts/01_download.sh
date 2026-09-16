#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p data/malecns data/hyperliquid
PYTHON="${PYTHON:-python3}"
if command -v conda >/dev/null 2>&1 && conda env list | grep -qE '^flyhl\s'; then
  eval "$(conda shell.bash hook)"
  conda activate flyhl
  PYTHON=python
fi
echo "==> MaleCNS v1.0 (annotations always; weights if --full-connectome)"
"$PYTHON" -m src.flyhl.download_connectome "$@"
echo "==> Hyperliquid public BTC candles, funding, recent trades"
"$PYTHON" -m src.flyhl.download_hyperliquid "$@"
echo "Done. See data/"
