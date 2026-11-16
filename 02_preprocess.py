"""Step 2: genus proportions, binning, site filtering, and modern reference set.

Supports original flags (--pinus-downweight, --jitter) plus Phase 1 modes:
  --trsh-only       filter to group == 'TRSH' (removes UPHE agricultural herbs)
  --rpp             apply empirical RPP weights (count / RPP) after raw grain QC
  --bin-width N     override bin width (e.g. 250 for Stage 06 sensitivity)
  --fossil-input P  use alternate fossil_long CSV (e.g. fossil_long_legacyage.csv)
  --out-tag TAG     save binned_<TAG>.csv, modern_<TAG>.csv, sites_<TAG>.csv
"""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
import config as C
from lib import ensure_dirs, to_genus, COLS


def counts_table(df, jitter_seed=None, pinus_w=1.0, trsh_only=False, use_rpp=False, rng_ages=None):
    audit = {"raw_datasets": int(df.dataset_id.nunique()), "raw_rows": int(len(df)), "dropped_outside_bbox": 0}
    if trsh_only and "group" in df.columns:
        df = df[df.group == "TRSH"].copy()
        audit["after_trsh_datasets"] = int(df.dataset_id.nunique())
        audit["after_trsh_rows"] = int(len(df))
    df = df.dropna(subset=["count", "lat", "lon"]).copy()
    w, s_, e, n = C.BBOX
    inside = df.lon.between(w, e) & df.lat.between(s_, n)
    if (~inside).any():
        audit["dropped_outside_bbox"] = int(df.loc[~inside, "dataset_id"].nunique())
        print(f"  dropped {audit['dropped_outside_bbox']} datasets outside the study region")
    df = df[inside].copy()
    audit["inside_bbox_datasets"] = int(df.dataset_id.nunique())

    df["genus"] = df["taxon"].map(to_genus)
    df["count"] = df["count"].astype(float)
    df["raw_count"] = df["count"]

    if pinus_w != 1.0:
        df.loc[df.genus == "Pinus", "count"] *= pinus_w
    if use_rpp:
        weights = df["genus"].map(C.RPP_WEIGHTS).fillna(1.0)
        df["count"] = df["count"] / weights

    if "age_bp" in df:
        if rng_ages is not None:
            df["age_bp"] = rng_ages
        elif jitter_seed is not None:
            rng = np.random.default_rng(jitter_seed)
            key = df[["dataset_id", "depth", "age_bp"]].drop_duplicates()
            sd = key["age_sd"] if "age_sd" in df.columns else C.AGE_SD_FRAC * key.age_bp.clip(lower=100)
            key["age_j"] = key.age_bp + rng.normal(0, sd)
            df = df.merge(key[["dataset_id", "depth", "age_bp", "age_j"]], on=["dataset_id", "depth", "age_bp"])
            df["age_bp"] = df["age_j"]

    idx_cols = ["dataset_id", "lat", "lon", "depth", "age_bp"]
    g = (df.groupby(idx_cols + ["genus"], dropna=False)["count"].sum()
           .unstack("genus", fill_value=0).reset_index())
    raw_tot = df.groupby(idx_cols, dropna=False)["raw_count"].sum().reset_index(name="raw_total")
    g = g.merge(raw_tot, on=idx_cols, how="left")
    for c in COLS:
        if c not in g:
            g[c] = 0.0
    g["total"] = g[COLS].sum(axis=1)
    # Quality gate uses real counted grains so RPP division does not falsely reject Pinus-rich samples
    kept = g[g.raw_total >= C.MIN_GRAINS].copy()
    audit["samples_before_min_grains"] = int(len(g))
    audit["samples_after_min_grains"] = int(len(kept))
    return kept, audit


