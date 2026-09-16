#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if command -v mamba >/dev/null 2>&1; then
  EXE=mamba
elif command -v conda >/dev/null 2>&1; then
  EXE=conda
else
  echo "Install Miniforge/Mambaforge first: https://github.com/conda-forge/miniforge"
  exit 1
fi

echo "==> Creating/updating mamba env 'flyhl'"
"$EXE" env update -f environment.yml --prune
eval "$(conda shell.bash hook)"
conda activate flyhl

if [[ ! -f data/hyperliquid/btc_candles_15m.json ]]; then
  echo "No market data yet — running download"
  python -m src.flyhl.download_connectome
  python -m src.flyhl.download_hyperliquid
fi

mkdir -p models runs
echo "==> Training vision-loop readout"
python -m src.flyhl.train "$@"
echo "Checkpoint: models/vision_loop.pt"
