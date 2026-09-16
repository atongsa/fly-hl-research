# fly-hl-research

Four-part research stack on [atongsa/fly-hl-research](https://github.com/atongsa/fly-hl-research):

1. Download MaleCNS v1.0 (Google Research / HHMI Janelia) and public Hyperliquid BTC data
2. Mamba/conda env + train a **vision-loop** model on that data
3. Run the model (paper by default; live Hyperliquid only if you opt in)
4. GitHub Pages dashboard for the live/paper process

This is an experiment. It is **not** a profitable strategy and **not** financial advice. Stonkfly-style connectome trading has not shown a durable edge.

## Quick start

```bash
git clone https://github.com/atongsa/fly-hl-research.git
cd fly-hl-research

# paper only: download + train + 8 paper steps, then exits
bash scripts/00_paper_all.sh

# dashboard
bash scripts/04_pages.sh
```

Then, if you still want live:

```bash
cp .env.example .env   # fill keys; MODE=live; CONFIRM_LIVE=I_UNDERSTAND_THE_RISK
bash scripts/03_trade.sh
```

Pieces if you prefer to run them apart:

```bash
bash scripts/01_download.sh
bash scripts/02_setup_and_train.sh
bash scripts/03_trade.sh          # paper unless MODE=live
bash scripts/04_pages.sh
```

Enable **Settings → Pages → Deploy from a branch → `/docs`** for the hosted dashboard.

`00_paper_all.sh` forces `MODE=paper`, ignores any agent key, and stops after `PAPER_STEPS` (default 8). More paper ticks:

```bash
PAPER_STEPS=20 POLL_SECONDS=5 bash scripts/00_paper_all.sh
```

## Live trading (optional, dangerous)

Copy `.env.example` to `.env` and fill:

- `HL_AGENT_KEY` — Hyperliquid **agent / API wallet** private key (cannot withdraw if you created it as an agent)
- `HL_ACCOUNT_ADDRESS` — your master account `0x…`

When `MODE=live`, the script **deletes `.env` on exit** (normal stop, error, or Ctrl-C) and unsets `HL_AGENT_KEY`. Next live run you must copy `.env.example` and fill again. To skip the wipe once: `KEEP_ENV=1`.

You can also export the key in the shell and never write `.env`. Caps default to **2x leverage** and **$50 notional**. Never commit `.env`.

## What “vision loop” means here

MaleCNS vision cells (photoreceptors R1–R8, lamina L1–L5, T4/T5 motion, LC looming, giant fiber `DNp01`) are used as a **frozen encoder motif**.

- Candles are drawn as a small RGB image (the fly “sees” the chart).
- Funding and recent tape are extra channels.
- A tiny trained head maps encoder activity → `{flat, short}`.
- Full 166k-cell simulation is **not** run (that needs many GB RAM).

## Data sources

| Source | License | URL |
|---|---|---|
| MaleCNS v1.0 flat connectome | CC BY 4.0 | https://male-cns.janelia.org/download/ |
| Hyperliquid public info API | exchange ToS | https://api.hyperliquid.xyz/info |

Cite Berg et al., *Cell* 2026 (MaleCNS) if you publish results.

## Layout

```
scripts/00_paper_all.sh         # paper: 1+2+bounded 3
scripts/01_download.sh
scripts/02_setup_and_train.sh
scripts/03_trade.sh             # paper or live
scripts/04_pages.sh             # dashboard
src/flyhl/
docs/
```
