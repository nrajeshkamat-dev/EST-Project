"""Step 2: genus proportions, 500-yr bins, site filtering, modern reference set.

Usage:
  python 02_preprocess.py                       -> binned.csv, modern.csv, sites.csv
  python 02_preprocess.py --pinus-downweight    -> binned_pinus.csv   (sensitivity)
  python 02_preprocess.py --jitter 3            -> binned_jitter_3.csv (age-uncertainty draw, seed 3)
"""
import argparse
import numpy as np
import pandas as pd
import config as C
from lib import ensure_dirs, to_genus, COLS


def counts_table(df, jitter_seed=None, pinus_w=1.0):
    df = df.dropna(subset=["count", "lat", "lon"]).copy()
    # keep only sites inside the study region (guards against stray or sign-flipped coordinates)
    w, s_, e, n = C.BBOX
    inside = df.lon.between(w, e) & df.lat.between(s_, n)
    if (~inside).any():
        print(f"  dropped {df.loc[~inside, 'dataset_id'].nunique()} datasets outside the study region")
    df = df[inside].copy()
    df["genus"] = df["taxon"].map(to_genus)
    df["count"] = df["count"].astype(float)
    if pinus_w != 1.0:
        df.loc[df.genus == "Pinus", "count"] *= pinus_w
    if "age_bp" in df and jitter_seed is not None:
        rng = np.random.default_rng(jitter_seed)
        key = df[["dataset_id", "depth", "age_bp"]].drop_duplicates()
        key["age_j"] = key.age_bp + rng.normal(0, C.AGE_SD_FRAC * key.age_bp.clip(lower=100))
        df = df.merge(key, on=["dataset_id", "depth", "age_bp"])
        df["age_bp"] = df["age_j"]
    g = (df.groupby(["dataset_id", "lat", "lon", "depth", "age_bp", "genus"], dropna=False)["count"].sum()
           .unstack("genus", fill_value=0).reset_index())
    for c in COLS:
        if c not in g:
            g[c] = 0.0
    g["total"] = g[COLS].sum(axis=1)
    return g[g.total >= C.MIN_GRAINS]


def bin_fossil(g):
    g = g[(g.age_bp >= C.AGE_MIN) & (g.age_bp < C.AGE_MAX)].copy()
    g["bin_age"] = (g.age_bp // C.BIN_WIDTH) * C.BIN_WIDTH + C.BIN_WIDTH / 2
    b = g.groupby(["dataset_id", "lat", "lon", "bin_age"])[COLS].sum().reset_index()
    tot = b[COLS].sum(axis=1)
    b[COLS] = b[COLS].div(tot, axis=0)
    b["n_grains"] = tot
    keep = []
    for sid, s in b.groupby("dataset_id"):
        ages = np.sort(s.bin_age.values)
        gaps = np.diff(ages) / C.BIN_WIDTH
        if len(ages) >= C.MIN_BINS and (len(gaps) == 0 or gaps.max() - 1 <= C.MAX_GAP_BINS):
            keep.append(sid)
    return b[b.dataset_id.isin(keep)].rename(columns={"dataset_id": "site_id"})


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pinus-downweight", action="store_true")
    ap.add_argument("--jitter", type=int, default=None)
    a = ap.parse_args()
    ensure_dirs()
    fossil = pd.read_csv(C.PROC / "fossil_long.csv")
    w = C.PINUS_DOWNWEIGHT if a.pinus_downweight else 1.0
    b = bin_fossil(counts_table(fossil, a.jitter, w))
    name = "binned.csv"
    if a.pinus_downweight: name = "binned_pinus.csv"
    if a.jitter is not None: name = f"binned_jitter_{a.jitter}.csv"
    b.to_csv(C.PROC / name, index=False)
    print(f"{name}: {b.site_id.nunique()} sites, {len(b)} binned samples")
    if name == "binned.csv":
        b.groupby("site_id")[["lat", "lon"]].first().reset_index().to_csv(C.PROC / "sites.csv", index=False)
        m = counts_table(pd.read_csv(C.PROC / "modern_long.csv"))
        mt = m[COLS].sum(axis=1)
        m[COLS] = m[COLS].div(mt, axis=0)
        m[["dataset_id", "lat", "lon"] + COLS].rename(columns={"dataset_id": "site_id"}).to_csv(C.PROC / "modern.csv", index=False)
        print(f"modern.csv: {len(m)} modern samples")