def bin_fossil(g, bin_width=None):
    bw = int(bin_width or C.BIN_WIDTH)
    min_bins = max(C.MIN_BINS, int(round(C.MIN_BINS * 500 / bw)))
    max_gap = max(C.MAX_GAP_BINS, int(round(C.MAX_GAP_BINS * 500 / bw)))
    g = g[(g.age_bp >= C.AGE_MIN) & (g.age_bp < C.AGE_MAX)].copy()
    g["bin_age"] = (g.age_bp // bw) * bw + bw / 2.0
    b = g.groupby(["dataset_id", "lat", "lon", "bin_age"])[COLS].sum().reset_index()
    tot = b[COLS].sum(axis=1)
    b[COLS] = b[COLS].div(tot, axis=0)
    b["n_grains"] = tot
    keep, dropped_reasons = [], []
    for sid, s in b.groupby("dataset_id"):
        ages = np.sort(s.bin_age.values)
        gaps = np.diff(ages) / bw
        if len(ages) < min_bins:
            dropped_reasons.append(f"site {int(sid)}: {len(ages)} bins < min {min_bins}")
        elif len(gaps) > 0 and gaps.max() - 1 > max_gap:
            dropped_reasons.append(f"site {int(sid)}: max gap {int(gaps.max() - 1)} > {max_gap} bins")
        else:
            keep.append(sid)
    out = b[b.dataset_id.isin(keep)].rename(columns={"dataset_id": "site_id"})
    return out, dropped_reasons


def run_preprocess(
    fossil_input=None,
    pinus_downweight=False,
    jitter=None,
    trsh_only=False,
    use_rpp=False,
    bin_width=None,
    out_tag=None,
    audit_json=None,
):
    ensure_dirs()
    bw = int(bin_width or C.BIN_WIDTH)
    f_path = Path(fossil_input) if fossil_input else (C.PROC / "fossil_long.csv")
    fossil = pd.read_csv(f_path)
    modern_long = pd.read_csv(C.PROC / "modern_long.csv")

    w = C.PINUS_DOWNWEIGHT if pinus_downweight else 1.0
    fg, f_audit = counts_table(fossil, jitter, w, trsh_only=trsh_only, use_rpp=use_rpp)
    b, dropped_sites = bin_fossil(fg, bin_width=bw)

    if out_tag:
        b_name, s_name, m_name = f"binned_{out_tag}.csv", f"sites_{out_tag}.csv", f"modern_{out_tag}.csv"
    elif pinus_downweight:
        b_name, s_name, m_name = "binned_pinus.csv", None, None
    elif jitter is not None:
        b_name, s_name, m_name = f"binned_jitter_{jitter}.csv", None, None
    else:
        b_name, s_name, m_name = "binned.csv", "sites.csv", "modern.csv"

    b.to_csv(C.PROC / b_name, index=False)
    print(f"{b_name}: {b.site_id.nunique()} sites, {len(b)} binned samples (dropped {len(dropped_sites)} sites)")

    m_audit = {}
    if s_name:
        b.groupby("site_id")[["lat", "lon"]].first().reset_index().to_csv(C.PROC / s_name, index=False)
    if m_name:
        m, m_audit = counts_table(modern_long, trsh_only=trsh_only, use_rpp=use_rpp)
        mt = m[COLS].sum(axis=1)
        m[COLS] = m[COLS].div(mt, axis=0)
        m[["dataset_id", "lat", "lon"] + COLS].rename(columns={"dataset_id": "site_id"}).to_csv(C.PROC / m_name, index=False)
        print(f"{m_name}: {len(m)} modern samples")

    summary = {
        "fossil_input": str(f_path),
        "bin_width": bw,
        "trsh_only": trsh_only,
        "use_rpp": use_rpp,
        "binned_file": b_name,
        "modern_file": m_name,
        "sites_retained": int(b.site_id.nunique()),
        "binned_rows": int(len(b)),
        "fossil_audit": f_audit,
        "modern_audit": m_audit,
        "dropped_sites": dropped_sites,
    }
    if audit_json:
        Path(audit_json).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pinus-downweight", action="store_true")
    ap.add_argument("--jitter", type=int, default=None)
    ap.add_argument("--trsh-only", action="store_true")
    ap.add_argument("--rpp", action="store_true")
    ap.add_argument("--bin-width", type=int, default=C.BIN_WIDTH)
    ap.add_argument("--fossil-input", default=None)
    ap.add_argument("--out-tag", default=None)
    ap.add_argument("--audit-json", default=None)
    a = ap.parse_args()
    run_preprocess(
        fossil_input=a.fossil_input,
        pinus_downweight=a.pinus_downweight,
        jitter=a.jitter,
        trsh_only=a.trsh_only,
        use_rpp=a.rpp,
        bin_width=a.bin_width,
        out_tag=a.out_tag,
        audit_json=a.audit_json,
    )
