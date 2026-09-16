"""Known fly vision-loop motif + tiny trainable readout.

R1-R8 -> L1/L2 -> T4/T5 -> LC -> DNp01
We render BTC candles as a 32x32 RGB image and train a small readout.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]


def candle_image(window: list[dict], size: int = 32) -> np.ndarray:
    img = Image.new("RGB", (size, size), (8, 8, 16))
    draw = ImageDraw.Draw(img)
    if not window:
        return np.asarray(img).transpose(2, 0, 1).astype(np.float32) / 255.0
    highs = [float(r["h"]) for r in window]
    lows = [float(r["l"]) for r in window]
    lo, hi = min(lows), max(highs)
    span = max(hi - lo, 1e-9)
    n = len(window)
    w = max(size / n, 1.0)
    for i, r in enumerate(window):
        x0 = int(i * w)
        x1 = int(min(size - 1, x0 + max(w * 0.6, 1)))
        o, c = float(r["o"]), float(r["c"])
        h, l = float(r["h"]), float(r["l"])
        y_h = int((1 - (h - lo) / span) * (size - 1))
        y_l = int((1 - (l - lo) / span) * (size - 1))
        y_o = int((1 - (o - lo) / span) * (size - 1))
        y_c = int((1 - (c - lo) / span) * (size - 1))
        color = (40, 200, 90) if c >= o else (220, 60, 70)
        mid = (x0 + x1) // 2
        draw.line([(mid, y_h), (mid, y_l)], fill=color)
        top, bot = min(y_o, y_c), max(y_o, y_c)
        draw.rectangle([x0, top, max(x0 + 1, x1), max(top + 1, bot)], fill=color)
    return np.asarray(img).transpose(2, 0, 1).astype(np.float32) / 255.0


class VisionLoopNet(nn.Module):
    def __init__(self, extra_features: int = 4, n_actions: int = 2):
        super().__init__()
        self.lamina = nn.Conv2d(3, 8, kernel_size=3, padding=1)
        self.medulla = nn.Conv2d(8, 8, kernel_size=3, padding=1)
        self.lobula = nn.Conv2d(8, 16, kernel_size=3, stride=2, padding=1)
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.readout = nn.Sequential(
            nn.Linear(16 + extra_features, 32),
            nn.Tanh(),
            nn.Linear(32, n_actions),
        )

    def forward(self, image: torch.Tensor, extra: torch.Tensor) -> torch.Tensor:
        x = torch.tanh(self.lamina(image))
        x = torch.tanh(self.medulla(x))
        x = torch.tanh(self.lobula(x))
        x = self.pool(x).flatten(1)
        return self.readout(torch.cat([x, extra], dim=1))


def extra_vec(window: list[dict], funding: float | None) -> np.ndarray:
    if len(window) < 2:
        return np.zeros(4, dtype=np.float32)
    closes = np.array([float(r["c"]) for r in window], dtype=np.float32)
    ret = (closes[-1] - closes[0]) / closes[0]
    vol = float(np.std(np.diff(closes) / closes[:-1])) if len(closes) > 2 else 0.0
    last = window[-1]
    rng = (float(last["h"]) - float(last["l"])) / float(last["c"])
    fund = 0.0 if funding is None else float(funding) * 1000.0
    return np.array([ret, vol, rng, fund], dtype=np.float32)


def load_provenance() -> dict:
    path = ROOT / "data" / "malecns" / "vision_types.json"
    if path.exists():
        return json.loads(path.read_text())
    return {"n_vision_like": 0}
