#!/usr/bin/env bash
# Download + train + a few fake trades, then stop. Never places a real order.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export MODE=paper
unset HL_AGENT_KEY CONFIRM_LIVE || true
export PAPER_STEPS="${PAPER_STEPS:-8}"
export POLL_SECONDS="${POLL_SECONDS:-5}"

echo "==> paper-all  fake trades=${PAPER_STEPS}  wait=${POLL_SECONDS}s between them"
echo "    no real order; any live key is ignored"

bash "$ROOT/scripts/01_download.sh" "$@"
bash "$ROOT/scripts/02_setup_and_train.sh"
bash "$ROOT/scripts/03_trade.sh"

cat <<EOF

Fake-trade run finished (${PAPER_STEPS} decisions).
State file: docs/live-state.json
Model:      models/vision_loop.pt

See the dashboard:
  bash scripts/04_pages.sh

Place real orders later (optional):
  cp .env.example .env
  # fill HL_AGENT_KEY, HL_ACCOUNT_ADDRESS
  # set MODE=live and CONFIRM_LIVE=I_UNDERSTAND_THE_RISK
  bash scripts/03_trade.sh
EOF
