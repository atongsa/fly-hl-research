#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi
if command -v conda >/dev/null 2>&1 && conda env list | grep -qE '^flyhl\s'; then
  eval "$(conda shell.bash hook)"
  conda activate flyhl
fi
MODE="${MODE:-paper}"
echo "==> trade mode=${MODE} network=${HL_NETWORK:-testnet}"
if [[ "$MODE" == "live" && "${CONFIRM_LIVE:-}" != "I_UNDERSTAND_THE_RISK" ]]; then
  echo "Refusing live mode. Set CONFIRM_LIVE=I_UNDERSTAND_THE_RISK in .env"
  exit 2
fi
python -m src.flyhl.trade "$@"
