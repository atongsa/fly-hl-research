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

# 1. data (~15 MB default; add --full-connectome for the 1.1 GB weight table)
bash scripts/01_download.sh

# 2. env + train
bash scripts/02_setup_and_train.sh

# 3. paper trade (no key)
bash scripts/03_trade.sh

# 4. local preview of the Pages site
bash scripts/04_pages.sh
```

Then enable **Settings → Pages → Deploy from a branch → `/docs`**.

## Live trading (optional, dangerous)

Copy `.env.example` to `.env` and fill:

- `HL_AGENT_KEY` — Hyperliquid **agent / API wallet** private key (cannot withdraw if you created it as an agent)
- `HL_ACCOUNT_ADDRESS` — your master account `0x…`

Default mode is `paper`. Live mainnet also needs:

```bash
export MODE=live
export CONFIRM_LIVE=I_UNDERSTAND_THE_RISK
export HL_NETWORK=mainnet
bash scripts/03_trade.sh
```

Caps default to **2x leverage** and **$50 notional**. Raise them only if you accept liquidation risk. Never commit `.env`.

## What “vision loop” means here

MaleCNS vision cells (photoreceptors R1–R8, lamina L1–L5, T4/T5 motion, LC looming, giant fiber `DNp01`) are used as a **frozen encoder motif**.

- Candles are drawn as a small RGB image (the fly “sees” the chart).
- Funding and recent tape are extra channels.
- A tiny trained head maps encoder activity → `{flat, short}`.
- Full 166k-cell simulation is **not** run (that needs many GB RAM). The default path uses annotations + a documented motif. Pass `--full-connectome` to also store the official 1.1 GB weight file for later subgraph extraction.

## Data sources

| Source | License | URL |
|---|---|---|
| MaleCNS v1.0 flat connectome | CC BY 4.0 | https://male-cns.janelia.org/download/ |
| Hyperliquid public info API | exchange ToS | https://api.hyperliquid.xyz/info |

Cite Berg et al., *Cell* 2026 (MaleCNS) if you publish results.

## Layout

```
scripts/01_download.sh          # part 1
scripts/02_setup_and_train.sh   # part 2
scripts/03_trade.sh             # part 3
scripts/04_pages.sh             # part 4 helper
src/flyhl/                      # python
docs/                           # GitHub Pages
```
