"""Step 1b: fetch & match Li et al. (2022) LegacyAge 1.0 chronologies + N=50 ensemble.

Streams Table-S5 from PANGAEA (DOI 10.1594/PANGAEA.933132), caches only study-region
dataset_ids to data/raw/legacyage_matched.csv, interpolates Age_Median & age_sd by depth,
falls back cleanly to Neotoma ages + depth-scaled uncertainty for unmatched cores.
"""
import argparse
import importlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import requests
import config as C
from lib import ensure_dirs

CACHE_PATH = C.RAW / "legacyage_matched.csv"


def fetch_legacyage_subset(target_ids, force=False):
    if CACHE_PATH.exists() and not force:
        df = pd.read_csv(CACHE_PATH)
        return df, None
    target_set = set(int(x) for x in target_ids)
    tmp_full = C.RAW / "Table-S5_legacyage_1_0_chronology.tsv"
    warn = None
    try:
        if not tmp_full.exists() or force:
            print(f"downloading LegacyAge 1.0 Table-S5 from {C.LEGACYAGE_URL} ...")
            with requests.get(C.LEGACYAGE_URL, stream=True, timeout=180) as r:
                r.raise_for_status()
                part = tmp_full.with_suffix(".part")
                with open(part, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
                part.replace(tmp_full)
        chunks = []
        for ch in pd.read_csv(tmp_full, sep="\t", chunksize=200_000):
            sub = ch[ch["Dataset_ID"].isin(target_set)]
            if len(sub):
                chunks.append(sub)
        df = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()
        df.to_csv(CACHE_PATH, index=False)
        # Clean up large full TSV once filtered subset is cached
        if tmp_full.exists():
            tmp_full.unlink()
        print(f"cached {len(df)} LegacyAge rows across {df['Dataset_ID'].nunique() if len(df) else 0} datasets")
        return df, None
    except Exception as e:
        warn = f"LegacyAge download failed ({e}); using Neotoma chronologies with depth-scaled fallback uncertainty."
        return pd.DataFrame(), warn


def apply_legacyage(fossil_df, la_df):
    df = fossil_df.copy()
    w, s_, e, n = C.BBOX
    inside_ids = sorted(df.loc[df.lon.between(w, e) & df.lat.between(s_, n), "dataset_id"].dropna().astype(int).unique())
    df["age_bp_orig"] = df["age_bp"]
    df["age_sd"] = np.maximum(100.0, C.AGE_SD_FRAC * df["age_bp"].fillna(1000.0).abs())
    df["chronology_source"] = "neotoma_fallback"

    audit_rows = []
    la_groups = {int(k): g.sort_values("Depth (cm)") for k, g in la_df.groupby("Dataset_ID")} if len(la_df) else {}
    for dsid in inside_ids:
        mask = df.dataset_id == dsid
        depths = df.loc[mask, "depth"].astype(float).values
        orig_ages = df.loc[mask, "age_bp_orig"].astype(float).values
        if dsid not in la_groups or np.all(np.isnan(depths)):
            reason = "not_in_legacyage_1.0" if dsid not in la_groups else "missing_sample_depths"
            audit_rows.append({"dataset_id": dsid, "matched": False, "reason": reason, "n_rows": int(mask.sum()), "median_abs_shift_yr": np.nan, "mean_sd_yr": float(np.nanmean(df.loc[mask, "age_sd"]))})
            continue

        lg = la_groups[dsid]
        ld = lg["Depth (cm)"].astype(float).values
        # Guard against m vs cm mismatch if core depths are recorded in meters
        d_scale = 100.0 if (np.nanmax(depths) <= 30.0 and np.nanmax(ld) > 100.0 and np.nanmax(depths) * 100.0 <= np.nanmax(ld) * 1.5) else 1.0
        q_depths = depths * d_scale

        # Check depth overlap sanity
        if np.nanmin(q_depths) > np.nanmax(ld) * 1.5 or np.nanmax(q_depths) < np.nanmin(ld) * 0.5:
            audit_rows.append({"dataset_id": dsid, "matched": False, "reason": "depth_range_mismatch", "n_rows": int(mask.sum()), "median_abs_shift_yr": np.nan, "mean_sd_yr": float(np.nanmean(df.loc[mask, "age_sd"]))})
            continue

        med_age = np.interp(q_depths, ld, lg["Age_Median"].astype(float).values)
        sd_vec = (lg["Age_Maximum"].astype(float).values - lg["Age_Minimum"].astype(float).values) / 3.92
        sd_interp = np.maximum(50.0, np.interp(q_depths, ld, sd_vec))

        valid_d = ~np.isnan(q_depths)
        new_ages = np.where(valid_d, med_age, orig_ages)
        new_sds = np.where(valid_d, sd_interp, df.loc[mask, "age_sd"].values)
        df.loc[mask, "age_bp"] = new_ages
        df.loc[mask, "age_sd"] = new_sds
        df.loc[mask, "chronology_source"] = "legacyage_1.0"

        shift = np.nanmedian(np.abs(new_ages - orig_ages))
        audit_rows.append({
            "dataset_id": dsid, "matched": True, "reason": "ok",
            "n_rows": int(mask.sum()), "depth_scale": d_scale,
            "median_abs_shift_yr": round(float(shift), 1) if not np.isnan(shift) else 0.0,
            "mean_sd_yr": round(float(np.nanmean(new_sds)), 1),
        })

    audit_df = pd.DataFrame(audit_rows)
    return df, audit_df


def run_age_ensemble(n_ensemble=C.LEGACYAGE_ENSEMBLE_N, seed=42):
    """Run N core-coherent LegacyAge uncertainty realizations and write ensemble_summary_legacyage.json."""
    pp = importlib.import_module("02_preprocess")
    met = importlib.import_module("03_metrics")
    la_df = pd.read_csv(C.PROC / "fossil_long_legacyage.csv")
    csite = pd.read_csv(C.PROC / "climate_sites.csv")
    audit_p = C.STAGE_LOGS / "legacyage_match_audit.csv"
    audit_df = pd.read_csv(audit_p) if audit_p.exists() else pd.DataFrame()

    # Precompute sample grain table once (TRSH-only + RPP), retaining sample age_sd
    fg_base, _ = pp.counts_table(la_df, trsh_only=True, use_rpp=True)
    sd_map = la_df.groupby(["dataset_id", "depth", "age_bp"])["age_sd"].first()
    fg_base["age_sd"] = [
        float(sd_map.get((r.dataset_id, r.depth, r.age_bp), max(100.0, C.AGE_SD_FRAC * abs(r.age_bp))))
        for r in fg_base.itertuples()
    ]
    sites_p = C.PROC / "sites_legacyage.csv"
    retained_ids = set(pd.read_csv(sites_p).site_id.astype(int)) if sites_p.exists() else set(fg_base.dataset_id.astype(int).unique())
    matched_ids = set(audit_df.loc[audit_df.matched == True, "dataset_id"].astype(int)) if len(audit_df) else set()
    matched_retained = len(retained_ids & matched_ids)

    rng = np.random.default_rng(seed)
    uniq_cores = fg_base.dataset_id.unique()
    core_vals = fg_base.dataset_id.values
    base_ages = fg_base.age_bp.values
    sd_vals = fg_base.age_sd.values

    cross_meds, genus_meds = [], {}
    for _ in range(int(n_ensemble)):
        z_map = dict(zip(uniq_cores, rng.normal(0.0, 1.0, size=len(uniq_cores))))
        z_vec = np.fromiter((z_map[c] for c in core_vals), dtype=float, count=len(core_vals))
        fg_draw = fg_base.copy()
        fg_draw["age_bp"] = np.clip(base_ages + z_vec * sd_vals, C.AGE_MIN, C.AGE_MAX - 1.0)
        b_draw, _ = pp.bin_fossil(fg_draw, bin_width=C.BIN_WIDTH)
        L_draw = met.compute_lags(b_draw, csite, bw=C.BIN_WIDTH, lag_mode="diff", ebisuzaki_n=0, seed=0)
        S_draw, _ = met.lag_summary(L_draw, n_boot=0)
        if len(S_draw):
            cross_meds.append(float(S_draw.median_lag_yr.median()))
            for r in S_draw.itertuples():
                genus_meds.setdefault(r.genus, []).append(float(r.median_lag_yr))

    summary = {
        "n_ensemble": int(n_ensemble),
        "matched_sites": int(matched_retained),
        "total_sites": int(len(retained_ids)),
        "matched_inside_bbox_datasets": int(len(matched_ids)),
        "total_inside_bbox_datasets": int(len(audit_df)),
        "ensemble_median_lag_yr": round(float(np.median(cross_meds)), 1) if cross_meds else None,
        "ensemble_lag_iqr_yr": f"{np.percentile(cross_meds, 25):.0f}–{np.percentile(cross_meds, 75):.0f} yr" if cross_meds else None,
        "per_genus_lag_iqr_yr": {
            g: {
                "median": round(float(np.median(vs)), 1),
                "q25": round(float(np.percentile(vs, 25)), 1),
                "q75": round(float(np.percentile(vs, 75)), 1),
                "n_draws": len(vs),
            }
            for g, vs in sorted(genus_meds.items())
        },
    }
    (C.OUT / "ensemble_summary_legacyage.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"[ensemble] N={n_ensemble} median={summary['ensemble_median_lag_yr']} yr (IQR {summary['ensemble_lag_iqr_yr']})")
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--run-ensemble", type=int, default=0)
    a = ap.parse_args()
    ensure_dirs()
    fossil = pd.read_csv(C.PROC / "fossil_long.csv")
    w, s_, e, n = C.BBOX
    inside_ids = sorted(fossil.loc[fossil.lon.between(w, e) & fossil.lat.between(s_, n), "dataset_id"].dropna().astype(int).unique())
    la_df, warn = fetch_legacyage_subset(inside_ids, force=a.force)
    out_df, audit_df = apply_legacyage(fossil, la_df)
    out_df.to_csv(C.PROC / "fossil_long_legacyage.csv", index=False)
    audit_df.to_csv(C.STAGE_LOGS / "legacyage_match_audit.csv", index=False)
    n_matched = int(audit_df.matched.sum()) if len(audit_df) else 0
    print(f"LegacyAge matched {n_matched}/{len(audit_df)} inside-bbox datasets; wrote fossil_long_legacyage.csv")
    if warn:
        print("WARNING:", warn)
    if a.run_ensemble > 0:
        run_age_ensemble(n_ensemble=a.run_ensemble)
