"""Download public Hyperliquid BTC perp candles, funding, and recent trades."""

from __future__ import annotations

import argparse
import json
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "hyperliquid"
INFO = "https://api.hyperliquid.xyz/info"


def post(body: dict):
    req = urllib.request.Request(
        INFO,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "fly-hl-research/0.1"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def candles(coin: str, interval: str, start_ms: int, end_ms: int) -> list:
    step = 10 * 24 * 3600 * 1000 if interval.endswith("m") else 60 * 24 * 3600 * 1000
    out: list = []
    t = start_ms
    while t < end_ms:
        chunk_end = min(end_ms, t + step)
        data = post({"type": "candleSnapshot", "req": {"coin": coin, "interval": interval, "startTime": t, "endTime": chunk_end}})
        if isinstance(data, list):
            out.extend(data)
        time.sleep(0.15)
        t = chunk_end
    seen = {}
    for row in out:
        seen[row.get("t")] = row
    return [seen[k] for k in sorted(seen)]


def funding(coin: str, start_ms: int, end_ms: int) -> list:
    step = 30 * 24 * 3600 * 1000
    out: list = []
    t = start_ms
    while t < end_ms:
        chunk_end = min(end_ms, t + step)
        data = post({"type": "fundingHistory", "coin": coin, "startTime": t, "endTime": chunk_end})
        if isinstance(data, list):
            out.extend(data)
        time.sleep(0.15)
        t = chunk_end
    return out


def recent_trades(coin: str) -> list:
    try:
        data = post({"type": "recentTrades", "coin": coin})
        return data if isinstance(data, list) else []
    except Exception as exc:
        print("recentTrades unavailable:", exc)
        return []


def contexts(coin: str) -> dict:
    data = post({"type": "metaAndAssetCtxs"})
    meta, ctxs = data[0], data[1]
    universe = meta.get("universe", [])
    for i, u in enumerate(universe):
        if u.get("name") == coin:
            return {"meta": u, "ctx": ctxs[i]}
    return {"meta": None, "ctx": None}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--coin", default="BTC")
    p.add_argument("--days", type=int, default=180)
    args, _ = p.parse_known_args(argv)
    OUT.mkdir(parents=True, exist_ok=True)
    end = int(time.time() * 1000)
    start = end - args.days * 24 * 3600 * 1000
    coin = args.coin
    print(f"HL {coin} last {args.days}d")
    c15 = candles(coin, "15m", start, end)
    (OUT / f"{coin.lower()}_candles_15m.json").write_text(json.dumps(c15))
    print(f"  15m candles {len(c15)}")
    c1h = candles(coin, "1h", start, end)
    (OUT / f"{coin.lower()}_candles_1h.json").write_text(json.dumps(c1h))
    print(f"  1h candles {len(c1h)}")
    fund = funding(coin, start, end)
    (OUT / f"{coin.lower()}_funding.json").write_text(json.dumps(fund))
    print(f"  funding rows {len(fund)}")
    trades = recent_trades(coin)
    (OUT / f"{coin.lower()}_recent_trades.json").write_text(json.dumps(trades))
    print(f"  recent trades {len(trades)}")
    ctx = contexts(coin)
    (OUT / f"{coin.lower()}_context.json").write_text(json.dumps(ctx, indent=2))
    proxy = []
    for row in c15:
        o, c = float(row["o"]), float(row["c"])
        ret = (c - o) / o if o else 0.0
        proxy.append({"t": row["t"], "ret": ret, "short_win": ret < 0, "range": (float(row["h"]) - float(row["l"])) / o if o else 0})
    (OUT / f"{coin.lower()}_short_proxy.json").write_text(json.dumps(proxy))
    print("  wrote short-win proxy from down-candles (not official short-fill labels)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
