# fly-hl-research

Research stack: Google/Janelia MaleCNS fly vision loop + public Hyperliquid BTC data.

Not financial advice. Not a proven edge. Do not send this repo your seed phrase.

## Usage

### 1. Fake trades only (no key, no real order)

```bash
git clone https://github.com/atongsa/fly-hl-research.git
cd fly-hl-research
bash scripts/00_paper_all.sh
```

This one script:

1. Downloads the fly connectome annotations and public BTC data
2. Creates the `flyhl` conda/mamba env and trains the model
3. Makes **8 pretend decisions** (short or flat) against live public prices
4. Writes `docs/live-state.json` and **exits**

No Hyperliquid account is used. Any key in the environment is ignored.

Why it stops after 8: so the script can finish by itself. It is not stuck. To pretend longer:

```bash
PAPER_STEPS=20 bash scripts/00_paper_all.sh
```

To pretend until you press Ctrl-C:

```bash
bash scripts/03_trade.sh
```

### 2. Dashboard

After a paper or live run:

```bash
bash scripts/04_pages.sh
```

Open http://127.0.0.1:8765/

Or on GitHub: **Settings → Pages → Deploy from a branch → `/docs`**.

### 3. Real Hyperliquid orders (optional)

Only after paper looks sane.

```bash
cp .env.example .env
```

Edit `.env`:

```
MODE=live
CONFIRM_LIVE=I_UNDERSTAND_THE_RISK
HL_NETWORK=testnet
HL_ACCOUNT_ADDRESS=0xYourMaster
HL_AGENT_KEY=0xYourAgentKey
MAX_NOTIONAL_USD=50
```

Then:

```bash
bash scripts/03_trade.sh
```

Use an **agent wallet** key, not your seed. Default size cap is $50. Prefer `testnet` first.

When this live run ends (or you hit Ctrl-C), `.env` is **deleted**. Next time copy `.env.example` again and refill. To keep the file once: `KEEP_ENV=1`.

You can export the key in the shell instead of writing `.env`.

### Scripts

| Script | What it does |
|---|---|
| `scripts/00_paper_all.sh` | Download + train + 8 fake trades, then stop |
| `scripts/01_download.sh` | Data only |
| `scripts/02_setup_and_train.sh` | Env + train only |
| `scripts/03_trade.sh` | Fake trades, or real trades if `.env` says `MODE=live` |
| `scripts/04_pages.sh` | Local dashboard |

### Hardware

Laptop is enough: ~4 CPU cores, 8 GB RAM, 10 GB disk. No GPU required.

## What the model is

Candles are drawn as a small chart image. A tiny net shaped like the fly optic-lobe cascade (R1–R8 → L1/L2 → T4/T5 → LC → giant fiber) outputs `flat` or `short`.

It does **not** simulate all 166k MaleCNS neurons.

## Data

| Source | License |
|---|---|
| [MaleCNS v1.0](https://male-cns.janelia.org/download/) | CC BY 4.0 |
| [Hyperliquid public info API](https://api.hyperliquid.xyz/info) | Exchange ToS |

Cite Berg et al., *Cell* 2026 if you publish results.
