"""Paper loop by default. Live Hyperliquid orders only with explicit env flags."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import torch

from .download_hyperliquid import candles, contexts, post
from .vision_loop import VisionLoopNet, candle_image, extra_vec

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "docs" / "live-state.json"
RUNLOG = ROOT / "runs" / "trades.jsonl"


def load_env():
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def write_state(payload):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    RUNLOG.parent.mkdir(parents=True, exist_ok=True)
    payload["updated"] = datetime.now(timezone.utc).isoformat()
    STATE.write_text(json.dumps(payload, indent=2))
    with RUNLOG.open("a") as f:
        f.write(json.dumps(payload) + "\n")


def latest_window(coin, n=32):
    end = int(time.time() * 1000)
    start = end - (n + 5) * 15 * 60 * 1000
    rows = candles(coin, "15m", start, end)[-n:]
    funding = 0.0
    try:
        hist = post({"type": "fundingHistory", "coin": coin, "startTime": end - 4 * 3600 * 1000})
        if hist:
            funding = float(hist[-1]["fundingRate"])
    except Exception:
        pass
    return rows, funding


def infer(model, window, funding):
    img = torch.tensor(candle_image(window)[None, ...])
    ex = torch.tensor(extra_vec(window, funding)[None, ...])
    with torch.no_grad():
        prob = torch.softmax(model(img, ex)[0], dim=0)
    action = "short" if int(prob.argmax()) == 1 and float(prob[1]) > 0.55 else "flat"
    return {
        "action": action,
        "p_flat": float(prob[0]),
        "p_short": float(prob[1]),
        "last_close": float(window[-1]["c"]) if window else None,
        "funding": funding,
    }


def paper_step(decision, paper):
    px = decision["last_close"] or 0.0
    if px and paper.get("size_btc", 0) <= 0.000001:
        paper["size_btc"] = float(os.environ.get("MAX_NOTIONAL_USD", "50")) / px
    pos = paper.get("position", 0.0)
    if decision["action"] == "short" and pos >= 0:
        paper["position"] = -paper["size_btc"]
        paper["entry"] = px
        paper["events"] = paper.get("events", 0) + 1
        paper["last_event"] = f"paper short {paper['size_btc']} @ {px}"
    elif decision["action"] == "flat" and pos < 0:
        pnl = (paper["entry"] - px) * abs(pos)
        paper["equity"] = paper.get("equity", 1000.0) + pnl
        paper["position"] = 0.0
        paper["entry"] = None
        paper["events"] = paper.get("events", 0) + 1
        paper["last_event"] = f"paper cover @ {px} pnl={pnl:.2f}"
    else:
        paper["last_event"] = "hold"
    paper["upnl"] = (paper["entry"] - px) * abs(paper["position"]) if paper.get("position", 0) < 0 and paper.get("entry") else 0.0
    return paper


def live_step(decision, coin):
    from eth_account import Account
    from hyperliquid.exchange import Exchange
    from hyperliquid.info import Info
    from hyperliquid.utils import constants

    key = os.environ.get("HL_AGENT_KEY", "")
    acct = os.environ.get("HL_ACCOUNT_ADDRESS", "")
    if not key or not acct:
        raise SystemExit("HL_AGENT_KEY and HL_ACCOUNT_ADDRESS required for live")
    network = os.environ.get("HL_NETWORK", "testnet")
    base = constants.MAINNET_API_URL if network == "mainnet" else constants.TESTNET_API_URL
    wallet = Account.from_key(key)
    info = Info(base, skip_ws=True)
    exchange = Exchange(wallet, base, account_address=acct)
    mid = float(decision["last_close"])
    sz = round(float(os.environ.get("MAX_NOTIONAL_USD", "50")) / mid, 5)
    slip = float(os.environ.get("SLIPPAGE", "0.01"))
    btc_pos = 0.0
    for p in info.user_state(acct).get("assetPositions", []):
        pos = p.get("position", {})
        if pos.get("coin") == coin:
            btc_pos = float(pos.get("szi", 0))
    result = {"live": True, "network": network, "btc_pos": btc_pos, "wanted": decision["action"]}
    if decision["action"] == "short" and btc_pos >= 0:
        result["order"] = exchange.market_open(coin, False, sz, None, slip)
        result["event"] = f"live short {sz}"
    elif decision["action"] == "flat" and btc_pos < 0:
        result["order"] = exchange.market_close(coin)
        result["event"] = "live cover"
    else:
        result["event"] = "live hold"
    return result


def main() -> int:
    load_env()
    mode = os.environ.get("MODE", "paper").lower()
    coin = os.environ.get("COIN", "BTC")
    poll = int(os.environ.get("POLL_SECONDS", "30"))
    max_steps = int(os.environ.get("PAPER_STEPS") or os.environ.get("MAX_STEPS") or "0")
    model = VisionLoopNet()
    ckpt = ROOT / "models" / "vision_loop.pt"
    if ckpt.exists():
        blob = torch.load(ckpt, map_location="cpu", weights_only=False)
        model.load_state_dict(blob["state_dict"])
        print("loaded", ckpt, "acc", blob.get("acc"))
    else:
        print("WARNING: no checkpoint, untrained weights")
    model.eval()
    paper = {"equity": 1000.0, "position": 0.0, "size_btc": 0.0, "events": 0}
    print(f"loop mode={mode} coin={coin} poll={poll}s paper_steps={max_steps or 'inf'}  Ctrl-C to stop")
    step = 0
    while True:
        try:
            window, funding = latest_window(coin)
            decision = infer(model, window, funding)
            ctx = {}
            try:
                ctx = contexts(coin)
            except Exception:
                pass
            payload = {
                "mode": mode,
                "coin": coin,
                "decision": decision,
                "mark": (ctx.get("ctx") or {}).get("markPx"),
                "funding": funding,
                "step": step + 1,
            }
            if mode == "live":
                if os.environ.get("CONFIRM_LIVE") != "I_UNDERSTAND_THE_RISK":
                    raise SystemExit("set CONFIRM_LIVE=I_UNDERSTAND_THE_RISK")
                payload["execution"] = live_step(decision, coin)
            else:
                paper = paper_step(decision, paper)
                payload["paper"] = {
                    "equity": paper["equity"],
                    "position": paper["position"],
                    "upnl": paper.get("upnl", 0),
                    "events": paper["events"],
                    "last_event": paper.get("last_event"),
                }
            print(payload.get("execution") or payload.get("paper"), decision)
            write_state(payload)
            step += 1
            if mode != "live" and max_steps and step >= max_steps:
                print(f"paper run complete ({step} steps)")
                return 0
        except KeyboardInterrupt:
            print("stop")
            return 0
        except Exception as exc:
            print("step error:", exc)
            write_state({"mode": mode, "error": str(exc)})
        time.sleep(poll)


if __name__ == "__main__":
    raise SystemExit(main())
