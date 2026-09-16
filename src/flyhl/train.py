"""Walk-forward train the vision-loop readout on public BTC 15m candles."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from .vision_loop import VisionLoopNet, candle_image, extra_vec, load_provenance

ROOT = Path(__file__).resolve().parents[2]
WIN = 32
FEE = 0.0006


def load_series():
    candles = json.loads((ROOT / "data" / "hyperliquid" / "btc_candles_15m.json").read_text())
    funding_rows = json.loads((ROOT / "data" / "hyperliquid" / "btc_funding.json").read_text())
    fund_map = {int(row["time"]): float(row["fundingRate"]) for row in funding_rows}
    return candles, fund_map


def nearest_funding(ts, fund_map):
    if not fund_map:
        return 0.0
    keys = list(fund_map)
    lo, hi, best = 0, len(keys) - 1, keys[0]
    while lo <= hi:
        mid = (lo + hi) // 2
        if keys[mid] <= ts:
            best = keys[mid]
            lo = mid + 1
        else:
            hi = mid - 1
    return fund_map[best]


def build_tensors(candles, fund_map):
    images, extras, labels = [], [], []
    for i in range(WIN, len(candles) - 1):
        window = candles[i - WIN : i]
        nxt = candles[i]
        o, c = float(nxt["o"]), float(nxt["c"])
        ret = (c - o) / o
        y = 1 if (-ret - FEE) > 0 else 0
        images.append(candle_image(window))
        extras.append(extra_vec(window, nearest_funding(int(window[-1]["t"]), fund_map)))
        labels.append(y)
    return (
        torch.tensor(np.stack(images), dtype=torch.float32),
        torch.tensor(np.stack(extras), dtype=torch.float32),
        torch.tensor(labels, dtype=torch.long),
    )


def main() -> int:
    candles, fund_map = load_series()
    print(f"candles={len(candles)} funding={len(fund_map)}")
    x_img, x_ex, y = build_tensors(candles, fund_map)
    n = len(y)
    split = int(n * 0.8)
    print(f"samples={n} short-label-rate={float(y.float().mean()):.3f} train={split}")
    model = VisionLoopNet()
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.CrossEntropyLoss()
    loader = DataLoader(TensorDataset(x_img[:split], x_ex[:split], y[:split]), batch_size=64, shuffle=True)
    model.train()
    for epoch in range(8):
        total = 0.0
        for img, ex, lab in loader:
            opt.zero_grad()
            loss = loss_fn(model(img, ex), lab)
            loss.backward()
            opt.step()
            total += float(loss) * len(lab)
        print(f"epoch {epoch+1} loss={total / split:.4f}")
    model.eval()
    with torch.no_grad():
        pred = model(x_img[split:], x_ex[split:]).argmax(-1)
        acc = float((pred == y[split:]).float().mean())
        flat_acc = float((y[split:] == 0).float().mean())
    print(f"walk-forward acc={acc:.3f} always-flat={flat_acc:.3f}")
    out = ROOT / "models"
    out.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": model.state_dict(), "acc": acc, "flat_acc": flat_acc, "provenance": load_provenance()}, out / "vision_loop.pt")
    (out / "metrics.json").write_text(json.dumps({"walk_forward_acc": acc, "always_flat_acc": flat_acc, "n_train": split, "n_test": n - split}, indent=2))
    print("wrote models/vision_loop.pt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
