#!/usr/bin/env bash
# One command: download + train + bounded paper trade. Never live.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export MODE=paper
unset HL_AGENT_KEY CONFIRM_LIVE || true
export PAPER_STEPS="${PAPER_STEPS:-8}"
export POLL_SECONDS="${POLL_SECONDS:-5}"

echo "==> paper-all  steps=${PAPER_STEPS} poll=${POLL_SECONDS}s"
echo "    live keys are ignored on this path"

bash "$ROOT/scripts/01_download.sh" "$@"
bash "$ROOT/scripts/02_setup_and_train.sh"
bash "$ROOT/scripts/03_trade.sh"

cat <<EOF

Paper pipeline finished.
Dashboard state: docs/live-state.json
Checkpoint:      models/vision_loop.pt

Next, live (optional):
  cp .env.example .env
  # fill HL_AGENT_KEY, HL_ACCOUNT_ADDRESS, MODE=live, CONFIRM_LIVE=I_UNDERSTAND_THE_RISK
  bash scripts/03_trade.sh

Dashboard:
  bash scripts/04_pages.sh
  # or Settings → Pages → /docs
EOF
