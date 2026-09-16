"""Download MaleCNS v1.0 flat-connectome files from the public GCS bucket."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "malecns"
BASE = "https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome"

FILES_MIN = [
    "body-annotations-male-cns-v1.0-minconf-0.5.feather",
    "body-neurotransmitters-male-cns-v1.0.feather",
]
FILES_FULL = FILES_MIN + [
    "connectome-weights-male-cns-v1.0-minconf-0.5.feather",
]

VISION_TYPE_PREFIXES = (
    "R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8",
    "L1", "L2", "L3", "L4", "L5",
    "T4", "T5", "Tm", "Mi1", "Mi4", "Mi9", "C2", "C3", "T1",
    "LC", "LPLC", "LPTC", "DNp01",
)


def _download(name: str) -> Path:
    dest = OUT / name
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  skip exists {name} ({dest.stat().st_size} bytes)")
        return dest
    url = f"{BASE}/{name}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".partial")
    print(f"  GET {url}")
    urllib.request.urlretrieve(url, tmp)
    tmp.replace(dest)
    print(f"  wrote {dest} ({dest.stat().st_size} bytes)")
    return dest


def extract_vision_types(ann_path: Path) -> Path:
    try:
        import pandas as pd
    except ImportError:
        print("pandas/pyarrow not installed yet; skip type index", file=sys.stderr)
        return OUT / "vision_types.json"

    df = pd.read_feather(ann_path)
    type_col = None
    for c in df.columns:
        if str(c).lower() in {"type", "celltype", "cell_type", "instance"}:
            type_col = c
            break
    id_col = None
    for c in df.columns:
        if str(c).lower() in {"bodyid", "body_id", "body"}:
            id_col = c
            break
    out = OUT / "vision_types.json"
    if type_col is None:
        out.write_text(json.dumps({"warning": "no type column", "columns": list(df.columns)}, indent=2))
        return out

    types = df[type_col].astype(str)
    mask = types.apply(lambda t: any(t.startswith(p) or t == p for p in VISION_TYPE_PREFIXES))
    sub = df.loc[mask]
    payload = {
        "source": str(ann_path.name),
        "n_neurons_total": int(len(df)),
        "n_vision_like": int(len(sub)),
        "type_column": type_col,
        "id_column": id_col,
        "counts_by_type": sub[type_col].astype(str).value_counts().head(80).to_dict(),
        "note": "These are MaleCNS cell-type labels used as the vision-loop prior. Full weights are optional.",
    }
    out.write_text(json.dumps(payload, indent=2))
    print(f"  vision-like cells: {payload['n_vision_like']} / {payload['n_neurons_total']}")
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Download MaleCNS v1.0")
    p.add_argument("--full-connectome", action="store_true", help="also fetch 1.1GB weight table")
    args, _ = p.parse_known_args(argv)
    OUT.mkdir(parents=True, exist_ok=True)
    names = FILES_FULL if args.full_connectome else FILES_MIN
    print("MaleCNS files:", ", ".join(names))
    paths = [_download(n) for n in names]
    extract_vision_types(paths[0])
    meta = {
        "release": "male-cns:v1.0",
        "license": "CC-BY-4.0",
        "credit": "FlyEM/HHMI Janelia, University of Cambridge, MRC LMB, Google Research",
        "page": "https://male-cns.janelia.org/download/",
        "files": [n for n in names],
    }
    (OUT / "SOURCE.json").write_text(json.dumps(meta, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
