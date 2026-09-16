#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

wipe_live_secrets() {
  # Always runs on exit (success, error, Ctrl-C).
  if [[ "${MODE:-paper}" != "live" ]]; then
    return 0
  fi
  if [[ "${KEEP_ENV:-}" == "1" ]]; then
    echo "KEEP_ENV=1 set; leaving .env in place"
    return 0
  fi
  if [[ -f "$ROOT/.env" ]]; then
    if command -v shred >/dev/null 2>&1; then
      shred -u "$ROOT/.env" || rm -f "$ROOT/.env"
    else
      : > "$ROOT/.env"
      rm -f "$ROOT/.env"
    fi
    echo "Deleted .env. Copy .env.example to .env and refill before the next live run."
  fi
  unset HL_AGENT_KEY CONFIRM_LIVE
}

trap wipe_live_secrets EXIT INT TERM

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
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
